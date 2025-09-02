import io
import time
import sys
from PIL import Image
from telebot.types import Message
from md2tgmd import escape
from telebot import TeleBot
from config import conf, generation_config, draw_generation_config, lang_settings, DEFAULT_SYSTEM_PROMPT, safety_settings
from google import genai
from google.genai import types
from google.api_core import exceptions as google_api_exceptions
from google.genai.types import Tool, UrlContext, GoogleSearch

import re
import asyncio
import logging

logger = logging.getLogger(__name__)

# Concurrency lock for operations on shared API key resources
api_key_lock = asyncio.Lock()

# API KEY管理
api_keys = []
current_api_key_index = 0

# Cooldown tracking for rate-limited keys
api_key_cooldowns = {}

gemini_draw_dict = {}
gemini_chat_dict = {}
gemini_pro_chat_dict = {}
switchable_chat_sessions = {}
user_language_dict = {}
user_system_prompt_dict = {}
user_model_index_dict = {}

# List of keys for chat models available for switching
CHAT_MODELS = ['model_1', 'model_2', 'paid_model_for_check']

model_1                 =       conf["model_1"]
model_2                 =       conf["model_2"]
model_3                 =       conf["model_3"]
default_language        =       conf["default_language"]
error_info              =       conf["error_info"]
before_generate_info    =       conf["before_generate_info"]
download_pic_notify     =       conf["download_pic_notify"]

client = None

async def initialize_client():
    global client
    if api_keys:
        try:
            client = genai.Client(api_key=api_keys[current_api_key_index])
            logger.info("Gemini client initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing client: {e}")
    else:
        logger.warning("No API keys found. Client remains uninitialized.")

async def check_individual_keys(keys_to_check, paid_model_name, standard_model_name):
    """
    Checks a given list of API keys and returns them classified.
    This is the core logic, accepting keys as a parameter.
    """
    semaphore = asyncio.Semaphore(conf.get("api_check_concurrency", 10))

    async def check_key(index, key):
        # This function remains the same as before
        if key in api_key_cooldowns and time.time() < api_key_cooldowns[key]:
            return "rate_limited", (index, key)
        if key in api_key_cooldowns:
            del api_key_cooldowns[key]
        async with semaphore:
            temp_client = genai.Client(api_key=key)
            def get_cooldown_from_exc(e):
                if hasattr(e, "response") and hasattr(e.response, "headers"):
                    retry_after = e.response.headers.get("retry-after")
                    if retry_after and retry_after.isdigit():
                        return int(retry_after)
                if hasattr(e, "__cause__") and hasattr(e.__cause__, "trailing_metadata"):
                    for k, v in e.__cause__.trailing_metadata():
                        if k == 'retry-after' and v.isdigit():
                            return int(v)
                if "429" in str(e):
                    match = re.search(r"retry-after: (\d+)", str(e), re.IGNORECASE)
                    if match:
                        return int(match.group(1))
                return 60
            try:
                if paid_model_name:
                    await temp_client.aio.models.generate_content(model=paid_model_name, contents="hi")
                logger.info(f"Key {index} ({key[:5]}...) is PAID.")
                return "paid", (index, key)
            except Exception:
                pass
            try:
                await temp_client.aio.models.generate_content(model=standard_model_name, contents="hi")
                logger.info(f"Key {index} ({key[:5]}...) is STANDARD.")
                return "standard", (index, key)
            except (google_api_exceptions.ResourceExhausted, google_api_exceptions.TooManyRequests) as e:
                cooldown = get_cooldown_from_exc(e)
                api_key_cooldowns[key] = time.time() + cooldown
                logger.warning(f"Key {index} ({key[:5]}...) is RATE LIMITED. Cooldown set for {cooldown}s.")
                return "rate_limited", (index, key)
            except Exception as e:
                if "429" in str(e):
                    cooldown = get_cooldown_from_exc(e)
                    api_key_cooldowns[key] = time.time() + cooldown
                    logger.warning(f"Key {index} ({key[:5]}...) is RATE LIMITED (429). Cooldown set for {cooldown}s.")
                    return "rate_limited", (index, key)
                logger.error(f"Key {index} ({key[:5]}...) is INVALID. Reason: {type(e).__name__}")
                return "invalid", (index, key)

    tasks = [check_key(i, key) for i, key in enumerate(keys_to_check)]
    results = await asyncio.gather(*tasks)

    paid_keys = [item for status, item in results if status == 'paid']
    standard_keys = [item for status, item in results if status == 'standard']
    rate_limited_keys = [item for status, item in results if status == 'rate_limited']
    invalid_keys = [item for status, item in results if status == 'invalid']

    return paid_keys, standard_keys, rate_limited_keys, invalid_keys

async def unified_api_key_check(paid_model_name, standard_model_name):
    """
    Checks all internally stored API keys. This function now calls the generic checker.
    """
    keys_to_check = list(api_keys)
    return await check_individual_keys(keys_to_check, paid_model_name, standard_model_name)

def get_current_api_key():
    if not api_keys:
        return None
    return api_keys[current_api_key_index]

def switch_to_next_api_key():
    global current_api_key_index, client
    if len(api_keys) <= 1:
        return False
    
    original_index = current_api_key_index
    
    for _ in range(len(api_keys)):
        current_api_key_index = (current_api_key_index + 1) % len(api_keys)
        
        # If we have looped back to the start, it means all keys might be in cooldown
        if current_api_key_index == original_index:
            return False

        key_to_check = api_keys[current_api_key_index]
        
        # Check if the next key is in cooldown
        if key_to_check in api_key_cooldowns and time.time() < api_key_cooldowns[key_to_check]:
            logger.warning(f"Skipping key #{current_api_key_index} as it is in cooldown.")
            continue

        try:
            client = genai.Client(api_key=key_to_check)
            logger.info(f"Successfully switched to API key #{current_api_key_index}")
            return True
        except Exception as e:
            logger.error(f"Error switching to next API key #{current_api_key_index}: {e}")
            continue # Try the next one
            
    return False

def get_current_chat_model_key(user_id):
    """Gets the key for the user's current chat model (e.g., 'model_1')."""
    user_id_str = str(user_id)
    model_index = user_model_index_dict.get(user_id_str, 0)
    # Ensure index is valid, fall back to 0 if out of bounds
    if not 0 <= model_index < len(CHAT_MODELS):
        model_index = 0
    return CHAT_MODELS[model_index]

def get_current_chat_model(user_id):
    """Gets the actual model name for the user's current chat model (e.g., 'gemini-pro')."""
    model_key = get_current_chat_model_key(user_id)
    return conf.get(model_key, conf['model_1']) # Fallback to model_1

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
                logger.error(f"Error initializing client with new API key: {e}")
                api_keys.pop()
                return False
        return True
    return False

def remove_api_key(key):
    global current_api_key_index, client
    if key in api_keys:
        # --- FIX START: Preserve active key and re-sync index ---
        active_key_value = api_keys[current_api_key_index] if api_keys else None
        was_current_key = (key == active_key_value)
        
        api_keys.remove(key)
        
        if not api_keys:
            current_api_key_index = 0
            client = None
            logger.info("All API keys removed. Client is now None.")
            return True
        
        if was_current_key:
            # If the active key was removed, reset to the first key
            current_api_key_index = 0
        else:
            # If a non-active key was removed, find the new index of the original active key
            try:
                current_api_key_index = api_keys.index(active_key_value)
            except ValueError:
                # This case happens if the active key was also invalid and removed by another process.
                # Safely reset to the first key.
                current_api_key_index = 0
        
        # Always re-initialize the client to ensure state consistency
        try:
            client = genai.Client(api_key=api_keys[current_api_key_index])
            logger.info(f"Key removed. New active key is at index {current_api_key_index}.")
        except Exception as e:
            logger.error(f"Failed to re-initialize client after removing key: {e}")
            client = None
        # --- FIX END ---
        
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
            logger.error(f"Error switching to API key at index {index}: {e}")
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
    if user_id_str in switchable_chat_sessions: del switchable_chat_sessions[user_id_str]
    confirmation_msg = f"{get_user_text(message.from_user.id, 'system_prompt_set')}\n{prompt}"
    await bot.reply_to(message, confirmation_msg)

async def delete_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    if user_id_str in user_system_prompt_dict: del user_system_prompt_dict[user_id_str]
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    if user_id_str in switchable_chat_sessions: del switchable_chat_sessions[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_deleted'))

async def reset_system_prompt(bot: TeleBot, message: Message):
    user_id_str = str(message.from_user.id)
    user_system_prompt_dict[user_id_str] = DEFAULT_SYSTEM_PROMPT
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    if user_id_str in switchable_chat_sessions: del switchable_chat_sessions[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, 'system_prompt_reset'))

async def show_system_prompt(bot: TeleBot, message: Message):
    user_id = message.from_user.id
    prompt = get_system_prompt(user_id)
    await bot.reply_to(message, f"{get_user_text(user_id, 'system_prompt_current')}\n{prompt}")

async def safe_edit_message(bot, text, chat_id, message_id, parse_mode=None):
    try:
        kwargs = {"text": text, "chat_id": chat_id, "message_id": message_id}
        if parse_mode:
            kwargs["parse_mode"] = parse_mode
        await bot.edit_message_text(**kwargs)
    except Exception as e:
        # We only want to log errors that are not "message is not modified"
        if "message is not modified" not in str(e).lower():
            # Re-raise the exception to be handled by the calling function
            raise e


async def gemini_stream(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        # Lock before checking for client to prevent race conditions
        async with api_key_lock:
            if client is None:
                await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty") )
                return
            
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")

        chat_dict = gemini_chat_dict if model_type == model_1 else gemini_pro_chat_dict
        user_id_str = str(message.from_user.id)

        # Initialize chat outside the retry loop but after the client check
        if user_id_str not in chat_dict:
            system_prompt = get_system_prompt(message.from_user.id)
            try:
                # Create a copy of the base config and add the system prompt
                config_copy = generation_config.copy()
                config_copy['system_instruction'] = system_prompt
                
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(**config_copy)
                )
                chat_dict[user_id_str] = chat
            except Exception as e:
                logger.error(f"Failed to set system prompt: {e}")
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(**generation_config)
                )
                chat_dict[user_id_str] = chat
        else:
            chat = chat_dict[user_id_str]
            
        lang = get_user_lang(message.from_user.id)
        if lang == "zh" and "用中文回复" not in m: m += "，请用中文回复"

        retry_count = 0
        # Use a copy of api_keys length for stable loop bound
        max_retries = len(api_keys)
        while retry_count < max_retries:
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
                                if "parse" in str(e).lower() or "entity" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                else:
                                    logger.warning(f"Error updating message during stream: {e}")
                            last_update = time.time()

                # Final message processing
                try:
                    final_text = escape(full_response)
                    if not final_text.strip():
                        final_text = get_user_text(message.from_user.id, 'error_info') + "\n" + "Model returned an empty response."
                    await safe_edit_message(bot, final_text, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse" in str(e).lower() or "entity" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    else:
                        logger.error(f"Final message update error: {e}", exc_info=True)
                break # Success, exit loop
                
            except Exception as e:
                error_str = repr(e)
                logger.error(f"An error occurred during gemini_stream: {error_str}", exc_info=True)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\nError: {error_str}\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id)

                async with api_key_lock:
                    switched = switch_to_next_api_key()
                
                if switched:
                    retry_count += 1
                    # Re-create chat object with the new client
                    system_prompt = get_system_prompt(message.from_user.id)
                    config_copy = generation_config.copy()
                    config_copy['system_instruction'] = types.Part.from_text(system_prompt)
                    chat = client.aio.chats.create(
                        model=model_type,
                        config=types.GenerateContentConfig(**config_copy)
                    )
                    chat_dict[user_id_str] = chat
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break # No more keys to try
            
    except Exception as e:
        logger.error("An unhandled error occurred in gemini_stream", exc_info=True)
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)

async def gemini_edit(bot: TeleBot, message: Message, m: str, photo_file: bytes):
    async with api_key_lock:
        if client is None:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty") )
            return
    
    sent_message = await bot.reply_to(message, download_pic_notify)
    
    max_retries = len(api_keys)
    retry_count = 0
    while retry_count < max_retries:
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
            if text:
                try:
                    await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                except Exception as e:
                    if "parse" in str(e).lower() or "entity" in str(e).lower():
                        await bot.send_message(message.chat.id, text)
                    else:
                        raise e
            
            await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
            break

        except Exception as e:
            error_str = repr(e)
            logger.error(f"An error occurred during gemini_edit: {error_str}", exc_info=True)
            error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\nError: {error_str}\nSwitching key..."
            await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id)

            async with api_key_lock:
                switched = switch_to_next_api_key()

            if switched:
                retry_count += 1
            else:
                await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                break
        
async def gemini_image_understand(bot: TeleBot, message: Message, photo_file: bytes, prompt: str = ""):
    sent_message = None
    try:
        async with api_key_lock:
            if client is None:
                await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty") )
                return
            
        sent_message = await bot.reply_to(message, download_pic_notify)
        lang = get_user_lang(message.from_user.id)
        
        if lang == "zh" and "用中文回复" not in prompt: prompt += "，请用中文回复"
        if not prompt: prompt = "描述这张图片" if lang == "zh" else "Describe this image"

        max_retries = len(api_keys)
        retry_count = 0
        while retry_count < max_retries:
            try:
                user_id = str(message.from_user.id)
                current_model_name = get_current_chat_model(user_id)
                # Determine the correct chat dictionary based on the model name
                # This part is tricky as we now have more than two models.
                # For simplicity, we can use a single chat dictionary or create a more dynamic system.
                # Let's assume gemini_chat_dict for pro models and gemini_pro_chat_dict for flash, and default to pro.
                if "flash" in current_model_name:
                    active_chat_dict = gemini_pro_chat_dict
                else:
                    active_chat_dict = gemini_chat_dict
                
                image = Image.open(io.BytesIO(photo_file))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG")
                image_bytes = buffer.getvalue()
                
                system_prompt = get_system_prompt(user_id)
                
                image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
                text_part = types.Part.from_text(text=prompt)
                
                if user_id not in active_chat_dict:
                    # Create a copy of the base config and add the system prompt
                    config_copy = generation_config.copy()
                    config_copy['system_instruction'] = system_prompt
                    
                    chat = client.aio.chats.create(
                        model=current_model_name,
                        config=types.GenerateContentConfig(**config_copy)
                    )
                    active_chat_dict[user_id] = chat
                else:
                    chat = active_chat_dict[user_id]
                
                response_stream = await chat.send_message_stream([text_part, image_part])
                
                full_response = ""
                last_update = time.time()
                update_interval = conf["streaming_update_interval"]
                
                # --- FIX: Use the correct variable 'response_stream' ---
                async for chunk in response_stream:
                    if hasattr(chunk, 'text') and chunk.text:
                        full_response += chunk.text
                        if time.time() - last_update >= update_interval:
                            try:
                                await safe_edit_message(bot, escape(full_response), sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                            except Exception as e:
                                if "parse" in str(e).lower() or "entity" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                else:
                                    logger.warning(f"Image understanding stream error: {e}")
                            last_update = time.time()
                
                # Final message processing
                try:
                    final_text = escape(full_response)
                    if not final_text.strip():
                        final_text = get_user_text(message.from_user.id, 'error_info') + "\n" + "Model returned an empty response."
                    await safe_edit_message(bot, final_text, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse" in str(e).lower() or "entity" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    else:
                        logger.error(f"Final image understanding message update error: {e}", exc_info=True)
                break
            
            except Exception as e:
                error_str = repr(e)
                logger.error(f"An error occurred during gemini_image_understand: {error_str}", exc_info=True)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\nError: {error_str}\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id)

                async with api_key_lock:
                    switched = switch_to_next_api_key()

                if switched:
                    retry_count += 1
                    if user_id in active_chat_dict: del active_chat_dict[user_id]
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break
                
    except Exception as e:
        logger.error("An unhandled error occurred in gemini_image_understand", exc_info=True)
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)

async def gemini_draw(bot:TeleBot, message:Message, m:str):
    sent_message = None
    try:
        async with api_key_lock:
            if client is None:
                await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty") )
                return
            
        sent_message = await bot.reply_to(message, get_user_text(message.from_user.id, "drawing_message") )
            
        max_retries = len(api_keys)
        retry_count = 0
        while retry_count < max_retries:
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
                if text:
                    try:
                        await bot.send_message(message.chat.id, escape(text), parse_mode="MarkdownV2")
                    except Exception as e:
                        if "parse" in str(e).lower() or "entity" in str(e).lower():
                            await bot.send_message(message.chat.id, text)
                        else:
                            raise e
                
                try: await bot.delete_message(chat_id=sent_message.chat.id, message_id=sent_message.message_id)
                except Exception: pass
                break
                
            except Exception as e:
                error_str = repr(e)
                logger.error(f"An error occurred during gemini_draw: {error_str}", exc_info=True)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\nError: {error_str}\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id)

                async with api_key_lock:
                    switched = switch_to_next_api_key()

                if switched:
                    retry_count += 1
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break
            
    except Exception as e:
        logger.error("An unhandled error occurred in gemini_draw", exc_info=True)
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)

async def switch_model_and_inherit_history(user_id):
    """
    Switches the user's chat model to the next one in the list and
    re-creates the chat session with the existing history.
    """
    global client
    if not client:
        raise ValueError("Gemini client is not initialized.")

    user_id_str = str(user_id)
    
    # Get current model index and calculate the next one
    current_index = user_model_index_dict.get(user_id_str, 0)
    next_index = (current_index + 1) % len(CHAT_MODELS)
    user_model_index_dict[user_id_str] = next_index
    
    new_model_key = CHAT_MODELS[next_index]
    new_model_name = conf.get(new_model_key, conf['model_1'])

    # Get history from the old chat, if it exists
    history = []
    if user_id_str in switchable_chat_sessions:
        try:
            # Accessing history might be complex depending on the library's async implementation
            # Assuming a synchronous accessor for simplicity or that it's readily available
            old_chat = switchable_chat_sessions[user_id_str]
            if hasattr(old_chat, 'history'):
                history = old_chat.history
        except Exception as e:
            logger.error(f"Could not retrieve history for user {user_id_str}: {e}")

    # Create a new chat with the new model and the old history
    system_prompt = get_system_prompt(user_id)
    try:
        # Create a copy of the base config and add the system prompt
        config_copy = generation_config.copy()
        config_copy['system_instruction'] = system_prompt
        
        new_chat = client.aio.chats.create(
            model=new_model_name,
            history=history,
            config=types.GenerateContentConfig(**config_copy)
        )
        switchable_chat_sessions[user_id_str] = new_chat
        logger.info(f"User {user_id_str} switched to model {new_model_name} inheriting {len(history)} messages.")
    except Exception as e:
        logger.error(f"Failed to create new chat for user {user_id_str} with model {new_model_name}: {e}")
        # Optionally, revert the model switch if creation fails
        user_model_index_dict[user_id_str] = current_index
        raise  # Re-raise the exception to be handled by the caller

    return new_model_name

async def gemini_stream_switchable(bot:TeleBot, message:Message, m:str, model_type:str):
    sent_message = None
    try:
        # Lock before checking for client to prevent race conditions
        async with api_key_lock:
            if client is None:
                await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty") )
                return
            
        sent_message = await bot.reply_to(message, "🤖 Generating answers...")

        chat_dict = switchable_chat_sessions
        user_id_str = str(message.from_user.id)

        # Initialize chat outside the retry loop but after the client check
        if user_id_str not in chat_dict:
            system_prompt = get_system_prompt(message.from_user.id)
            try:
                # Create a copy of the base config and add the system prompt
                config_copy = generation_config.copy()
                config_copy['system_instruction'] = system_prompt
                
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(**config_copy)
                )
                chat_dict[user_id_str] = chat
            except Exception as e:
                logger.error(f"Failed to set system prompt: {e}")
                chat = client.aio.chats.create(
                    model=model_type,
                    config=types.GenerateContentConfig(**generation_config)
                )
                chat_dict[user_id_str] = chat
        else:
            chat = chat_dict[user_id_str]
            
        lang = get_user_lang(message.from_user.id)
        if lang == "zh" and "用中文回复" not in m: m += "，请用中文回复"

        retry_count = 0
        # Use a copy of api_keys length for stable loop bound
        max_retries = len(api_keys)
        while retry_count < max_retries:
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
                                if "parse" in str(e).lower() or "entity" in str(e).lower():
                                    await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                                else:
                                    logger.warning(f"Error updating message during stream: {e}")
                            last_update = time.time()

                # Final message processing
                try:
                    final_text = escape(full_response)
                    if not final_text.strip():
                        final_text = get_user_text(message.from_user.id, 'error_info') + "\n" + "Model returned an empty response."
                    await safe_edit_message(bot, final_text, sent_message.chat.id, sent_message.message_id, "MarkdownV2")
                except Exception as e:
                    if "parse" in str(e).lower() or "entity" in str(e).lower():
                        await safe_edit_message(bot, full_response, sent_message.chat.id, sent_message.message_id)
                    else:
                        logger.error(f"Final message update error: {e}", exc_info=True)
                break # Success, exit loop
                
            except Exception as e:
                error_str = repr(e)
                logger.error(f"An error occurred during gemini_stream: {error_str}", exc_info=True)
                error_msg = f"{get_user_text(message.from_user.id, 'error_info')}\nError: {error_str}\nSwitching key..."
                await safe_edit_message(bot, error_msg, sent_message.chat.id, sent_message.message_id)

                async with api_key_lock:
                    switched = switch_to_next_api_key()
                
                if switched:
                    retry_count += 1
                    # Re-create chat object with the new client
                    system_prompt = get_system_prompt(message.from_user.id)
                    config_copy = generation_config.copy()
                    config_copy['system_instruction'] = types.Part.from_text(system_prompt)
                    chat = client.aio.chats.create(
                        model=model_type,
                        config=types.GenerateContentConfig(**config_copy)
                    )
                    chat_dict[user_id_str] = chat
                else:
                    await safe_edit_message(bot, get_user_text(message.from_user.id, 'all_api_quota_exhausted'), sent_message.chat.id, sent_message.message_id)
                    break # No more keys to try
            
    except Exception as e:
        logger.error("An unhandled error occurred in gemini_stream", exc_info=True)
        error_details = f"{error_info}\nError details: {str(e)}"
        if sent_message:
            await safe_edit_message(bot, error_details, sent_message.chat.id, sent_message.message_id)
        else:
            await bot.reply_to(message, error_details)
