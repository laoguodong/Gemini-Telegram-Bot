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
from google.genai.types import Tool, UrlContext, GoogleSearch

# API KEY管理
api_keys = []  # 存储多个API key
current_api_key_index = 0  # 当前使用的API key索引

# 初始化API key列表
if len(sys.argv) > 2:
    # 支持多种格式的密钥输入：逗号分隔、换行分隔或两者的组合
    input_keys = sys.argv[2]
    # 替换中文逗号为英文逗号
    input_keys = input_keys.replace('，', ',')
    # 先按逗号分割
    comma_split_keys = input_keys.split(',')
    
    for item in comma_split_keys:
        # 对于每个逗号分割的项，再按换行符分割
        line_split_keys = item.splitlines()
        for key in line_split_keys:
            clean_key = key.strip()
            if clean_key:
                api_keys.append(clean_key)

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

# search_tool = {'google_search': {}}
tools = [
    Tool(google_search=GoogleSearch()),
    Tool(url_context=UrlContext()),
]

# 初始化客户端
client = None
if api_keys:
    try:
        client = genai.Client(api_key=api_keys[current_api_key_index])
    except Exception as e:
        print(f"Error initializing client: {e}")

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
    try:
        client = genai.Client(api_key=api_keys[current_api_key_index])
        print(f"成功切换到API密钥 #{current_api_key_index}")
        return True
    except Exception as e:
        print(f"Error switching to next API key: {e}")
        # 如果切换失败，不要直接返回False，而是递归调用自己尝试下一个密钥
        return switch_to_next_api_key()

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

# 添加一个安全的消息编辑函数
async def safe_edit_message(bot, text, chat_id, message_id, parse_mode=None):
    """安全地编辑消息，处理'message is not modified'错误"""
    try:
        kwargs = {
            "text": text,
            "chat_id": chat_id,
            "message_id": message_id
        }
        if parse_mode:
            kwargs["parse_mode"] = parse_mode
        
        await bot.edit_message_text(**kwargs)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"Error editing message: {e}")

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
                        tools=tools
                    )
                )
                chat_dict[str(message.from_user.id)] = chat
            except Exception as e:
                print(f"Failed to set system prompt in chat creation: {e}")
                # 如果设置系统提示词失败，尝试创建没有系统提示词的聊天
                chat = client.aio.chats.create(
                    model=model_type, 
                    tools=tools
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
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e:
                                if "parse markdown" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                elif "message is not modified" not in str(e).lower():
                                    print(f"Error updating message: {e}")
                            last_update = current_time

                try:
                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse markdown" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    else:
                        print(f"Final message update error: {e}")
                
                break # 成功，跳出循环
                
            except Exception as e:
                error_str = str(e)
                error_msg_to_user = (
                    f"{get_user_text(message.from_user.id, 'error_info')}\n"
                    f"当前API密钥发生错误: `{escape(error_str)}`\n"
                    f"正在尝试切换到下一个密钥..."
                )
                try:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id)

                if switch_to_next_api_key():
                    retry_count += 1
                    try:
                        system_prompt = get_system_prompt(message.from_user.id)
                        chat = client.aio.chats.create(
                            model=model_type,
                            config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools)
                        )
                        chat_dict[str(message.from_user.id)] = chat
                        continue
                    except Exception as chat_error:
                        print(f"Error recreating chat with new API key: {chat_error}")
                        await safe_edit_message(bot, f"{error_info}\n切换密钥后创建会话失败: {chat_error}", sent_message.chat.id, sent_message.message_id)
                        break
                else:
                    await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                    break
            
    except Exception as e:
        if sent_message:
            await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
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
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG")
                image_bytes = buffer.getvalue()
            except Exception as img_error:
                await safe_edit_message(bot, f"{error_info}\n图像处理错误: {str(img_error)}", sent_message.chat.id, sent_message.message_id)
                return
            
            # 创建内容
            text_part = types.Part.from_text(text=m)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            
            # 发送请求
            response = await client.aio.models.generate_content(
                model=model_3,
                contents=[text_part, image_part],
                config=types.GenerateContentConfig(**draw_generation_config)
            )
            
            # 检查响应
            if not hasattr(response, 'candidates') or not response.candidates:
                await safe_edit_message(bot, f"{error_info}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
                return
            
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
            
            if img:
                with io.BytesIO(img) as bio:
                    await bot.send_photo(message.chat.id, bio)
            
            if text:
                if len(text) > 4000:
                    await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                    await bot.send_message(message.chat.id, escape(text[4000:]), parse_mode="MarkdownV2")
                else:
                    await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
            
            await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
            break # 成功，跳出循环

        except Exception as e:
            error_str = str(e)
            error_msg_to_user = (
                f"{get_user_text(message.from_user.id, 'error_info')}\n"
                f"当前API密钥发生错误: `{escape(error_str)}`\n"
                f"正在尝试切换到下一个密钥..."
            )
            try:
                await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
            except Exception:
                await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id)

            if switch_to_next_api_key():
                retry_count += 1
                continue
            else:
                await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                break
        
async def gemini_image_understand(bot: TeleBot, message: Message, photo_file: bytes, prompt: str = ""):
    sent_message = None
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
                # 获取用户的对话历史字典和模型名称 (确保格式一致)
                user_id = str(message.from_user.id)
                is_model_1_default = default_model_dict.get(user_id, True)  # 默认使用 model_1
                active_chat_dict = gemini_chat_dict if is_model_1_default else gemini_pro_chat_dict
                current_model_name = model_1 if is_model_1_default else model_2
                
                # 调试日志
                print(f"用户 {user_id} 使用模型 {current_model_name}, " +
                     f"已有会话: {user_id in active_chat_dict}")
                
                # Load image from bytes
                image_obj = Image.open(io.BytesIO(photo_file))
                buffer = io.BytesIO()
                image_obj.save(buffer, format="JPEG")
                image_bytes = buffer.getvalue()

                # 系统提示词只应在创建新会话时使用
                system_prompt = get_system_prompt(message.from_user.id)
                
                # 准备多模态输入内容
                image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                text_part = types.Part.from_text(text=prompt)
                
                # 确保聊天会话管理与 gemini_stream 函数保持一致
                if user_id not in active_chat_dict:
                    print(f"为用户 {user_id} 创建新会话，模型：{current_model_name}")
                    try:
                        chat = client.aio.chats.create(
                            model=current_model_name,
                            config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools)
                        )
                        active_chat_dict[user_id] = chat
                    except Exception as e:
                        print(f"创建带系统提示词的会话失败: {e}")
                        chat = client.aio.chats.create(
                            model=current_model_name,
                            config=types.GenerateContentConfig(tools=tools)
                        )
                        active_chat_dict[user_id] = chat
                else:
                    print(f"用户 {user_id} 使用现有会话")
                    chat = active_chat_dict[user_id]
                
                # 使用聊天会话发送多模态内容
                parts = [text_part, image_part]
                response_stream = await chat.send_message_stream(parts)
                
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]
                
                async for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        current_time = time.time()
                    
                        if current_time - last_update >= update_interval:
                            try:
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e_stream:
                                if "parse markdown" in str(e_stream).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                elif "message is not modified" not in str(e_stream).lower():
                                    print(f"图片理解流更新错误: {e_stream}")
                            
                            last_update = current_time
                
                try:
                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception:
                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                
                break # 成功，跳出循环
            
            except Exception as e:
                error_str = str(e)
                error_msg_to_user = (
                    f"{get_user_text(message.from_user.id, 'error_info')}\n"
                    f"当前API密钥发生错误: `{escape(error_str)}`\n"
                    f"正在尝试切换到下一个密钥..."
                )
                try:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id)

                if switch_to_next_api_key():
                    retry_count += 1
                    # 清除可能已创建的无效会话
                    if user_id in active_chat_dict:
                        del active_chat_dict[user_id]
                    continue
                else:
                    await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                    break
                
    except Exception as e:
        if sent_message:
            await safe_edit_message(bot, f"{error_info}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
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
                # 使用新的API方式进行绘图
                response = await client.aio.models.generate_content(
                    model=model_3,
                    contents=m,
                    config=types.GenerateContentConfig(**draw_generation_config)
                )
                
                # 检查响应
                if not hasattr(response, 'candidates') or not response.candidates:
                    error_msg = get_user_text(message.from_user.id, "error_info")
                    await safe_edit_message(bot, f"{error_msg}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
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
                
                if img:
                    with io.BytesIO(img) as bio:
                        await bot.send_photo(message.chat.id, bio)
                
                if text:
                    if len(text) > 4000:
                        await bot.send_message(message.chat.id, escape(text[:4000]), parse_mode="MarkdownV2")
                        await bot.send_message(message.chat.id, escape(text[4000:]), parse_mode="MarkdownV2")
                    else:
                        await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                
                try:
                    await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                except Exception:
                    pass
                
                break # 成功，跳出循环
                
            except Exception as e:
                error_str = str(e)
                error_msg_to_user = (
                    f"{get_user_text(message.from_user.id, 'error_info')}\n"
                    f"当前API密钥发生错误: `{escape(error_str)}`\n"
                    f"正在尝试切换到下一个密钥..."
                )
                try:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception:
                    await safe_edit_message(bot, error_msg_to_user, sent_message.chat.id, sent_message.message_id)

                if switch_to_next_api_key():
                    retry_count += 1
                    continue
                else:
                    await safe_edit_message(bot, f"{error_info}\n{get_user_text(message.from_user.id, 'all_api_quota_exhausted')}", sent_message.chat.id, sent_message.message_id)
                    break
            
    except Exception as e:
        error_msg = get_user_text(message.from_user.id, "error_info")
        if sent_message:
            await safe_edit_message(bot, f"{error_msg}\nError details: {str(e)}", sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, f"{error_msg}\nError details: {str(e)}")
