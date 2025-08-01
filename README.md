# Gemini-Telegram-Bot

一个功能强大且可高度定制的 Telegram 机器人，它利用 Google 的 Gemini API 来提供先进的对话、图像理解和生成能力。

## ✨ 功能特性

- **多模型支持**: 无缝切换和使用不同的 Gemini 模型 (`gemini-2.5-pro`, `gemini-2.5-flash`, 等)。
- **多模态交互**:
  - **文本对话**: 进行流畅、支持上下文的对话。
  - **图像理解**: 发送图片进行提问或描述。
  - **图像生成**: 根据文本描述创作新图片。
- **健壮的 API 密钥管理**:
  - **多密钥支持**: 可添加多个 API 密钥。
  - **自动故障切换**: 当前密钥失效或额度用尽时，自动切换到下一个可用密钥。
  - **动态管理**: 管理员可通过命令动态添加、删除、列出、切换和检查密钥。
- **高级管理员功能**:
  - **用户授权系统**: 控制谁可以使用您的机器人。
  - **自定义系统提示词**: 为每个用户设置不同的机器人角色或指令。
  - **密钥状态检查**: 一键检查所有密钥的状态（付费/普通/失效）。
- **用户友好**:
  - **流式响应**: 打字机效果，提升交互体验。
  - **多语言支持**: 内置中文和英文界面。
  - **会话管理**: 为每个用户维护独立的对话历史。

## 🚀 快速开始

### 1. 环境准备

- Python 3.9+
- Telegram Bot Token (从 [@BotFather](https://t.me/BotFather) 获取)
- Google Gemini API Key (从 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取)

### 2. 安装

```bash
# 克隆仓库
git clone https://github.com/wzpan/Gemini-Telegram-Bot.git
cd Gemini-Telegram-Bot

# 安装依赖
pip install -r requirements.txt
```

### 3. 运行

通过命令行参数启动机器人：

```bash
python main.py <你的TG_BOT_TOKEN> <你的GEMINI_API_KEY> --admin-uid <你的管理员UID>
```

- `<你的TG_BOT_TOKEN>`: 你的 Telegram 机器人令牌。
- `<你的GEMINI_API_KEY>`: 你的 Google Gemini API 密钥。你可以提供一个或多个密钥，用逗号分隔。
- `<你的管理员UID>`: 你的 Telegram User ID。你可以提供一个或多个管理员UID，用空格分隔。

**示例:**
```bash
python main.py 123456:ABC-DEF your_api_key_1,your_api_key_2 --admin-uid 123456789 987654321
```

## 🤖 命令用法

### 普通用户命令

- `/start` - 开始使用机器人。
- `/gemini <prompt>` - 使用 `gemini-2.5-flash` 模型进行对话。
- `/gemini_pro <prompt>` - 使用 `gemini-2.5-pro` 模型进行对话。
- `/draw <prompt>` - 生成一张图片。
- `/clear` - 清除您的对话历史。
- `/switch` - 在私聊中切换默认使用的模型 (`gemini-2.5-pro` 或 `gemini-2.5-flash`)。
- `/lang` - 切换界面语言 (中文/英文)。

### 👑 管理员命令

#### 用户管理
- `/adduser <user_id>` - 授权一个新用户。
- `/deluser <user_id>` - 移除一个用户的授权。
- `/listusers` - 列出所有已授权的用户。

#### 系统提示词
- `/system <prompt>` - 为您自己设置一个自定义的系统提示词。
- `/system_clear` - 清除您的系统提示词。
- `/system_reset` - 重置为默认的系统提示词。
- `/system_show` - 查看当前的系统提示词。

#### API 密钥管理
- `/api_add <keys...>` - 批量添加一个或多个API密钥，用空格或换行分隔。
- `/api_remove <index|all>` - 按索引号删除一个密钥，或使用 `all` 删除所有密钥。
- `/api_list` - 列出所有已添加的API密钥及其索引。
- `/api_switch <index>` - 手动切换到指定索引的API密钥。
- `/api_check` - 检查所有密钥的状态，并将其分类为付费、普通或失效。

## 🐳 Docker 部署

```bash
# 构建 Docker 镜像
docker build -t gemini_tg_bot .

# 运行容器
docker run -d --name gemini-bot \
  -e TELEGRAM_BOT_API_KEY="<你的TG_BOT_TOKEN>" \
  -e GEMINI_API_KEYS="<你的GEMINI_API_KEY>" \
  -e ADMIN_UIDS="<你的管理员UID>" \
  gemini_tg_bot
```

**注意**: 在 Docker 中，环境变量的值应该用引号括起来。多个 API 密钥请用逗号分隔，多个管理员 UID 请用空格分隔。



```