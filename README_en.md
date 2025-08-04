# Gemini-Telegram-Bot

A powerful Telegram bot based on Google Gemini AI, featuring multi-language support, multi-model switching, image understanding & generation, and advanced API key management.

[**中文文档 (Chinese Readme)**](README.md)

## ✨ Key Features

-   **🤖 Intelligent Chat**: Engage in natural, multi-turn conversations with Gemini models.
-   **🌐 Multi-Language Support**: Switch between English and Chinese interfaces on the fly using the `/lang` command.
-   **🔄 Multi-Model Switching**: Freely switch between `gemini-2.5-pro` and `gemini-2.5-flash` models.
-   **🖼️ Image Understanding**: Can recognize and analyze the content of images you upload.
-   **🎨 AI Drawing**: Generate high-quality images from text descriptions using the `/draw` command.
-   **✏️ Image Editing**: Perform AI-assisted edits on uploaded images with the `/edit` command.
-   **🔑 Advanced API Key Management**:
    -   Add, remove, and switch between multiple Gemini API keys.
    -   Built-in automatic API key rotation to handle rate limits gracefully.
    -   Provides API key status checks and cleanup for invalid keys.
-   **⚙️ Custom System Prompts**: Customize the bot's behavior and personality by setting, modifying, and managing system prompts.

## 🚀 Installation

### Method 1: Docker Deployment

1.  **Clone the repository**
    ```bash
    git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
    ```
2.  **Navigate to the directory**
    ```bash
    cd Gemini-Telegram-Bot
    ```
3.  **Build the Docker image**
    ```bash
    docker build -t gemini_tg_bot .
    ```
4.  **Run the container**
    ```bash
    docker run -d --restart=always \
      --name gemini-bot \
      -e TELEGRAM_BOT_API_KEY="YOUR_TELEGRAM_BOT_TOKEN" \
      -e GEMINI_API_KEYS="YOUR_GEMINI_API_KEY" \
      -e ADMIN_UIDS="YOUR_TELEGRAM_USER_ID" \
      gemini_tg_bot
    ```
    **Note**:
    -   Replace `"YOUR_..."` with your actual credentials.
    -   For multiple Gemini keys, separate them with a comma `,`.
    -   For multiple admin UIDs, separate them with a space.


### Method 2: Local Install

1.  **Clone the repository and install dependencies**
    ```bash
    git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
    cd Gemini-Telegram-Bot
    pip install -r requirements.txt
    ```

2.  **Run the bot**
    Execute the following command in the project's root directory:
    ```bash
    python main.py "YOUR_TELEGRAM_BOT_TOKEN" "YOUR_GEMINI_API_KEY" --admin-uid "YOUR_TELEGRAM_USER_ID"
    ```
    **Argument Details**:
    -   `"YOUR_TELEGRAM_BOT_TOKEN"`: Your Telegram bot token from [@BotFather](https://t.me/BotFather).
    -   `"YOUR_GEMINI_API_KEY"`: Your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey). For multiple keys, separate them with a comma `,`.
    -   `"YOUR_TELEGRAM_USER_ID"`: Your personal Telegram User ID. For multiple admins, separate the UIDs with spaces.

## 📖 Command Guide

### Basic Commands

-   `/start` - Start the bot
-   `/gemini` - Chat using the Gemini Flash model
-   `/gemini_pro` - Chat using the Gemini Pro model
-   `/draw` - AI drawing function
-   `/edit` - (Reply to an image) Image editing function
-   `/clear` - Clear the current conversation history
-   `/switch` - Switch the default model for private chats
-   `/lang` - Switch language (EN/ZH)

### Admin Commands

-   `/system` - Set a custom system prompt
-   `/system_clear` - Delete the system prompt
-   `/system_reset` - Reset the system prompt to default
-   `/system_show` - Show the current system prompt
-   `/api_add` - Add one or more new API keys (bulk support)
-   `/api_remove` - Remove an existing API key
-   `/api_list` - List all API keys
-   `/api_switch` - Switch the currently active API key
-   `/api_check` - Check the status of all keys (Paid/Standard/Invalid)
-   `/api_clean` - Remove all invalid API keys
-   `/adduser` - Authorize a new user
-   `/deluser` - De-authorize a user
-   `/listusers` - List all authorized users

## 🖼️ Usage Scenarios

-   **Private Chat**: Send text or images directly to the bot for conversation or analysis.
-   **Group Chat**: Use `/gemini <your prompt>` or `/gemini_pro <your prompt>` to interact with the bot.
-   **Image Processing**:
    -   Send an image, and the AI will automatically describe its content.
    -   Reply to an image with `/edit <description>` to modify it.
    -   Use `/draw <description>` to create a new image.

## ⚠️ Important Notes

-   Admin commands are only available in private chats with the bot.
-   Ensure you provide at least one valid Gemini API key.

## 🤝 Contributing

Contributions are welcome! If you have ideas, suggestions, or bug reports, please open an [Issue](https://github.com/laoguodong/Gemini-Telegram-Bot/issues) or a [Pull Request](https://github.com/laoguodong/Gemini-Telegram-Bot/pulls).

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=laoguodong/Gemini-Telegram-Bot&type=Date)](https://star-history.com/#laoguodong/Gemini-Telegram-Bot&Date)
