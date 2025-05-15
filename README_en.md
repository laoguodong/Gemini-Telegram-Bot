# Gemini-Telegram-Bot

A powerful Telegram bot based on Google Gemini AI, supporting multiple languages, models, image understanding, and generation.

[中文文档](https://github.com/laoguodong/Gemini-Telegram-Bot/blob/main/README.md)

## ✨ Key Features

- 💬 **Intelligent Conversation**: Support natural, coherent multi-turn dialogues with Gemini models
- 🌐 **Multi-language Support**: Built-in Chinese and English interfaces, easily switchable
- 🔄 **Multi-model Switching**: Freedom to switch between different Gemini models
- 📸 **Image Understanding**: Ability to recognize and analyze content in uploaded images
- 🎨 **AI Drawing**: Generate images from text descriptions
- ✏️ **Image Editing**: Support AI-assisted editing of uploaded images
- 🔑 **Multiple API Key Management**: Add, remove, and switch between multiple Gemini API keys
- 📝 **Custom System Prompts**: Set, modify, and manage system prompts

## 🚀 Installation Methods

### Method 1 (Railway One-Click Deploy)

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/ya_ZL5?referralCode=HPHyYT)

### Method 2 (Docker Deployment)

1. Clone the repository
   ```bash
   git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
   ```

2. Navigate to the project directory
   ```bash
   cd Gemini-Telegram-Bot
   ```

3. Build Docker image
   ```bash
   docker build -t gemini_tg_bot .
   ```

4. Run container
   ```bash
   docker run -d --restart=always -e TELEGRAM_BOT_API_KEY={Telegram_Bot_API} -e GEMINI_API_KEYS={Gemini_API_Key} gemini_tg_bot
   ```

### Method 3 (Linux Installation)

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Obtain Telegram Bot API key from [BotFather](https://t.me/BotFather)

3. Get Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

4. Run the bot
   ```bash
   python main.py ${Telegram_Bot_API} ${Gemini_API_Key}
   ```

## 📖 User Guide

### Basic Commands

- `/start` - Start using the bot
- `/gemini` - Use Gemini model
- `/gemini_pro` - Use Gemini Pro model
- `/draw` - AI drawing functionality
- `/edit` - Image editing functionality
- `/clear` - Clear current conversation history
- `/switch` - Switch default model
- `/lang` - Switch language (Chinese/English)
- `/language` - Display current language setting

### System Prompt Management

- `/system` - Set system prompt
- `/system_clear` - Delete system prompt
- `/system_reset` - Reset system prompt to default
- `/system_show` - Show current system prompt

### API Key Management

- `/api_add` - Add new API key
- `/api_remove` - Remove existing API key
- `/api_list` - View all API keys
- `/api_switch` - Switch current API key

### Usage Scenarios

1. **Private Chat Mode**: Directly send text or images for conversation
2. **Group Chat Mode**: Use `/gemini` or `/gemini_pro` commands plus your question
3. **Image Processing**:
   - Send an image for AI to recognize content
   - Use `/edit` + image + description for image editing
   - Use `/draw` + description to generate AI images

## 📋 Important Notes

- Some features (such as API key management) are only available in private chat mode
- Ensure API key format is correct for proper functionality
- System prompts affect AI response style and can be customized as needed

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=laoguodong/Gemini-Telegram-Bot&type=Date)](https://star-history.com/#laoguodong/Gemini-Telegram-Bot&Date)
