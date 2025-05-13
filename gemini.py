import io
import time
import traceback
import sys
from PIL import Image
from telebot.types import Message
from md2tgmd import escape
from telebot import TeleBot
from config import conf, generation_config, draw_generation_config, lang_settings, DEFAULT_SYSTEM_PROMPT, safety_settings
from google import genai
from google.genai import types

# API KEY管理
api_keys = []  # 存储多个API key
current_api_key_index = 0  # 当前使用的API key索引

# 初始化API key列表
if len(sys.argv) > 2:
    initial_keys = sys.argv[2].split(',')
    for key in initial_keys:
        if key.strip():
            api_keys.append(key.strip())

gemini_draw_dict = {}
gemini_chat_dict = {}
gemini_pro_chat_dict = {}
default_model_dict = {}
user_language_dict = {}  # 新增：用户语言偏好字典
user_system_prompt_dict = {}  # 用户系统提示词字典

model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]
model_3                 =       conf["model_3"]
default_language        =       conf["default_language"]
error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]

search_tool = {'google_search': {}}

# 初始化客户端
client = None
if api_keys:
    client = genai.Client(api_key=api_keys[current_api_key_index])

# API KEY管理函数
def get_current_api_key():
    """获取当前使用的API key"""
    if not api_keys:
        return None
    return api_keys[current_api_key_index]

def switch_to_next_api_key():
    """切换到下一个可用的API key"""
    global current_api_key_index, client
    if len(api_keys) <= 1:
        return False  # 如果只有0或1个密钥，无法切换
    
    # 记录原始索引，用于检测是否已经尝试了所有key
    original_index = current_api_key_index
    
    # 尝试切换到下一个key
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    
    # 如果循环一圈回到原始索引，说明所有key都尝试过了
    if current_api_key_index == original_index:
        return False
    
    # 更新客户端
    client = genai.Client(api_key=api_keys[current_api_key_index])
    return True

def validate_api_key_format(key):
    """验证API密钥格式（简单检查）"""
    # 简单格式检查：密钥应该是有一定长度且只包含合法字符
    if not key or len(key) < 8:  # Google API密钥一般较长
        return False
        
    # 检查是否只包含字母、数字和常用特殊字符
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.")
    return all(c in valid_chars for c in key)

def add_api_key(key):
    """添加新的API key"""
    global client
    
    # 清理密钥中可能的空格和换行符
    key = key.strip()
    
    # 验证API密钥格式
    if not validate_api_key_format(key):
        return False
    
    if key not in api_keys:
        api_keys.append(key)
        # 如果这是第一个key，初始化客户端
        if len(api_keys) == 1:
            try:
                client = genai.Client(api_key=key)
                return True
            except Exception as e:
                print(f"Error initializing client with new API key: {e}")
                # 如果初始化失败，删除密钥
                api_keys.pop()
                return False
        return True
    return False

def remove_api_key(key):
    """删除指定的API key"""
    global current_api_key_index, client
    if key in api_keys:
        index = api_keys.index(key)
        api_keys.remove(key)
        
        # 如果删除后没有密钥了
        if not api_keys:
            current_api_key_index = 0
            client = None
            return True
        
        # 如果删除的是当前使用的key
        if index == current_api_key_index:
            # 如果删除的是最后一个密钥，指向新的最后一个密钥
            if index >= len(api_keys):
                current_api_key_index = len(api_keys) - 1
            # 否则保持相同索引（自动指向下一个密钥）
            client = genai.Client(api_key=api_keys[current_api_key_index])
        # 如果删除的key在当前使用的key之前，需要更新索引
        elif index < current_api_key_index:
            current_api_key_index -= 1
        
        return True
    return False

def list_api_keys():
    """列出所有API key（仅显示部分字符）"""
    masked_keys = []
    for i, key in enumerate(api_keys):
        # 根据键的长度进行脱敏处理
        if len(key) > 8:
            # 只显示前4位和后4位，中间用星号代替
            visible_part = len(key) // 4  # 显示约1/4的字符
            if visible_part < 2:
                visible_part = 2
            
            masked_key = key[:visible_part] + "*" * (len(key) - visible_part*2) + key[-visible_part:]
        else:
            # 对于短密钥，至少保留首尾字符，确保不同密钥可区分
            masked_key = key[0] + "*" * (max(len(key) - 2, 1)) + (key[-1] if len(key) > 1 else "")
        
        # 标记当前使用的key
        if i == current_api_key_index:
            masked_key = f"[当前] {masked_key}"
        masked_keys.append(masked_key)
    return masked_keys

def set_current_api_key(index):
    """设置当前使用的API key"""
    global current_api_key_index, client
    if 0 <= index < len(api_keys):
        try:
            # 保存原来的索引，以便在出错时恢复
            old_index = current_api_key_index
            # 先尝试初始化新客户端
            test_client = genai.Client(api_key=api_keys[index])
            # 如果成功，更新索引和客户端
            current_api_key_index = index
            client = test_client
            return True
        except Exception as e:
            print(f"Error switching to API key at index {index}: {e}")
            return False
    return False

# 根据用户ID获取语言设置
def get_user_lang(user_id):
    user_id_str = str(user_id)
    if user_id_str not in user_language_dict:
        user_language_dict[user_id_str] = default_language
    return user_language_dict[user_id_str]

# 获取用户对应语言的提示文案
def get_user_text(user_id, text_key):
    lang = get_user_lang(user_id)
    return lang_settings[lang].get(text_key, lang_settings[default_language].get(text_key, ""))

# 切换用户语言
async def switch_language(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    current_lang = get_user_lang(user_id_str)
    
    # 切换语言
    new_lang = "en" if current_lang == "zh" else "zh"
    user_language_dict[user_id_str] = new_lang
    
    # 发送语言切换确认消息
    await bot.reply_to(message, lang_settings[new_lang]["language_switched"])

# 获取当前语言状态
async def get_language(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    current_lang = get_user_lang(user_id_str)
    await bot.reply_to(message, lang_settings[current_lang]["language_current"])

# 获取用户系统提示词，如果没有设置则返回默认值
def get_system_prompt(user_id):
    user_id_str = str(user_id)
    return user_system_prompt_dict.get(user_id_str, DEFAULT_SYSTEM_PROMPT)

# 设置用户系统提示词
async def set_system_prompt(bot: TeleBot, message: Message, prompt: str):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = prompt
    
    # 清除该用户的聊天历史，以便新的系统提示词生效
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    
    confirmation_msg = f"{get_user_text(message.from_user.id, 'system_prompt_set')}\n{prompt}"
    await bot.reply_to(message, confirmation_msg)

# 删除用户系统提示词
async def delete_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    if user_id_str in user_system_prompt_dict:
        del user_system_prompt_dict[user_id_str]
    
    # 清除该用户的聊天历史，以便移除系统提示词生效
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_deleted'))

# 重置用户系统提示词为默认值
async def reset_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = DEFAULT_SYSTEM_PROMPT
    
    # 清除该用户的聊天历史，以便默认系统提示词生效
    if user_id_str in gemini_chat_dict:
        del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict:
        del gemini_pro_chat_dict[user_id_str]
    
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_reset'))

# 显示当前系统提示词
async def show_system_prompt(bot: TeleBot, message: Message):
    user_id = message.from_user.id
    prompt = get_system_prompt(user_id)
    await bot.reply_to(message, f"{get_user_text(user_id, 'system_prompt_current')}\n{prompt}")

async def gemini_stream(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        # 检查client是否已初始化
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")

        chat = None
        if model_type == model_1:
            chat_dict = gemini_chat_dict
        else:
            chat_dict = gemini_pro_chat_dict

        if str(message.from_user.id) not in chat_dict:
            # 获取用户系统提示词
            system_prompt = get_system_prompt(message.from_user.id)
            
            # 创建聊天会话，并使用系统提示词
            try:
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        tools=[search_tool]
                    )
                )
                chat_dict[str(message.from_user.id)] = chat
            except Exception as e:
                print(f"Failed to set system prompt in chat creation: {e}")
                # 如果设置系统提示词失败，尝试创建没有系统提示词的聊天
                chat = client.aio.chats.create(
                    model=model_type, 
                    config={'tools': [search_tool]}
                )
                chat_dict[str(message.from_user.id)] = chat
        else:
            chat = chat_dict[str(message.from_user.id)]
            
        # 根据用户语言添加中文回复请求
        lang = get_user_lang(message.from_user.id)
        if lang == "zh" and "用中文回复" not in m and "中文回答" not in m:
            m += "，请用中文回复"

        # 尝试发送消息，处理API密钥额度用尽的情况
        max_retry_attempts = len(api_keys)
        retry_count = 0
        
        while retry_count < max_retry_attempts:
            try:
                response = await chat.send_message_stream(m)
                
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]

                async for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        current_time = time.time()

                        if current_time - last_update >= update_interval:

                            try:
                                await bot.edit_message_text(
                                    escape(full_response),
                                    chat_id=sent_message.chat.id,
                                    message_id=sent_message.message_id,
                                    parse_mode="MarkdownV2"
                                    )
                            except Exception as e:
                                if "parse markdown" in str(e).lower():
                                    await bot.edit_message_text(
                                        full_response,
                                        chat_id=sent_message.chat.id,
                                        message_id=sent_message.message_id
                                        )
                                else:
                                    if "message is not modified" not in str(e).lower():
                                        print(f"Error updating message: {e}")
                            last_update = current_time

                try:
                    await bot.edit_message_text(
                        escape(full_response),
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id,
                        parse_mode="MarkdownV2"
                    )
                except Exception as e:
                    try:
                        if "parse markdown" in str(e).lower():
                            await bot.edit_message_text(
                                full_response,
                                chat_id=sent_message.chat.id,
                                message_id=sent_message.message_id
                            )
                    except Exception:
                        print(f"Final message update error: {e}")
                
                # 成功发送消息，跳出循环
                break
                
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额用尽错误
                if (hasattr(e, 'status_code') and e.status_code == 429) or \
                   ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    # 尝试切换到下一个API密钥
                    if switch_to_next_api_key():
                        # 提示用户正在切换API密钥
                        try:
                            await bot.edit_message_text(
                                get_user_text(message.from_user.id, "api_quota_exhausted"),
                                chat_id=sent_message.chat.id,
                                message_id=sent_message.message_id
                            )
                        except Exception:
                            pass
                        
                        # 重新创建聊天会话
                        try:
                            system_prompt = get_system_prompt(message.from_user.id)
                            chat = client.aio.chats.create(
                                model=model_type,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_prompt,
                                    tools=[search_tool]
                                )
                            )
                            chat_dict[str(message.from_user.id)] = chat
                            retry_count += 1
                            continue
                        except Exception as chat_error:
                            print(f"Error recreating chat with new API key: {chat_error}")
                    else:
                        # 所有API密钥都已尝试过
                        await bot.edit_message_text(
                            f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}",
                            chat_id=sent_message.chat.id,
                            message_id=sent_message.message_id
                        )
                        break
                else:
                    # 其他错误，直接显示给用户
                    await bot.edit_message_text(
                        f"{error_info}\nError details: {str(e)}",
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
                    break
                    
            retry_count += 1
            
    except Exception as e:
        if sent_message:
            await bot.edit_message_text(
                f"{error_info}\nError details: {str(e)}",
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id
            )
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {str(e)}")

async def gemini_edit(bot: TeleBot, message: Message, m: str, photo_file: bytes):
    # 检查client是否已初始化
    if client is None:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
        return
    
    # 先发送处理通知
    sent_message = await bot.reply_to(message, download_pic_notify)
    
    # 尝试处理图片，处理API密钥额度用尽的情况
    max_retry_attempts = len(api_keys)
    retry_count = 0
    
    while retry_count < max_retry_attempts:
        try:
            # 打开图像
            try:
                image = Image.open(io.BytesIO(photo_file))
            except Exception as img_error:
                await bot.edit_message_text(
                    f"{error_info}\n图像处理错误: {str(img_error)}",
                    chat_id=sent_message.chat.id,
                    message_id=sent_message.message_id
                )
                return
            
            # 获取用户语言
            lang = get_user_lang(message.from_user.id)
            
            # 如果是中文用户且提示中没有指定语言，确保添加"用中文回复"
            if lang == "zh" and "用中文回复" not in m and "中文回答" not in m and "in English" not in m.lower():
                m += "，请用中文回复"
            
            # 发送请求
            response = await client.aio.models.generate_content(
                model=model_3,
                contents=[m, image],
                config=types.GenerateContentConfig(**generation_config)
            )
            
            # 检查响应
            if not hasattr(response, 'candidates') or not response.candidates or not hasattr(response.candidates[0], 'content'):
                await bot.edit_message_text(
                    f"{error_info}\n无效的响应", 
                    chat_id=sent_message.chat.id,
                    message_id=sent_message.message_id
                )
                return
            
            # 处理响应
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text is not None:
                    await bot.send_message(message.chat.id, escape(part.text), parse_mode="MarkdownV2")
                elif hasattr(part, 'inline_data') and part.inline_data is not None:
                    photo = part.inline_data.data
                    await bot.send_photo(message.chat.id, photo)
            
            # 删除"正在加载"消息
            await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
            
            # 成功处理，跳出循环
            break
            
        except Exception as e:
            error_str = str(e)
            
            # 检查是否是配额用尽错误
            if (hasattr(e, 'status_code') and e.status_code == 429) or \
               ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                # 尝试切换到下一个API密钥
                if switch_to_next_api_key():
                    # 提示用户正在切换API密钥
                    try:
                        await bot.edit_message_text(
                            get_user_text(message.from_user.id, "api_quota_exhausted"),
                            chat_id=sent_message.chat.id,
                            message_id=sent_message.message_id
                        )
                    except Exception:
                        pass
                    
                    retry_count += 1
                    continue
                else:
                    # 所有API密钥都已尝试过
                    await bot.edit_message_text(
                        f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}",
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
                    break
            else:
                # 其他错误，直接显示给用户
                await bot.edit_message_text(
                    f"{error_info}\nError details: {str(e)}",
                    chat_id=sent_message.chat.id,
                    message_id=sent_message.message_id
                )
                break
        
        retry_count += 1

async def gemini_image_understand(bot: TeleBot, message: Message, photo_file: bytes, prompt: str = ""):
    sent_message = None
    current_model_name_for_error_msg = "configured model" # Placeholder for error messages
    try:
        # 检查client是否已初始化
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, download_pic_notify)

        # 获取用户语言
        lang = get_user_lang(message.from_user.id)
        
        # 如果是中文且没有明确要求英文回复，添加中文回复请求
        if lang == "zh" and "用中文回复" not in prompt and "中文回答" not in prompt and "in English" not in prompt.lower():
            prompt += "，请用中文回复"
            
        # 处理空提示词
        if not prompt:
            if lang == "zh":
                prompt = "描述这张图片，用中文回复"
            else:
                prompt = "Describe this image"

        # 尝试理解图片，处理API密钥额度用尽的情况
        max_retry_attempts = len(api_keys)
        retry_count = 0
        
        while retry_count < max_retry_attempts:
            try:
                # Load image from bytes
                image_obj = Image.open(io.BytesIO(photo_file))

                # 使用用户系统提示词
                system_prompt = get_system_prompt(message.from_user.id)
                
                # 创建模型
                current_model_name = model_1  # 默认使用model_1
                current_model_name_for_error_msg = current_model_name
                
                # 创建模型实例
                model = client.aio.genai_model(current_model_name)
                
                # 设置生成配置
                gen_config = generation_config.copy()
                
                # 创建聊天
                chat_session = await model.aio.start_chat(
                    system_instruction=system_prompt,
                    generation_config=gen_config, 
                    safety_settings=safety_settings
                )
                
                # 准备消息内容
                current_contents_for_chat = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/jpeg", "data": image_obj}}
                        ]
                    }
                ]
                
                # Use `content` (singular) keyword for send_message_stream with a list of parts.
                response_stream = await chat_session.send_message_stream(current_contents_for_chat)
                
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]
                
                async for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        current_time = time.time()
                    
                        if current_time - last_update >= update_interval:
                            try:
                                await bot.edit_message_text(
                                    escape(full_response),
                                    chat_id=sent_message.chat.id,
                                    message_id=sent_message.message_id,
                                    parse_mode="MarkdownV2"
                                )
                            except Exception as e_stream:
                                if "parse markdown" in str(e_stream).lower():
                                    await bot.edit_message_text(
                                        full_response,
                                        chat_id=sent_message.chat.id,
                                        message_id=sent_message.message_id
                                    )
                                elif "message is not modified" not in str(e_stream).lower():
                                    print(f"Streaming update error for image understanding: {e_stream}")
                            
                            last_update = current_time
                
                # Final update - try with markdown first, fall back to plain text
                try:
                    await bot.edit_message_text(
                        escape(full_response),
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id,
                        parse_mode="MarkdownV2"
                    )
                except Exception: # Fallback to sending raw text if markdown parsing fails on the final message
                    await bot.edit_message_text(
                        full_response,
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
                
                # 成功处理图片，跳出循环
                break
            
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额用尽错误
                if (hasattr(e, 'status_code') and e.status_code == 429) or \
                   ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    # 尝试切换到下一个API密钥
                    if switch_to_next_api_key():
                        # 提示用户正在切换API密钥
                        try:
                            await bot.edit_message_text(
                                get_user_text(message.from_user.id, "api_quota_exhausted"),
                                chat_id=sent_message.chat.id,
                                message_id=sent_message.message_id
                            )
                        except Exception:
                            pass
                        
                        retry_count += 1
                        continue
                    else:
                        # 所有API密钥都已尝试过
                        await bot.edit_message_text(
                            f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}",
                            chat_id=sent_message.chat.id,
                            message_id=sent_message.message_id
                        )
                        break
                else:
                    # General exception handler
                    error_detail_str = str(e)
                    # Check for the specific API error about text-only output
                    specific_api_error_check = ("This model only supports text output." in error_detail_str or \
                    "only supports text and HHFM function calling" in error_detail_str) and \
                    ("INVALID_ARGUMENT" in error_detail_str.upper() or isinstance(e, getattr(genai.errors, 'InvalidArgumentError', Exception)))
                    
                    error_message = f"{get_user_text(message.from_user.id, 'error_info')}\nError details: {error_detail_str}"
                    if specific_api_error_check: # If it is the text-only error, provide a more helpful message
                        if lang == "zh":
                            error_message = (
                            f"{get_user_text(message.from_user.id, 'error_info')}\n"
                            f"API错误: {error_detail_str}\n"
                            f"此错误表明模型 '{current_model_name_for_error_msg}'（如在config.py中配置的）"
                            f"只支持文本输出，但正在尝试生成多模态内容。\n"
                            f"请检查config.py中的模型配置。"
                            )
                        else:
                            error_message = (
                            f"{get_user_text(message.from_user.id, 'error_info')}\n"
                            f"API Error: {error_detail_str}\n"
                            f"This error suggests that the model '{current_model_name_for_error_msg}' (as configured in your config.py) "
                            f"only supports text output, but is being asked to generate multimodal content.\n"
                            f"Please check your model configuration in config.py."
                            )
                    
                    if sent_message: # If a message was already sent to the user, edit it with the error
                        await bot.edit_message_text(error_message, chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                    else: # Otherwise, reply to the original message with the error
                        await bot.reply_to(message, error_message)
                    break
            
            retry_count += 1
                
    except Exception as e:
        if sent_message:
            await bot.edit_message_text(
                f"{error_info}\nError details: {str(e)}",
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id
            )
        else:
            await bot.reply_to(message, f"{error_info}\nError details: {str(e)}")

async def gemini_draw(bot:TeleBot, message:Message, m:str):
    sent_message = None
    try:
        # 检查client是否已初始化
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        # 发送绘图中提示
        sent_message = await bot.reply_to(message, get_user_text(message.from_user.id, "drawing_message"))
            
        # 尝试绘图，处理API密钥额度用尽的情况
        max_retry_attempts = len(api_keys)
        retry_count = 0
        
        while retry_count < max_retry_attempts:
            try:
                # 获取用户语言
                lang = get_user_lang(message.from_user.id)
                
                # 如果是中文用户且提示中没有指定语言，确保添加"用中文回复"
                if lang == "zh" and "用中文回复" not in m and "中文回答" not in m and "in English" not in m.lower():
                    m += "，请用中文回复"
                
                # 使用绘图模型
                model = client.aio.genai_model(model_3)
                
                # 设置绘图配置
                gen_config = draw_generation_config.copy()
                
                # 发送绘图请求
                response = await model.aio.generate_content(m, generation_config=gen_config)
                
                # 检查响应
                if not hasattr(response, 'candidates') or not response.candidates:
                    error_msg = get_user_text(message.from_user.id, "error_info")
                    await bot.edit_message_text(
                        f"{error_msg}\nNo candidates generated",
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
                    break
                
                # 获取文本和图片
                text = ""
                img = None
                candidate = response.candidates[0]
                
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text += part.text
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img = part.inline_data.data
                
                # 先发送图片(如果有)
                if img:
                    with io.BytesIO(img) as bio:
                        await bot.send_photo(message.chat.id, bio)
                
                # 然后发送文本(如果有)
                if text:
                    if len(text) > 4000:
                        await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                        await bot.send_message(message.chat.id, escape(text[4000:]), parse_mode="MarkdownV2")
                    else:
                        await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                
                # 删除"绘图中"消息
                try:
                    await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                except Exception:
                    pass
                
                # 成功生成图片，跳出循环
                break
                
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额用尽错误
                if (hasattr(e, 'status_code') and e.status_code == 429) or \
                   ("429 RESOURCE_EXHAUSTED" in error_str and "You exceeded your current quota" in error_str):
                    # 尝试切换到下一个API密钥
                    if switch_to_next_api_key():
                        # 提示用户正在切换API密钥
                        try:
                            await bot.edit_message_text(
                                get_user_text(message.from_user.id, "api_quota_exhausted"),
                                chat_id=sent_message.chat.id,
                                message_id=sent_message.message_id
                            )
                        except Exception:
                            pass
                            
                        retry_count += 1
                        continue
                    else:
                        # 所有API密钥都已尝试过
                        error_msg = get_user_text(message.from_user.id, "error_info")
                        await bot.edit_message_text(
                            f"{error_msg}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}",
                            chat_id=sent_message.chat.id,
                            message_id=sent_message.message_id
                        )
                        break
                else:
                    # 其他错误，直接显示给用户
                    error_msg = get_user_text(message.from_user.id, "error_info")
                    await bot.edit_message_text(
                        f"{error_msg}\nError details: {str(e)}",
                        chat_id=sent_message.chat.id,
                        message_id=sent_message.message_id
                    )
                    break
            
            retry_count += 1
            
    except Exception as e:
        error_msg = get_user_text(message.from_user.id, "error_info")
        if sent_message:
            await bot.edit_message_text(
                f"{error_msg}\nError details: {str(e)}",
                chat_id=sent_message.chat.id,
                message_id=sent_message.message_id
            )
        else:
            await bot.reply_to(message, f"{error_msg}\nError details: {str(e)}")
