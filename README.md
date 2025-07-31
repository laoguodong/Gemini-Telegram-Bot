# Gemini Telegram Bot

这是一个功能强大、可高度定制的 Telegram 机器人，它利用 Google 先进的 Gemini 系列模型，为您提供流畅的对话、强大的图像理解以及创意无限的绘图功能。

## ✨ 核心功能

- **🚀 多模型支持**: 内置支持 `gemini-2.5-pro` 和 `gemini-2.5-flash` 等多种模型，并可通过配置文件轻松扩展。
- **🔑 强大的API密钥管理**:
  - **多密钥池**: 支持添加多个 Gemini API 密钥。
  - **自动故障转移**: 当一个密钥的配额用尽时，系统会自动无缝切换到下一个可用密钥，确保服务持续稳定。
  - **动态管理**: 管理员可以直接通过聊天命令添加、删除、列出和切换API密钥，无需重启机器人。
- **👥 完善的权限系统**:
  - **管理员与用户角色**: 区分管理员和普通授权用户。
  - **动态菜单**: 根据用户角色自动显示不同的命令菜单（管理员拥有更多管理权限）。
  - **用户管理**: 管理员可随时添加或移除授权用户。
- **🖼️ 多模态能力**:
  - **图像理解**: 发送图片即可获得详细的描述和分析。
  - **文本生成图像**: 使用 `/draw` 命令，将您的想法变为精美图片。
- **💬 智能对话**:
  - **流式响应**: 打字机般的逐字响应，提升交互体验。
  - **上下文记忆**: 支持连续对话，能记住之前的聊天内容。
  - **自定义系统提示词**: 管理员可以为机器人设定特定的角色和行为（例如，`你是一个专业的翻译官`）。
- **🌐 多语言支持**: 内置支持中文和英文，可轻松切换。

## 🚀 部署方式

在开始之前，您需要准备好以下三样东西：
1.  **Telegram Bot Token**: 从 [@BotFather](https://t.me/BotFather) 获取。
2.  **Google Gemini API Key**: 从 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取。
3.  **管理员Telegram用户ID**: 从 [@userinfobot](https://t.me/userinfobot) 获取。

### 方式一：Railway 一键部署 (推荐)

点击下方按钮，即可在 Railway 平台上一键部署。这是最简单、最快捷的方式。

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/ya_ZL5?referralCode=HPHyYT)

部署时，您需要在 Railway 的环境变量设置中填入 `TELEGRAM_BOT_API_KEY`, `GEMINI_API_KEYS`, 和 `ADMIN_UIDS` 这三个变量。

### 方式二：Docker 部署

1.  **克隆项目**
    ```bash
    git clone https://github.com/your-username/Gemini-Telegram-Bot.git
    cd Gemini-Telegram-Bot
    ```

2.  **构建 Docker 镜像**
    ```bash
    docker build -t gemini_tg_bot .
    ```

3.  **运行 Docker 容器**
    使用以下命令运行容器。请将占位符替换为您的真实信息。
    ```bash
    docker run -d --restart=always \
      -e TELEGRAM_BOT_API_KEY="<你的Telegram机器人TOKEN>" \
      -e GEMINI_API_KEYS="<你的Gemini_API密钥>" \
      -e ADMIN_UIDS="<你的Telegram用户ID>" \
      --name my_gemini_bot \
      gemini_tg_bot
    ```
    - 如果有多个管理员，`ADMIN_UIDS` 用空格隔开，例如 `"123456789 987654321"`。

### 方式三：本地运行

1.  **克隆项目并安装依赖**
    ```bash
    git clone https://github.com/your-username/Gemini-Telegram-Bot.git
    cd Gemini-Telegram-Bot
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

2.  **运行机器人**
    使用以下命令启动。请将占位符替换为您的真实信息。
    ```bash
    python main.py <你的Telegram机器人TOKEN> <你的Gemini_API密钥> --admin-uid <你的Telegram用户ID>
    ```
    - 如果有多个管理员，`--admin-uid` 后面跟多个ID，用空格隔开。
    - 为了让机器人在后台持续运行，建议使用 `nohup` 或 `tmux`。

## 🤖 命令列表

### 普通用户命令
- `/start` - ✨ 开始使用机器人
- `/gemini` - 💬 使用默认模型 (`gemini-2.5-pro`) 进行对话
- `/gemini_pro` - ⚡️ 使用备用模型 (`gemini-2.5-flash`) 进行对话
- `/draw` - 🎨 绘图（例如: `/draw 一只太空猫`）
- `/clear` - 🗑️ 清除当前会话历史
- `/switch` - 🔄 在两个默认对话模型之间切换
- `/lang` - 🌐 切换语言 (中/英)

### 管理员命令
管理员拥有所有普通用户命令，并额外包含以下管理功能：

- **用户管理**
  - `/adduser <用户ID>` - ✅ 添加一个授权用户
  - `/deluser <用户ID>` - ❌ 删除一个授权用户
  - `/listusers` - 👥 列出所有授权用户

- **系统提示词 (System Prompt)**
  - `/system <提示词>` - ⚙️ 设置机器人的系统提示词
  - `/system_show` - 📄 查看当前的系统提示词
  - `/system_clear` - 🗑️ 删除系统提示词
  - `/system_reset` - 🔄 重置为默认系统提示词

- **API密钥管理**
  - `/api_add <密钥>` - 🔑 添加一个或多个Gemini API密钥（多个密钥用逗号隔开）
  - `/api_remove <密钥或索引>` - 🗑️ 删除一个指定的API密钥
  - `/api_list` - 📋 列出所有API密钥及其状态
  - `/api_switch <索引>` - 🔄 切换当前使用的API密钥

## ⚙️ 高级配置

您可以通过修改 `config.py` 文件来进行更深度的定制：
- **默认模型**: 您可以修改 `model_1`, `model_2`, `model_3` 的值来更换默认的对话和绘图模型。
- **默认系统提示词**: 您可以修改 `DEFAULT_SYSTEM_PROMPT` 来改变机器人的默认行为。
- **安全设置**: `safety_settings` 允许您调整内容审查的严格程度。

## 📄 许可证

本项目基于 [MIT License](LICENSE) 授权。
