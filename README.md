# Gemini-Telegram-Bot

一个功能强大的基于Google Gemini AI的Telegram机器人，支持多语言、多模型、图像理解与生成等功能。

[English Document](https://github.com/laoguodong/Gemini-Telegram-Bot/blob/main/README_en.md)

## ✨ 主要功能

- 💬 **智能对话**：支持与Gemini模型进行自然、连贯的多轮对话
- 🌐 **多语言支持**：内置中英文支持，可随时切换界面语言
- 🔄 **多模型切换**：支持在Gemini模型之间自由切换
- 📸 **图像理解**：可以识别和分析用户上传的图片内容
- 🎨 **AI绘图**：通过文字描述生成图像
- ✏️ **图像编辑**：支持对上传的图片进行AI辅助编辑
- 🔑 **多API密钥管理**：支持添加、移除和切换多个Gemini API密钥
- 📝 **自定义系统提示词**：可以设置、修改和管理系统提示词

## 🚀 安装方法

### 方法一（Railway一键部署）

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/ya_ZL5?referralCode=HPHyYT)

### 方法二（Docker部署）

1. 克隆项目
   ```bash
   git clone https://github.com/laoguodong/Gemini-Telegram-Bot.git
   ```

2. 进入项目目录
   ```bash
   cd Gemini-Telegram-Bot
   ```

3. 构建Docker镜像
   ```bash
   docker build -t gemini_tg_bot .
   ```

4. 运行容器
   ```bash
   docker run -d --restart=always -e TELEGRAM_BOT_API_KEY={Telegram机器人API} -e GEMINI_API_KEYS={Gemini API密钥} gemini_tg_bot
   ```

### 方法三（Linux系统安装）

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 在[BotFather](https://t.me/BotFather)获取Telegram Bot API密钥

3. 在[Google AI Studio](https://makersuite.google.com/app/apikey)获取Gemini API密钥

4. 运行机器人
   ```bash
   python main.py ${Telegram机器人API} ${Gemini API密钥}
   ```

## 📖 使用指南

### 基本命令

- `/start` - 开始使用机器人
- `/gemini` - 使用Gemini模型
- `/gemini_pro` - 使用Gemini Pro模型
- `/draw` - AI绘图功能
- `/edit` - 图片编辑功能
- `/clear` - 清除当前对话历史
- `/switch` - 切换默认使用的模型
- `/lang` - 切换语言（中/英）
- `/language` - 显示当前语言设置

### 系统提示词管理

- `/system` - 设置系统提示词
- `/system_clear` - 删除系统提示词
- `/system_reset` - 重置系统提示词为默认
- `/system_show` - 显示当前系统提示词

### API密钥管理

- `/api_add` - 添加新的API密钥
- `/api_remove` - 删除现有API密钥
- `/api_list` - 查看所有API密钥列表
- `/api_switch` - 切换当前使用的API密钥

### 使用场景

1. **私聊模式**：直接发送文字或图片进行对话
2. **群组模式**：使用 `/gemini` 或 `/gemini_pro` 命令加问题进行对话
3. **图像处理**：
   - 发送图片让AI识别内容
   - 使用 `/edit` + 图片 + 描述进行图像编辑
   - 使用 `/draw` + 描述生成AI图像

## 📋 注意事项

- 部分功能（如API密钥管理）仅在私聊模式下可用
- 确保API密钥格式正确以保证功能正常使用
- 系统提示词会影响AI的回复风格，可根据需要定制

## ⭐ Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=laoguodong/Gemini-Telegram-Bot&type=Date)](https://star-history.com/#laoguodong/Gemini-Telegram-Bot&Date)
