# Gemini-Telegram-Bot

一个功能强大的、基于 Google Gemini AI 的 Telegram 机器人，支持多语言、多模型切换、图像理解与生成、多 API 密钥管理等高级功能。

[**English Document**](README_en.md)



## ✨ 主要功能

-   **🤖 智能对话**：支持与 Gemini 模型进行自然、连贯的多轮对话。
-   **🌐 多语言支持**：内置中英文支持，可通过 `/lang` 命令随时切换界面语言。
-   **🔄 多模型切换**：支持在 `gemini-2.5-pro` 和 `gemini-2.5-flash` 模型之间自由切换。
-   **🖼️ 图像理解**：可以识别和分析用户上传的图片内容。
-   **🎨 AI 绘图**：通过文字描述 (`/draw`) 生成高质量图像。
-   **✏️ 图像编辑**：支持对上传的图片进行 AI 辅助编辑 (`/edit`)。
-   **🔑 多 API 密钥管理**：
    -   支持添加、移除和切换多个 Gemini API 密钥。
    -   内置 API 密钥轮询和自动切换机制，从容应对速率限制。
    -   提供 API 密钥状态检查和无效密钥清理功能。
-   **⚙️ 自定义系统提示词**：可以为 AI 设置、修改和管理系统提示词，定制其行为和回复风格。

## 🚀 安装方法

### 方法一 (Docker 部署)

1.  **克隆项目**
    ```bash
    git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
    ```
2.  **进入项目目录**
    ```bash
    cd Gemini-Telegram-Bot
    ```
3.  **构建 Docker 镜像**
    ```bash
    docker build -t gemini_tg_bot .
    ```
4.  **运行容器**
    ```bash
    docker run -d --restart=always \
      --name gemini-bot \
      -e TELEGRAM_BOT_API_KEY="你的Telegram机器人API" \
      -e GEMINI_API_KEYS="你的Gemini API密钥" \
      -e ADMIN_UIDS="你的Telegram User ID" \
      gemini_tg_bot
    ```
    **注意**: 
    -   请将 "你的..." 替换为您的实际信息。
    -   多个 Gemini API 密钥请用英文逗号 `,` 分隔。
    -   多个管理员 ID 请用空格分隔。


### 方法二 (本地运行)

1.  **克隆项目并安装依赖**
    ```bash
    git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
    cd Gemini-Telegram-Bot
    pip install -r requirements.txt
    ```

2.  **运行机器人**
    在项目根目录下，执行以下命令来启动机器人：
    ```bash
    python main.py "你的Bot API Key" "你的Gemini Key" --admin-uid "你的Telegram User ID"
    ```
    **参数说明**:
    -   `"你的Bot API Key"`: 从 [@BotFather](https://t.me/BotFather) 获取的 Telegram Bot Token。
    -   `"你的Gemini Key"`: 从 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取的 Gemini API 密钥。如果你有多个，请用英文逗号 `,` 隔开。
    -   `"你的Telegram User ID"`: 你的 Telegram User ID。如果你想设置多个管理员，请用空格隔开。

## 📖 使用指南

### 基本命令

-   `/start` - 开始使用机器人
-   `/gemini` - 使用 Gemini Flash 模型进行对话
-   `/gemini_pro` - 使用 Gemini Pro 模型进行对话
-   `/draw` - AI 绘图功能
-   `/edit` - (回复图片使用) 图片编辑功能
-   `/clear` - 清除当前对话历史
-   `/switch` - 切换私聊时的默认对话模型
-   `/lang` - 切换语言 (中/英)

### 管理员命令

-   `/system` - 设置系统提示词
-   `/system_clear` - 删除系统提示词
-   `/system_reset` - 重置系统提示词为默认
-   `/system_show` - 显示当前系统提示词
-   `/api_add` - 添加新的 API 密钥 (支持批量)
-   `/api_remove` - 删除现有 API 密钥
-   `/api_list` - 查看所有 API 密钥列表
-   `/api_switch` - 切换当前使用的 API 密钥
-   `/api_check` - 检查所有密钥的状态 (付费/普通/失效)
-   `/api_clean` - 清理所有无效的 API 密钥
-   `/adduser` - 授权新用户
-   `/deluser` - 删除用户
-   `/listusers` - 列出所有授权用户

## 🖼️ 使用场景

-   **私聊模式**：直接向机器人发送文字或图片即可进行智能对话和图像分析。
-   **群组模式**：在群组中，使用 `/gemini <你的问题>` 或 `/gemini_pro <你的问题>` 来与机器人交互。
-   **图像处理**：
    -   直接发送图片，AI 会自动识别图片内容。
    -   回复一张图片并使用 `/edit <你的描述>` 来编辑图像。
    -   使用 `/draw <你的描述>` 来生成 AI 图像。

## ⚠️ 注意事项

-   管理员命令仅限管理员在私聊模式下使用。
-   请确保至少提供一个有效的 Gemini API 密钥。

## 🤝 贡献

欢迎各种形式的贡献！如果你有任何想法、建议或发现 Bug，请随时提交 [Issues](https://github.com/laoguodong/Gemini-Telegram-Bot/issues) 或 [Pull Requests](https://github.com/laoguodong/Gemini-Telegram-Bot/pulls)。

## 🌟 Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=laoguodong/Gemini-Telegram-Bot&type=Date)](https://star-history.com/#laoguodong/Gemini-Telegram-Bot&Date)