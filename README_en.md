# Gemini-Telegram-Bot

A powerful and highly customizable Telegram bot that leverages Google's Gemini API to provide advanced conversation, image understanding, and generation capabilities.

## ✨ Features

- **Multi-Model Support**: Seamlessly switch and use different Gemini models (uses `gemini-2.5-pro` and `gemini-2.5-flash` by default).
- **Multimodal Interaction**:
  - **Text Conversation**: Engage in fluent, context-aware dialogues.
  - **Image Understanding**: Send a picture to ask questions or get descriptions.
  - **Image Generation**: Create new images from text descriptions (uses `gemini-2.0-flash-preview-image-generation`).
- **Robust API Key Management**:
  - **Multiple Key Support**: Add multiple API keys.
  - **Automatic Failover**: Automatically switches to the next available key if the current one fails or runs out of quota.
  - **Dynamic Management**: Admins can dynamically add, remove, list, switch, and check keys via commands.
  - **Smart Cleanup**: Automatically detect and remove all invalid API keys with a single command.
- **Advanced Admin Features**:
  - **User Authorization System**: Control who can use your bot.
  - **Custom System Prompts**: Set different roles or instructions for the bot on a per-user basis.
  - **Key Status Check**: One-click command to check the status of all keys (Paid/Standard/Invalid). The model for paid checks can be configured via `paid_model_for_check` in `config.py`.
- **User-Friendly**:
  - **Streaming Responses**: Typewriter effect for an enhanced interactive experience.
  - **Multi-Language Support**: Built-in support for English and Chinese.
  - **Session Management**: Maintains separate conversation histories for each user.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- A Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))
- A Google Gemini API Key (get it from [Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/wzpan/Gemini-Telegram-Bot.git
cd Gemini-Telegram-Bot

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Bot

It is **highly recommended** to start the bot using command-line arguments to avoid hard-coding sensitive information:

```bash
python main.py <YOUR_TG_BOT_TOKEN> <YOUR_GEMINI_API_KEY> --admin-uid <YOUR_ADMIN_UID>
```

- `<YOUR_TG_BOT_TOKEN>`: Your Telegram bot token.
- `<YOUR_GEMINI_API_KEY>`: Your Google Gemini API key. You can provide one or more keys, separated by commas `,`.
- `<YOUR_ADMIN_UID>`: Your Telegram User ID. You can provide one or more admin UIDs, separated by spaces.

**Example:**
```bash
python main.py 123456:ABC-DEF your_api_key_1,your_api_key_2 --admin-uid 123456789 987654321
```

## 🤖 Command Usage

### User Commands

- `/start` - Start interacting with the bot.
- `/gemini <prompt>` - Chat using the `gemini-2.5-flash` model.
- `/gemini_pro <prompt>` - Chat using the `gemini-2.5-pro` model.
- `/draw <prompt>` - Generate an image.
- `/clear` - Clear your conversation history.
- `/switch` - Switch the default model (`gemini-2.5-pro` or `gemini-2.5-flash`) in a private chat.
- `/lang` - Switch the interface language (English/Chinese).

### 👑 Admin Commands

#### User Management
- `/adduser <user_id>` - Authorize a new user.
- `/deluser <user_id>` - De-authorize a user.
- `/listusers` - List all authorized users.

#### System Prompt
- `/system <prompt>` - Set a custom system prompt for yourself.
- `/system_clear` - Clear your system prompt.
- `/system_reset` - Reset to the default system prompt.
- `/system_show` - Show your current system prompt.

#### API Key Management
- `/api_add <keys...>` - Add one or more API keys in bulk, separated by spaces or newlines.
- `/api_remove <index|all>` - Remove a key by its index, or use `all` to remove all keys.
- `/api_list` - List all added API keys with their indices.
- `/api_switch <index>` - Manually switch to the API key at the specified index.
- `/api_check` - Check the status of all keys and classify them as Paid, Standard, or Invalid.
- `/api_clean` - Automatically detect and remove all invalid API keys.

## 🐳 Docker Deployment

```bash
# Build the Docker image
docker build -t gemini_tg_bot .

# Run the container
docker run -d --name gemini-bot \
  -e TELEGRAM_BOT_API_KEY="<YOUR_TG_BOT_TOKEN>" \
  -e GEMINI_API_KEYS="<YOUR_GEMINI_API_KEY>" \
  -e ADMIN_UIDS="<YOUR_ADMIN_UID>" \
  --restart always \
  gemini_tg_bot
```

**Note**: When using Docker, enclose the environment variable values in quotes. For multiple API keys, separate them with commas. For multiple admin UIDs, separate them with spaces.
