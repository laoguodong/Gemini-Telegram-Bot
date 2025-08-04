import argparse
import asyncio
import sys
import os
import json
import logging

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    stream=sys.stdout
)

import telebot
from telebot.async_telebot import AsyncTeleBot
import handlers
import gemini
from handlers import is_admin, load_authorized_users
import config

logger = logging.getLogger(__name__)

async def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Gemini Telegram Bot")
    parser.add_argument("tg_token", help="Telegram Bot token")
    parser.add_argument("gemini_key", help="Google Gemini API key(s), comma-separated")
    parser.add_argument("--admin-uid", type=int, nargs='+', required=True, help="Space-separated list of administrator User IDs")
    options = parser.parse_args()

    # --- Initialization ---
    config.ADMIN_UID = options.admin_uid

    # Populate API keys from command-line argument
    keys = options.gemini_key.replace('，', ',').split(',')
    for key in keys:
        clean_key = key.strip()
        if clean_key:
            gemini.api_keys.append(clean_key)
    
    logger.info("Argument parsing and API key setup done.")

    # Initialize the Gemini client within the running async loop
    await gemini.initialize_client()

    # Initialize user data file
    if not os.path.exists(config.USER_DATA_FILE):
        logger.warning(f"User file {config.USER_DATA_FILE} not found, creating...")
        with open(config.USER_DATA_FILE, 'w') as f:
            json.dump(list(config.ADMIN_UID), f, indent=4)
        logger.info(f"Administrators {config.ADMIN_UID} have been added to the authorized list.")

    bot = AsyncTeleBot(options.tg_token)
    handlers.register_handlers(bot) # Register all handlers from the handlers module

    # Set bot commands for users
    authorized_users = load_authorized_users()
    for user_id in authorized_users:
        try:
            menu = handlers.admin_menu_zh if is_admin(user_id) else handlers.user_menu_zh
            await bot.set_my_commands(menu, scope=telebot.types.BotCommandScopeChat(user_id))
        except Exception as e:
            logger.error(f"Failed to set commands for user {user_id}: {e}")
    
    await bot.set_my_commands(handlers.user_menu_zh, scope=telebot.types.BotCommandScopeDefault())

    logger.info("Bot init done.")
    logger.info("Starting Gemini_Telegram_Bot polling.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"Bot stopped due to a critical error: {e}", exc_info=True)