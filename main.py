import argparse
import traceback
import asyncio
import re
import telebot
from telebot.async_telebot import AsyncTeleBot
import handlers
from config import conf, generation_config, safety_settings, lang_settings
from gemini import user_language_dict, get_user_lang

# Init args
parser = argparse.ArgumentParser()
parser.add_argument("tg_token", help="Telegram机器人令牌")
parser.add_argument("--keys", nargs="+", help="一个或多个Google Gemini API密钥")
parser.add_argument("--keys_file", help="包含API密钥的文件路径，每行一个密钥")
options = parser.parse_args()

# 确保sys.argv[2]包含所有API密钥，用逗号分隔
import sys
if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
    # 如果用户直接在命令行中提供了第二个位置参数，我们保留它，假设它已经是正确格式的API密钥列表
    pass
elif options.keys or options.keys_file:
    # 处理从命令行参数或文件中获取的API密钥
    api_keys = []
    
    # 从--keys参数获取密钥
    if options.keys:
        for key in options.keys:
            # 移除可能的逗号和空格
            clean_key = key.strip().rstrip(",")
            if clean_key:
                api_keys.append(clean_key)
    
    # 从文件获取密钥
    if options.keys_file:
        try:
            with open(options.keys_file, 'r') as f:
                for line in f:
                    # 移除可能的逗号、空格和换行符
                    clean_key = line.strip().rstrip(",")
                    if clean_key:
                        api_keys.append(clean_key)
        except Exception as e:
            print(f"读取密钥文件时出错: {e}")
    
    # 将处理好的密钥列表添加到sys.argv
    if api_keys:
        if len(sys.argv) <= 2:
            sys.argv.append(",".join(api_keys))
        else:
            sys.argv[2] = ",".join(api_keys)
else:
    # 如果没有提供任何密钥，确保有一个空的sys.argv[2]
    if len(sys.argv) <= 2:
        sys.argv.append("")

print("Arg parse done.")


async def main():
    # Init bot
    bot = AsyncTeleBot(options.tg_token)
    
    # 定义中英文菜单
    menu_zh = [
        telebot.types.BotCommand("start", "开始使用"),
        telebot.types.BotCommand("gemini", f"使用 {conf['model_1']}"),
        telebot.types.BotCommand("gemini_pro", f"使用 {conf['model_2']}"),
        telebot.types.BotCommand("draw", "绘图"),
        telebot.types.BotCommand("edit", "编辑图片"),
        telebot.types.BotCommand("clear", "清除历史记录"),
        telebot.types.BotCommand("switch", "切换默认模型"),
        telebot.types.BotCommand("lang", "切换语言 (中/英)"),
        telebot.types.BotCommand("language", "显示当前语言"),
        telebot.types.BotCommand("system", "设置系统提示词"),
        telebot.types.BotCommand("system_clear", "删除系统提示词"),
        telebot.types.BotCommand("system_reset", "重置系统提示词"),
        telebot.types.BotCommand("system_show", "显示当前系统提示词"),
        telebot.types.BotCommand("api_add", "添加API密钥"),
        telebot.types.BotCommand("api_remove", "删除API密钥"),
        telebot.types.BotCommand("api_list", "查看API密钥列表"),
        telebot.types.BotCommand("api_switch", "切换当前API密钥")
    ]
    
    menu_en = [
        telebot.types.BotCommand("start", "Start"),
        telebot.types.BotCommand("gemini", f"using {conf['model_1']}"),
        telebot.types.BotCommand("gemini_pro", f"using {conf['model_2']}"),
        telebot.types.BotCommand("draw", "draw picture"),
        telebot.types.BotCommand("edit", "edit photo"),
        telebot.types.BotCommand("clear", "Clear all history"),
        telebot.types.BotCommand("switch", "switch default model"),
        telebot.types.BotCommand("lang", "switch language (中/英)"),
        telebot.types.BotCommand("language", "show current language"),
        telebot.types.BotCommand("system", "set system prompt"),
        telebot.types.BotCommand("system_clear", "delete system prompt"),
        telebot.types.BotCommand("system_reset", "reset system prompt"),
        telebot.types.BotCommand("system_show", "show current system prompt"),
        telebot.types.BotCommand("api_add", "add API key"),
        telebot.types.BotCommand("api_remove", "remove API key"),
        telebot.types.BotCommand("api_list", "list all API keys"),
        telebot.types.BotCommand("api_switch", "switch current API key")
    ]
    
    # 默认使用中文菜单
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(menu_zh)
    print("Bot init done.")

    # 语言切换后更新菜单的处理函数
    async def on_lang_changed(message, new_lang):
        user_scope = telebot.types.BotCommandScopeChat(message.chat.id)
        if new_lang == "zh":
            await bot.set_my_commands(menu_zh, scope=user_scope)
        else:
            await bot.set_my_commands(menu_en, scope=user_scope)
    
    # 修改语言切换处理函数，加入菜单切换
    async def language_switch_handler_with_menu(message: telebot.types.Message, bot: AsyncTeleBot) -> None:
        user_id_str = str(message.from_user.id)
        current_lang = get_user_lang(user_id_str)
        
        # 切换语言
        new_lang = "en" if current_lang == "zh" else "zh"
        user_language_dict[user_id_str] = new_lang
        
        # 更新菜单
        await on_lang_changed(message, new_lang)
        
        # 发送语言切换确认消息
        await bot.reply_to(message, lang_settings[new_lang]["language_switched"])

    # Init commands
    bot.register_message_handler(handlers.start,                         commands=['start'],         pass_bot=True)
    bot.register_message_handler(handlers.gemini_stream_handler,         commands=['gemini'],        pass_bot=True)
    bot.register_message_handler(handlers.gemini_pro_stream_handler,     commands=['gemini_pro'],    pass_bot=True)
    bot.register_message_handler(handlers.draw_handler,                  commands=['draw'],          pass_bot=True)
    bot.register_message_handler(handlers.gemini_edit_handler,           commands=['edit'],          pass_bot=True)
    bot.register_message_handler(handlers.clear,                         commands=['clear'],         pass_bot=True)
    bot.register_message_handler(handlers.switch,                        commands=['switch'],        pass_bot=True)
    bot.register_message_handler(language_switch_handler_with_menu,      commands=['lang'],          pass_bot=True)
    bot.register_message_handler(handlers.language_status_handler,       commands=['language'],      pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_handler,         commands=['system'],        pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_clear_handler,   commands=['system_clear'],  pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_reset_handler,   commands=['system_reset'],  pass_bot=True)
    bot.register_message_handler(handlers.system_prompt_show_handler,    commands=['system_show'],   pass_bot=True)
    bot.register_message_handler(handlers.api_key_add_handler,           commands=['api_add'],       pass_bot=True)
    bot.register_message_handler(handlers.api_key_remove_handler,        commands=['api_remove'],    pass_bot=True)
    bot.register_message_handler(handlers.api_key_list_handler,          commands=['api_list'],      pass_bot=True)
    bot.register_message_handler(handlers.api_key_switch_handler,        commands=['api_switch'],    pass_bot=True)
    bot.register_message_handler(handlers.gemini_photo_handler,          content_types=["photo"],    pass_bot=True)
    bot.register_message_handler(
        handlers.gemini_private_handler,
        func=lambda message: message.chat.type == "private",
        content_types=['text'],
        pass_bot=True)

    # Start bot
    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    asyncio.run(main())
