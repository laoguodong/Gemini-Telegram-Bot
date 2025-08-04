import argparse
import asyncio
import sys
import os
import json
import logging

# --- Logging Setup ---
# Configure logging before importing other project modules to ensure they inherit the config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    stream=sys.stdout
)

import telebot
from telebot.async_telebot import AsyncTeleBot
import handlers
from handlers import is_admin, load_authorized_users
import config

logger = logging.getLogger(__name__)

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Gemini Telegram Bot")
parser.add_argument("tg_token", help="Telegram Bot token")
parser.add_argument("gemini_key", help="Google Gemini API key")
parser.add_argument("--admin-uid", type=int, nargs='+', required=True, help="Space-separated list of administrator User IDs")

options = parser.parse_args()

# --- Initialization ---

# Set admin UIDs from command line arguments
config.ADMIN_UID = options.admin_uid

# Pass Gemini API key to the gemini module
if options.gemini_key:
    # This part is tricky as gemini.py reads from sys.argv. 
    # A better approach would be to refactor gemini.py to accept the key directly.
    # For now, we will modify sys.argv as the original code did.
    if len(sys.argv) > 2:
        sys.argv[2] = options.gemini_key

logger.info("Argument parsing done.")

def initialize_users():
    """Initializes the user data file, adding admins if the file is new."""
    if not os.path.exists(config.USER_DATA_FILE):
        logger.warning(f"User file {config.USER_DATA_FILE} not found, creating...")
        with open(config.USER_DATA_FILE, 'w') as f:
            json.dump(list(config.ADMIN_UID), f, indent=4)
        logger.info(f"Administrators {config.ADMIN_UID} have been added to the authorized list.")

initialize_users()

bot = AsyncTeleBot(options.tg_token)

# --- Handler Registrations (using decorators) ---

@bot.message_handler(commands=['start'])
async def start(message):
    await handlers.start(message, bot)

@bot.message_handler(commands=['gemini'])
async def gemini_stream_handler(message):
    await handlers.gemini_stream_handler(message, bot)

@bot.message_handler(commands=['gemini_pro'])
async def gemini_pro_stream_handler(message):
    await handlers.gemini_pro_stream_handler(message, bot)

@bot.message_handler(commands=['draw'])
async def draw_handler(message):
    await handlers.draw_handler(message, bot)

@bot.message_handler(commands=['edit'])
async def edit_handler(message):
    await handlers.gemini_edit_handler(message, bot)

@bot.message_handler(commands=['clear'])
async def clear(message):
    await handlers.clear(message, bot)

@bot.message_handler(commands=['switch'])
async def switch(message):
    await handlers.switch(message, bot)

@bot.message_handler(commands=['lang'])
async def lang_switch(message):
    await handlers.language_switch_handler(message, bot)

@bot.message_handler(commands=['language'])
async def lang_status(message):
    await handlers.language_status_handler(message, bot)

# Admin commands
@bot.message_handler(commands=['adduser'])
async def add_user(message):
    await handlers.add_user(message, bot)

@bot.message_handler(commands=['deluser'])
async def del_user(message):
    await handlers.del_user(message, bot)

@bot.message_handler(commands=['listusers'])
async def list_users(message):
    await handlers.list_users(message, bot)

@bot.message_handler(commands=['api_add'])
async def api_add(message):
    await handlers.api_key_add_handler(message, bot)

@bot.message_handler(commands=['api_remove'])
async def api_remove(message):
    await handlers.api_key_remove_handler(message, bot)

@bot.message_handler(commands=['api_list'])
async def api_list(message):
    await handlers.api_key_list_handler(message, bot)

@bot.message_handler(commands=['api_switch'])
async def api_switch(message):
    await handlers.api_key_switch_handler(message, bot)

@bot.message_handler(commands=['api_check'])
async def api_check(message):
    await handlers.api_check_handler(message, bot)

@bot.message_handler(commands=['api_clean'])
async def api_clean(message):
    await handlers.api_clean_handler(message, bot)

@bot.message_handler(commands=['system'])
async def system_prompt(message):
    await handlers.system_prompt_handler(message, bot)

@bot.message_handler(commands=['system_clear'])
async def system_clear(message):
    await handlers.system_prompt_clear_handler(message, bot)

@bot.message_handler(commands=['system_reset'])
async def system_reset(message):
    await handlers.system_prompt_reset_handler(message, bot)

@bot.message_handler(commands=['system_show'])
async def system_show(message):
    await handlers.system_prompt_show_handler(message, bot)

# Content handlers
@bot.message_handler(content_types=['photo'])
async def photo_handler(message):
    await handlers.gemini_photo_handler(message, bot)

@bot.message_handler(
    func=lambda message: (
        message.chat.type == "private" and
        (not message.entities or not any(e.type == 'bot_command' for e in message.entities))
    ),
    content_types=['text']
)
async def private_text_handler(message):
    logger.info(f"private_text_handler caught message: '{message.text}'")
    await handlers.gemini_private_handler(message, bot)

async def main():
    # Set commands for each user based on their role
    authorized_users = load_authorized_users()
    for user_id in authorized_users:
        try:
            if is_admin(user_id):
                # Set admin menu
                await bot.set_my_commands(handlers.admin_menu_zh, scope=telebot.types.BotCommandScopeChat(user_id), language_code='zh')
                await bot.set_my_commands(handlers.admin_menu_en, scope=telebot.types.BotCommandScopeChat(user_id), language_code='en')
            else:
                # Set user menu
                await bot.set_my_commands(handlers.user_menu_zh, scope=telebot.types.BotCommandScopeChat(user_id), language_code='zh')
                await bot.set_my_commands(handlers.user_menu_en, scope=telebot.types.BotCommandScopeChat(user_id), language_code='en')
        except Exception as e:
            logger.error(f"Failed to set commands for user {user_id}: {e}")

    # Set a default menu for users who are not yet authorized
    await bot.set_my_commands(handlers.user_menu_zh, scope=telebot.types.BotCommandScopeDefault(), language_code='zh')
    await bot.set_my_commands(handlers.user_menu_en, scope=telebot.types.BotCommandScopeDefault(), language_code='en')

    logger.info("Bot init done.")
    logger.info("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
