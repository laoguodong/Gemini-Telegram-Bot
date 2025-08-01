from telebot import TeleBot
from telebot.types import Message, BotCommand
from md2tgmd import escape
import traceback
import json
import os
from functools import wraps
import config
from config import conf, lang_settings, USER_DATA_FILE
import gemini
import re

# Directly import functions from the gemini module
from gemini import (
    get_user_text, get_user_lang, switch_language, get_language,
    set_system_prompt, delete_system_prompt, reset_system_prompt, show_system_prompt,
    add_api_key, remove_api_key, list_api_keys, set_current_api_key, get_current_api_key,
    remove_all_api_keys, unified_api_key_check
)

# --- Menu Definitions ---

admin_menu_zh = [
    BotCommand("start", "开始"),
    BotCommand("gemini", f"模型 {conf['model_2']}"),
    BotCommand("gemini_pro", f"模型 {conf['model_1']}"),
    BotCommand("draw", "绘图"),
    BotCommand("clear", "清除会话"),
    BotCommand("switch", "切换模型"),
    BotCommand("lang", "切换语言"),
    BotCommand("system", "⚙️ 设置系统提示词"),
    BotCommand("system_show", "👀 查看系统提示词"),
    BotCommand("system_clear", "🗑️ 删除系统提示词"),
    BotCommand("system_reset", "🔄 重置系统提示词"),
    BotCommand("adduser", "✅ 添加用户"),
    BotCommand("deluser", "❌ 删除用户"),
    BotCommand("listusers", "👥 列出用户"),
    BotCommand("api_add", "🔑 添加密钥"),
    BotCommand("api_remove", "🗑️ 删除密钥"),
    BotCommand("api_list", "📋 列出密钥"),
    BotCommand("api_switch", "🔄 切换密钥"),
    BotCommand("api_check", "检查密钥状态"),
]

user_menu_zh = [
    BotCommand("start", "开始"),
    BotCommand("gemini", f"模型 {conf['model_2']}"),
    BotCommand("gemini_pro", f"模型 {conf['model_1']}"),
    BotCommand("draw", "绘图"),
    BotCommand("clear", "清除会话"),
    BotCommand("switch", "切换模型"),
    BotCommand("lang", "切换语言"),
]

admin_menu_en = [
    BotCommand("start", "Start"),
    BotCommand("gemini", f"Model {conf['model_2']}"),
    BotCommand("gemini_pro", f"Model {conf['model_1']}"),
    BotCommand("draw", "Draw"),
    BotCommand("clear", "Clear Chat"),
    BotCommand("switch", "Switch Model"),
    BotCommand("lang", "Switch Language"),
    BotCommand("system", "⚙️ Set System Prompt"),
    BotCommand("system_show", "👀 Show System Prompt"),
    BotCommand("system_clear", "🗑️ Clear System Prompt"),
    BotCommand("system_reset", "🔄 Reset System Prompt"),
    BotCommand("adduser", "✅ Add User"),
    BotCommand("deluser", "❌ Delete User"),
    BotCommand("listusers", "👥 List Users"),
    BotCommand("api_add", "🔑 Add API Key"),
    BotCommand("api_remove", "🗑️ Remove API Key"),
    BotCommand("api_list", "📋 List API Keys"),
    BotCommand("api_switch", "🔄 Switch API Key"),
    BotCommand("api_check", "Check Key Status"),
]

user_menu_en = [
    BotCommand("start", "Start"),
    BotCommand("gemini", f"Model {conf['model_2']}"),
    BotCommand("gemini_pro", f"Model {conf['model_1']}"),
    BotCommand("draw", "Draw"),
    BotCommand("clear", "Clear Chat"),
    BotCommand("switch", "Switch Model"),
    BotCommand("lang", "Switch Language"),
]

# --- User and Admin Management ---

def load_authorized_users():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, TypeError):
            return set(config.ADMIN_UID)
    return set(config.ADMIN_UID)

def save_authorized_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(list(users), f, indent=4)

def is_admin(user_id):
    return user_id in config.ADMIN_UID

# --- Decorators for Permission Control ---

def authorized_user_only(func):
    @wraps(func)
    async def wrapped(message: Message, bot: TeleBot, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in load_authorized_users():
            await bot.reply_to(message, "🚫 You do not have permission to use this bot.")
            return
        return await func(message, bot, *args, **kwargs)
    return wrapped

def admin_only(func):
    @wraps(func)
    async def wrapped(message: Message, bot: TeleBot, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await bot.reply_to(message, "🚫 Only administrators can perform this action.")
            return
        return await func(message, bot, *args, **kwargs)
    return wrapped

# --- Bot Handlers ---

gemini_chat_dict = gemini.gemini_chat_dict
gemini_pro_chat_dict = gemini.gemini_pro_chat_dict
default_model_dict = gemini.default_model_dict
gemini_draw_dict = gemini.gemini_draw_dict

@authorized_user_only
async def start(message: Message, bot: TeleBot) -> None:
    await bot.reply_to(message, get_user_text(message.from_user.id, "welcome_message"))

@authorized_user_only
async def language_switch_handler(message: Message, bot: TeleBot) -> None:
    await switch_language(bot, message)
    user_id = message.from_user.id
    new_lang = get_user_lang(user_id)
    menu_to_set = user_menu_zh
    if is_admin(user_id):
        menu_to_set = admin_menu_zh if new_lang == 'zh' else admin_menu_en
    else:
        menu_to_set = user_menu_zh if new_lang == 'zh' else user_menu_en
    try:
        await bot.set_my_commands(menu_to_set, scope=telebot.types.BotCommandScopeChat(chat_id=user_id))
    except Exception as e:
        print(f"Failed to set commands for user {user_id}: {e}")

@authorized_user_only
async def gemini_stream_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "gemini_prompt_help")
        await bot.reply_to(message, escape(help_msg), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, conf['model_2'])

@authorized_user_only
async def gemini_pro_stream_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "gemini_pro_prompt_help")
        await bot.reply_to(message, escape(help_msg), parse_mode="MarkdownV2")
        return
    await gemini.gemini_stream(bot, message, m, conf['model_1'])

@authorized_user_only
async def clear(message: Message, bot: TeleBot) -> None:
    user_id_str = str(message.from_user.id)
    if user_id_str in gemini_chat_dict: del gemini_chat_dict[user_id_str]
    if user_id_str in gemini_pro_chat_dict: del gemini_pro_chat_dict[user_id_str]
    if user_id_str in gemini_draw_dict: del gemini_draw_dict[user_id_str]
    await bot.reply_to(message, get_user_text(message.from_user.id, "history_cleared"))

@authorized_user_only
async def switch(message: Message, bot: TeleBot) -> None:
    if message.chat.type != "private":
        await bot.reply_to(message, get_user_text(message.from_user.id, "private_chat_only"))
        return
    user_id_str = str(message.from_user.id)
    default_model_dict[user_id_str] = not default_model_dict.get(user_id_str, False)
    model_name = conf['model_2'] if not default_model_dict.get(user_id_str) else conf['model_1']
    await bot.reply_to(message, f"{get_user_text(user_id_str, 'now_using_model')} {model_name}")

@authorized_user_only
async def language_status_handler(message: Message, bot: TeleBot) -> None:
    await get_language(bot, message)

@authorized_user_only
async def gemini_private_handler(message: Message, bot: TeleBot) -> None:
    if message.content_type == 'photo':
        s = message.caption or ""
        try:
            file_path = await bot.get_file(message.photo[-1].file_id)
            photo_file = await bot.download_file(file_path.file_path)
            await gemini.gemini_image_understand(bot, message, photo_file, prompt=s)
        except Exception as e:
            traceback.print_exc()
            await bot.reply_to(message, get_user_text(message.from_user.id, "error_info"))
        return

    m = message.text.strip()
    user_id_str = str(message.from_user.id)
    model_to_use = conf['model_1'] if default_model_dict.get(user_id_str, True) else conf['model_2']
    await gemini.gemini_stream(bot, message, m, model_to_use)

@authorized_user_only
async def gemini_photo_handler(message: Message, bot: TeleBot) -> None:
    s = message.caption or ""
    try:
        file_path = await bot.get_file(message.photo[-1].file_id)
        photo_file = await bot.download_file(file_path.file_path)
        if message.chat.type == "private" and not s.startswith("/"):
            await gemini.gemini_image_understand(bot, message, photo_file, prompt=s)
        else:
            m = s.strip().split(maxsplit=1)[1].strip() if s.startswith("/edit") and len(s.strip().split(maxsplit=1)) > 1 else s
            await gemini.gemini_edit(bot, message, m, photo_file)
    except Exception:
        traceback.print_exc()
        await bot.reply_to(message, get_user_text(message.from_user.id, "error_info"))

@authorized_user_only
async def draw_handler(message: Message, bot: TeleBot) -> None:
    try:
        m = message.text.strip().split(maxsplit=1)[1].strip()
        await gemini.gemini_draw(bot, message, m)
    except IndexError:
        await bot.reply_to(message, get_user_text(message.from_user.id, "draw_prompt_help"))

@admin_only
async def system_prompt_handler(message: Message, bot: TeleBot) -> None:
    try:
        prompt = message.text.strip().split(maxsplit=1)[1].strip()
        await set_system_prompt(bot, message, prompt)
    except IndexError:
        help_msg = get_user_text(message.from_user.id, "system_prompt_help")
        await bot.reply_to(message, help_msg)

@admin_only
async def system_prompt_clear_handler(message: Message, bot: TeleBot) -> None:
    await delete_system_prompt(bot, message)

@admin_only
async def system_prompt_reset_handler(message: Message, bot: TeleBot) -> None:
    await reset_system_prompt(bot, message)

@admin_only
async def system_prompt_show_handler(message: Message, bot: TeleBot) -> None:
    await show_system_prompt(bot, message)

@admin_only
async def add_user(message: Message, bot: TeleBot):
    try:
        user_to_add = int(message.text.split()[1])
        users = load_authorized_users()
        if user_to_add in users:
            await bot.reply_to(message, f"⚠️ User {user_to_add} is already authorized.")
            return
        users.add(user_to_add)
        save_authorized_users(users)
        await bot.reply_to(message, f"✅ User {user_to_add} has been added successfully.")
    except (IndexError, ValueError):
        await bot.reply_to(message, "⚠️ Incorrect command format. Use /adduser <user_id>")

@admin_only
async def del_user(message: Message, bot: TeleBot):
    try:
        user_to_del = int(message.text.split()[1])
        if is_admin(user_to_del):
            await bot.reply_to(message, "🚫 Cannot remove an administrator.")
            return
        users = load_authorized_users()
        if user_to_del not in users:
            await bot.reply_to(message, f"⚠️ User {user_to_del} is not found.")
            return
        users.discard(user_to_del)
        save_authorized_users(users)
        await bot.reply_to(message, f"✅ User {user_to_del} has been removed.")
    except (IndexError, ValueError):
        await bot.reply_to(message, "⚠️ Incorrect command format. Use /deluser <user_id>")

@admin_only
async def list_users(message: Message, bot: TeleBot):
    users = load_authorized_users()
    admin_list = "\n".join([f"👑 {uid} (Admin)" for uid in config.ADMIN_UID if uid in users])
    user_list = "\n".join([f"👤 {uid}" for uid in users if not is_admin(uid)])
    response = f"Authorized Users:\n\n{admin_list}\n{user_list}"
    await bot.reply_to(message, response)

@admin_only
async def api_key_add_handler(message: Message, bot: TeleBot):
    user_id = message.from_user.id
    try:
        command_parts = message.text.strip().split(maxsplit=1)
        if len(command_parts) < 2:
            await bot.reply_to(message, get_user_text(user_id, "api_key_add_help"))
            return
            
        keys_text = command_parts[1]
        keys = [key.strip() for key in re.split(r'[\s,]+', keys_text) if key.strip()]

        if not keys:
            await bot.reply_to(message, get_user_text(user_id, "api_key_add_help"))
            return

        added_count, exist_count, invalid_count = 0, 0, 0
        for key in keys:
            if gemini.validate_api_key_format(key):
                if gemini.add_api_key(key):
                    added_count += 1
                else:
                    exist_count += 1
            else:
                invalid_count += 1
        
        response = f"{get_user_text(user_id, 'api_key_bulk_add_summary')}\n"
        if added_count > 0: response += f"✅ {added_count} {get_user_text(user_id, 'api_key_added_count')}\n"
        if exist_count > 0: response += f"⚠️ {exist_count} {get_user_text(user_id, 'api_key_exist_count')}\n"
        if invalid_count > 0: response += f"❌ {invalid_count} {get_user_text(user_id, 'api_key_invalid_count')}\n"
        
        await bot.reply_to(message, response.strip())

    except Exception:
        traceback.print_exc()
        await bot.reply_to(message, get_user_text(user_id, "api_key_add_help"))

@admin_only
async def api_key_remove_handler(message: Message, bot: TeleBot):
    user_id = message.from_user.id
    try:
        arg = message.text.strip().split(maxsplit=1)[1].strip().lower()

        if arg == 'all':
            remove_all_api_keys()
            await bot.reply_to(message, get_user_text(user_id, "api_key_all_removed"))
            return

        try:
            index = int(arg)
            if 0 <= index < len(gemini.api_keys):
                key_to_remove = gemini.api_keys[index]
                if gemini.remove_api_key(key_to_remove):
                    await bot.reply_to(message, get_user_text(user_id, "api_key_removed"))
                else:
                    await bot.reply_to(message, get_user_text(user_id, "api_key_not_found"))
            else:
                await bot.reply_to(message, get_user_text(user_id, "api_key_switch_invalid"))
            return
        except ValueError:
            pass
        
        await bot.reply_to(message, get_user_text(user_id, "api_key_remove_help"))

    except IndexError:
        await bot.reply_to(message, get_user_text(user_id, "api_key_remove_help"))
    except Exception as e:
        traceback.print_exc()
        await bot.reply_to(message, f"An error occurred: {e}")

@admin_only
async def api_key_list_handler(message: Message, bot: TeleBot):
    keys = list_api_keys()
    if not keys:
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_list_empty"))
        return
    
    response = get_user_text(message.from_user.id, "api_key_list_title") + "\n"
    for i, key in enumerate(keys):
        response += f"`{i}`: `{escape(key)}`\n"
        
    await bot.reply_to(message, response, parse_mode="MarkdownV2")

@admin_only
async def api_key_switch_handler(message: Message, bot: TeleBot):
    try:
        index_to_switch = int(message.text.split(maxsplit=1)[1].strip())
        
        if gemini.set_current_api_key(index_to_switch):
            await bot.reply_to(message, f"{get_user_text(message.from_user.id, 'api_key_switched')} `{index_to_switch}`", parse_mode="MarkdownV2")
        else:
            await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_switch_invalid"))
            
    except (IndexError, ValueError):
        await bot.reply_to(message, get_user_text(message.from_user.id, "api_key_switch_help"))

@admin_only
async def api_check_handler(message: Message, bot: TeleBot):
    user_id = message.from_user.id
    sent_message = await bot.reply_to(message, get_user_text(user_id, "api_checking_message"))
    
    paid_model = conf.get("paid_model_for_check")
    standard_model = conf.get("model_1")
    paid_keys, standard_keys, invalid_keys = await unified_api_key_check(paid_model, standard_model)
    
    # Correctly handle the (index, key) tuples
    title = escape(get_user_text(user_id, 'api_check_results_title'))
    paid_title = escape(f"{get_user_text(user_id, 'api_check_paid_keys')} ({len(paid_keys)})")
    standard_title = escape(f"{get_user_text(user_id, 'api_check_standard_keys')} ({len(standard_keys)})")
    invalid_title = escape(f"{get_user_text(user_id, 'api_check_invalid_keys')} ({len(invalid_keys)})")

    response = f"*{title}*\n\n"
    
    response += f"*{paid_title}*\n"
    if paid_keys:
        for index, key in paid_keys:
            response += f"`{index}`: `{escape(key)}`\n"
            
    response += f"\n*{standard_title}*\n"
    if standard_keys:
        for index, key in standard_keys:
            response += f"`{index}`: `{escape(key)}`\n"
            
    response += f"\n*{invalid_title}*\n"
    if invalid_keys:
        for index, key in invalid_keys:
            response += f"`{index}`: `{escape(key)}`\n"
            
    await bot.edit_message_text(response, sent_message.chat.id, sent_message.message_id, parse_mode="MarkdownV2")