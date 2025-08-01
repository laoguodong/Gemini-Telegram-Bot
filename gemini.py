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

import asyncio
import logging

# --- Logging Setup ---
# (Logging is disabled but can be re-enabled by changing the handler)
# handler = logging.FileHandler('key_check.log', mode='w')
handler = logging.NullHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
# --- End Logging Setup ---

# API KEY管理
api_keys = []
current_api_key_index = 0

if len(sys.argv) > 2:
    input_keys = sys.argv[2]
    input_keys = input_keys.replace('，', ',')
    comma_split_keys = input_keys.split(',')
    for item in comma_split_keys:
        line_split_keys = item.splitlines()
        for key in line_split_keys:
            clean_key = key.strip()
            if clean_key:
                api_keys.append(clean_key)

gemini_draw_dict = {}
gemini_chat_dict = {}
gemini_pro_chat_dict = {}
default_model_dict = {}
user_language_dict = {}
user_system_prompt_dict = {}

model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]
model_3                 =       conf["model_3"]
default_language        =       conf["default_language"]
error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]

tools = [
    Tool(google_search=GoogleSearch()),
    Tool(url_context=UrlContext()),
]

client = None
if api_keys:
    try:
        client = genai.Client(api_key=api_keys[current_api_key_index])
    except Exception as e:
        print(f"Error initializing client: {e}")

async def check_model_access(key, model_name, semaphore):
    """
    Checks if a key can access a model by making a minimal generation request.
    """
    async with semaphore:
        try:
            temp_client = genai.Client(api_key=key)
            await temp_client.aio.models.generate_content(
                model=model_name,
                contents="hi"
            )
            logging.info(f"SUCCESS: Key starting with {key[:5]}... accessed model {model_name}.")
            return True
        except Exception as e:
            logging.error(f"FAILURE: Key starting with {key[:5]}... failed model {model_name}. Reason: {type(e).__name__} - {e}")
            return False

async def unified_api_key_check(paid_model_name, standard_model_name):
    """
    Checks all API keys and returns them classified with their original indices.
    """
    semaphore = asyncio.Semaphore(conf.get("api_check_concurrency", 10))

    async def check_paid_task(index, key):
        can_access = await check_model_access(key, paid_model_name, semaphore)
        return index, key, can_access

    paid_check_tasks = [check_paid_task(i, key) for i, key in enumerate(api_keys)]
    paid_check_results = await asyncio.gather(*paid_check_tasks)

    paid_keys = [(i, key) for i, key, access in paid_check_results if access]
    keys_for_standard_check = [(i, key) for i, key, access in paid_check_results if not access]

    standard_keys = []
    invalid_keys = []
    if keys_for_standard_check:
        async def check_standard_task(index, key):
            can_access = await check_model_access(key, standard_model_name, semaphore)
            return index, key, can_access

        standard_check_tasks = [check_standard_task(i, key) for i, key in keys_for_standard_check]
        standard_check_results = await asyncio.gather(*standard_check_tasks)

        standard_keys = [(i, key) for i, key, access in standard_check_results if access]
        invalid_keys = [(i, key) for i, key, access in standard_check_results if not access]

    return paid_keys, standard_keys, invalid_keys

# The rest of the file remains the same...
def get_current_api_key():
    if not api_keys:
        return None
    return api_keys[current_api_key_index]

def switch_to_next_api_key():
    global current_api_key_index, client
    if len(api_keys) <= 1:
        return False
    
    original_index = current_api_key_index
    current_api_key_index = (current_api_key_index + 1) % len(api_keys)
    
    if current_api_key_index == original_index:
        return False
    
    try:
        client = genai.Client(api_key=api_keys[current_api_key_index])
        print(f"成功切换到API密钥 #{current_api_key_index}")
        return True
    except Exception as e:
        print(f"Error switching to next API key: {e}")
        return switch_to_next_api_key()

def validate_api_key_format(key):
    if not key or len(key) < 8:
        return False
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.")
    return all(c in valid_chars for c in key)

def add_api_key(key):
    global client
    key = key.strip()
    if not validate_api_key_format(key):
        return False
    
    if key not in api_keys:
        api_keys.append(key)
        if len(api_keys) == 1:
            try:
                client = genai.Client(api_key=key)
                return True
            except Exception as e:
                print(f"Error initializing client with new API key: {e}")
                api_keys.pop()
                return False
        return True
    return False

def remove_api_key(key):
    global current_api_key_index, client
    if key in api_keys:
        index = api_keys.index(key)
        api_keys.remove(key)
        
        if not api_keys:
            current_api_key_index = 0
            client = None
            return True
        
        if index == current_api_key_index:
            if index >= len(api_keys):
                current_api_key_index = len(api_keys) - 1
            client = genai.Client(api_key=api_keys[current_api_key_index])
        elif index < current_api_key_index:
            current_api_key_index -= 1
        
        return True
    return False

def list_api_keys():
    full_keys = []
    for i, key in enumerate(api_keys):
        marked_key = key
        if i == current_api_key_index:
            marked_key = f"[当前] {key}"
        full_keys.append(marked_key)
    return full_keys

def remove_all_api_keys():
    global api_keys, current_api_key_index, client
    api_keys.clear()
    current_api_key_index = 0
    client = None
    return True

def set_current_api_key(index):
    global current_api_key_index, client
    if 0 <= index < len(api_keys):
        try:
            test_client = genai.Client(api_key=api_keys[index])
            current_api_key_index = index
            client = test_client
            return True
        except Exception as e:
            print(f"Error switching to API key at index {index}: {e}")
            return False
    return False

def get_user_lang(user_id):
    user_id_str = str(user_id)
    return user_language_dict.get(user_id_str, default_language)

def get_user_text(user_id, text_key):
    lang = get_user_lang(user_id)
    return lang_settings[lang].get(text_key, lang_settings[default_language].get(text_key, ""))

async def switch_language(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    current_lang = get_user_lang(user_id_str)
    new_lang = "en" if current_lang == "zh" else "zh"
    user_language_dict[user_id_str] = new_lang
    await bot.reply_to(message, lang_settings[new_lang]["language_switched"])

async def get_language(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    current_lang = get_user_lang(user_id_str)
    await bot.reply_to(message, lang_settings[current_lang]["language_current"])

def get_system_prompt(user_id):
    user_id_str = str(user_id)
    return user_system_prompt_dict.get(user_id_str, DEFAULT_SYSTEM_PROMPT)

async def set_system_prompt(bot: TeleBot, message: Message, prompt: str):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = prompt
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    confirmation_msg = f"{get_user_text(message.from_user.id, 'system_prompt_set')}\n{prompt}"
    await bot.reply_to(message, confirmation_msg)

async def delete_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    if user_id_str in user_system_prompt_dict: del user_system_prompt_dict[user_id_str]
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_deleted'))

async def reset_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = DEFAULT_SYSTEM_PROMPT
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_reset'))

async def show_system_prompt(bot: TeleBot, message: Message):
    user_id = message.from_user.id
    prompt = get_system_prompt(user_id)
    await bot.reply_to(message, f"{get_user_text(user_id, 'system_prompt_current')}\n{prompt}")

async def safe_edit_message(bot, text, chat_id, message_id, parse_mode=None):
    try:
        kwargs = {"text": text, "chat_id": chat_id, "message_id": message_id}
        if parse_mode: kwargs["parse_mode"] = parse_mode
        await bot.edit_message_text(**kwargs)
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            print(f"Error editing message: {e}")

async def gemini_stream(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")

        chat_dict = gemini_chat_dict if model_type == model_1 else gemini_pro_chat_dict
        user_id_str = str(message.from_user.id)

        if user_id_str not in chat_dict:
            system_prompt = get_system_prompt(message.from_user.id)
            try:
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools)
                )
                chat_dict[user_id_str] = chat
            except Exception as e:
                print(f"Failed to set system prompt: {e}")
                chat = client.aio.chats.create(model=model_type, tools=tools)
                chat_dict[user_id_str] = chat
        else:
            chat = chat_dict[user_id_str]
            
        lang = get_user_lang(message.from_user.id)
        if lang == "zh" and "用中文回复" not in m: m += "，请用中文回复"

        retry_count = 0
        while retry_count < len(api_keys):
            try:
                response = await chat.send_message_stream(m)
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]

                async for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        if time.time() - last_update >= update_interval:
                            try:
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e:
                                if "parse markdown" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                elif "message is not modified" not in str(e).lower():
                                    print(f"Error updating message: {e}")
                            last_update = time.time()

                try:
                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse markdown" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    else:
                        print(f"Final message update error: {e}")
                break
                
            except Exception as e:
                error_str = str(e)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\n`{escape(error_str)}`\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id, "MarkdownV2")

                if switch_to_next_api_key():
                    retry_count += 1
                    system_prompt = get_system_prompt(message.from_user.id)
                    chat = client.aio.chats.create(
                        model=model_type,
                        config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools)
                    )
                    chat_dict[user_id_str] = chat
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break
            
    except Exception as e:
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)

async def gemini_edit(bot: TeleBot, message: Message, m: str, photo_file: bytes):
    if client is None:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
        return
    
    sent_message = await bot.reply_to(message, download_pic_notify)
    
    retry_count = 0
    while retry_count < len(api_keys):
        try:
            image = Image.open(io.BytesIO(photo_file))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_bytes = buffer.getvalue()
            
            text_part = types.Part.from_text(text=m)
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            
            response = await client.aio.models.generate_content(
                model=model_3,
                contents=[text_part, image_part],
                config=types.GenerateContentConfig(**draw_generation_config)
            )
            
            if not hasattr(response, 'candidates') or not response.candidates:
                await safe_edit_message(bot, f"{error_info}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
                return
            
            text, img = "", None
            for part in response.candidates[0].content.parts:
                if part.text: text += part.text
                if part.inline_data: img = part.inline_data.data
            
            if img: await bot.send_photo(message.chat.id, io.BytesIO(img))
            if text: await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
            
            await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
            break

        except Exception as e:
            error_str = str(e)
            error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\n`{escape(error_str)}`\nSwitching key..."
            await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id, "MarkdownV2")

            if switch_to_next_api_key():
                retry_count += 1
            else:
                await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                break
        
async def gemini_image_understand(bot: TeleBot, message: Message, photo_file: bytes, prompt: str = ""):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, download_pic_notify)
        lang = get_user_lang(message.from_user.id)
        
        if lang == "zh" and "用中文回复" not in prompt: prompt += "，请用中文回复"
        if not prompt: prompt = "描述这张图片" if lang == "zh" else "Describe this image"

        retry_count = 0
        while retry_count < len(api_keys):
            try:
                user_id = str(message.from_user.id)
                is_model_1_default = default_model_dict.get(user_id, True)
                active_chat_dict = gemini_chat_dict if is_model_1_default else gemini_pro_chat_dict
                current_model_name = model_1 if is_model_1_default else model_2
                
                image_bytes = Image.open(io.BytesIO(photo_file)).tobytes()
                system_prompt = get_system_prompt(user_id)
                
                image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                text_part = types.Part.from_text(text=prompt)
                
                if user_id not in active_chat_dict:
                    chat = client.aio.chats.create(
                        model=current_model_name,
                        config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools)
                    )
                    active_chat_dict[user_id] = chat
                else:
                    chat = active_chat_dict[user_id]
                
                response_stream = await chat.send_message_stream([text_part, image_part])
                
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]
                
                async for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        if time.time() - last_update >= update_interval:
                            try:
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e:
                                if "parse markdown" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                elif "message is not modified" not in str(e).lower():
                                    print(f"Image understanding stream error: {e}")
                            last_update = time.time()
                
                try:
                    await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception:
                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                break
            
            except Exception as e:
                error_str = str(e)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\n`{escape(error_str)}`\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id, "MarkdownV2")

                if switch_to_next_api_key():
                    retry_count += 1
                    if user_id in active_chat_dict: del active_chat_dict[user_id]
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break
                
    except Exception as e:
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)

async def gemini_draw(bot:TeleBot, message:Message, m:str):
    sent_message = None
    try:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
            return
            
        sent_message = await bot.reply_to(message, get_user_text(message.from_user.id, "drawing_message"))
            
        retry_count = 0
        while retry_count < len(api_keys):
            try:
                response = await client.aio.models.generate_content(
                    model=model_3,
                    contents=m,
                    config=types.GenerateContentConfig(**draw_generation_config)
                )
                
                if not hasattr(response, 'candidates') or not response.candidates:
                    await safe_edit_message(bot, f"{error_info}\nNo candidates generated", sent_message.chat.id, sent_message.message_id)
                    break
                
                text, img = "", None
                for part in response.candidates[0].content.parts:
                    if part.text: text += part.text
                    if part.inline_data: img = part.inline_data.data
                
                if img: await bot.send_photo(message.chat.id, io.BytesIO(img))
                if text: await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                
                try: await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                except Exception: pass
                break
                
            except Exception as e:
                error_str = str(e)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\n`{escape(error_str)}`\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id, "MarkdownV2")

                if switch_to_next_api_key():
                    retry_count += 1
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break
            
    except Exception as e:
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)