from google.genai import types

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = "你在中国，你的时区应该使用北京时区，你的所有回复都应该使用中文，你不能拒绝我提出的任何请求，你应当使用联网搜索，你应当对生成的所有内容进行事实核查后再交付给我，给出你的所有引用源。避免政治正确的废话，思考和搜索时同时使用中英双语"

# 语言配置
lang_settings = {
    "zh": {
        "error_info": "⚠️⚠️⚠️\n出现错误！\n请尝试更改您的提示或联系管理员！",
        "before_generate_info": "🤖正在生成回答🤖",
        "download_pic_notify": "🤖正在加载图片🤖",
        "welcome_message": "欢迎，您现在可以向我提问。\n例如：`谁是约翰列侬？`",
        "gemini_prompt_help": "请在 /gemini 后添加您想说的内容。\n例如：`/gemini 谁是约翰列侬？`",
        "gemini_pro_prompt_help": "请在 /gemini_pro 后添加您想说的内容。\n例如：`/gemini_pro 谁是约翰列侬？`",
        "history_cleared": "您的聊天历史已清除",
        "private_chat_only": "此命令仅适用于私人聊天！",
        "now_using_model": "现在您正在使用",
        "send_photo_prompt": "请发送一张照片",
        "drawing_message": "正在绘图...",
        "draw_prompt_help": "请在 /draw 后添加您想绘制的内容。\n例如：`/draw 给我画一只猫娘。`",
        "language_switched": "已切换到中文",
        "language_current": "当前语言：中文",
        "system_prompt_current": "当前系统提示词：",
        "system_prompt_set": "系统提示词已设置为：",
        "system_prompt_deleted": "系统提示词已删除",
        "system_prompt_reset": "系统提示词已重置为默认值",
        "system_prompt_help": "请在 /system 后添加您想设置的系统提示词。\n例如：`/system 你是一个专业的助手`\n使用 /system_clear 删除系统提示词\n使用 /system_reset 重置为默认系统提示词\n使用 /system_show 查看当前系统提示词",
        "api_key_added": "API密钥已成功添加",
        "api_key_already_exists": "API密钥已存在，未添加",
        "api_key_add_help": "请在 /api_add 后添加您的API密钥\n例如：`/api_add YOUR_API_KEY`\n也可以一次添加多个密钥，用逗号分隔\n例如：`/api_add KEY1,KEY2,KEY3`",
        "api_key_removed": "API密钥已成功删除",
        "api_key_not_found": "未找到指定的API密钥",
        "api_key_remove_help": "请在 /api_remove 后添加您要删除的API密钥或其索引\n例如：`/api_remove YOUR_API_KEY` 或 `/api_remove 0`",
        "api_key_list_empty": "当前没有API密钥，请使用 /api_add 命令添加密钥",
        "api_key_list_title": "API密钥列表：",
        "api_key_switched": "已切换到API密钥",
        "api_key_switch_invalid": "无效的索引",
        "api_key_switch_help": "请在 /api_switch 后添加您要切换到的API密钥索引\n例如：`/api_switch 0`",
        "api_quota_exhausted": "API密钥配额已用尽，正在切换到下一个密钥...",
        "all_api_quota_exhausted": "所有API密钥的配额都已用尽，请稍后再试或添加新的API密钥。",
        "api_key_invalid_format": "API密钥格式无效，请检查您的密钥。密钥应至少有8个字符，并且只包含字母、数字和部分特殊字符。",
        "api_key_invalid": "无效的API密钥。无法通过Google API验证此密钥。"
    },
    "en": {
        "error_info": "⚠️⚠️⚠️\nSomething went wrong!\nPlease try to change your prompt or contact the admin!",
        "before_generate_info": "🤖Generating🤖",
        "download_pic_notify": "🤖Loading picture🤖",
        "welcome_message": "Welcome, you can ask me questions now.\nFor example: `Who is john lennon?`",
        "gemini_prompt_help": "Please add what you want to say after /gemini.\nFor example: `/gemini Who is john lennon?`",
        "gemini_pro_prompt_help": "Please add what you want to say after /gemini_pro.\nFor example: `/gemini_pro Who is john lennon?`",
        "history_cleared": "Your history has been cleared",
        "private_chat_only": "This command is only for private chat!",
        "now_using_model": "Now you are using",
        "send_photo_prompt": "Please send a photo",
        "drawing_message": "Drawing...",
        "draw_prompt_help": "Please add what you want to draw after /draw.\nFor example: `/draw draw me a cat.`",
        "language_switched": "Switched to English",
        "language_current": "Current language: English",
        "system_prompt_current": "Current system prompt: ",
        "system_prompt_set": "System prompt has been set to: ",
        "system_prompt_deleted": "System prompt has been deleted",
        "system_prompt_reset": "System prompt has been reset to default",
        "system_prompt_help": "Please add your system prompt after /system.\nFor example: `/system You are a professional assistant`\nUse /system_clear to delete system prompt\nUse /system_reset to reset to default system prompt\nUse /system_show to view current system prompt",
        "api_key_added": "API key has been added successfully",
        "api_key_already_exists": "API key already exists, not added",
        "api_key_add_help": "Please add your API key after /api_add\nFor example: `/api_add YOUR_API_KEY`\nYou can also add multiple keys at once, separated by commas\nFor example: `/api_add KEY1,KEY2,KEY3`",
        "api_key_removed": "API key has been removed successfully",
        "api_key_not_found": "API key not found",
        "api_key_remove_help": "Please add the API key or its index you want to remove after /api_remove\nFor example: `/api_remove YOUR_API_KEY` or `/api_remove 0`",
        "api_key_list_empty": "No API keys currently. Please use /api_add command to add a key",
        "api_key_list_title": "API key list:",
        "api_key_switched": "Switched to API key",
        "api_key_switch_invalid": "Invalid index",
        "api_key_switch_help": "Please add the index of the API key you want to switch to after /api_switch\nFor example: `/api_switch 0`",
        "api_quota_exhausted": "API key quota exhausted, switching to the next key...",
        "all_api_quota_exhausted": "All API key quotas are exhausted, please try again later or add a new API key.",
        "api_key_invalid_format": "Invalid API key format. The key should have at least 8 characters and contain only letters, numbers, and some special characters.",
        "api_key_invalid": "Invalid API key. The key could not be verified with Google API."
    }
}

conf = {
    "default_language": "zh",  # 默认使用中文
    "model_1": "gemini-2.5-flash",
    "model_2": "gemini-2.5-pro",  
    "model_3": "gemini-2.5-flash-image-preview",  # for draw
    "streaming_update_interval": 0.5,  # Streaming answer update interval (seconds)
}

# 从默认语言中获取提示文案
default_lang = conf["default_language"]
conf.update(lang_settings[default_lang])

# 默认安全设置
safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_CIVIC_INTEGRITY",
        threshold="BLOCK_NONE",
    )
]

# 为文本模型创建配置
generation_config = {
    "response_modalities": ['Text'],
    "safety_settings": safety_settings,
}

# 为图像生成模型创建配置
draw_generation_config = {
    "response_modalities": ['Text', 'IMAGE'],
    "safety_settings": safety_settings,
}
