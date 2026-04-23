# ancient-voices

古人之声 - 历史人物沉浸式对话系统

一个开源的 AI 对话系统，让用户通过沉浸式对话深入理解历史人物，感受古人的内心世界。

## 功能特性

- **历史场景库**：包含鸿门宴经典历史场景
- **智能体角色**：每个历史人物都有独特的性格、目标和说话风格
- **多种对话模式**：深度访谈、冲突模拟、幕后军师
- **反思报告**：AI 生成对话分析，帮助理解人物决策逻辑

## 技术栈

- **后端**: FastAPI + PostgreSQL + SQLAlchemy
- **前端**: 纯 HTML/CSS/JS（无框架依赖）
- **AI**: 支持多 LLM 提供商配置（通过数据库管理）

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone git@github.com:aiyaxcom/ancient-voices.git
cd ancient-voices

# 安装依赖
pip install -r backend/requirements.txt
```

### 2. 配置数据库

创建 PostgreSQL 数据库：

```sql
CREATE DATABASE ancient_voices;
```

### 3. 配置环境变量

创建 `backend/.env` 文件：

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ancient_voices
APP_SECRET=your-secret-key
```

### 4. 初始化数据库

```bash
cd backend
python scripts/init_db.py
```

### 5. 配置 LLM 提供商

在数据库中添加 LLM 提供商配置：

```sql
INSERT INTO llm_providers (provider_key, display_name, api_url, api_key, default_model, is_enabled, priority)
VALUES ('your_provider', 'Your LLM', 'https://api.example.com', 'your-api-key', 'model-name', true, 1);
```

### 6. 启动服务

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 7. 访问前端

直接在浏览器打开 `frontend/index.html`，或配置 nginx 静态文件服务。

## 项目结构

```
ancient-voices/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── api/
│   │   │   └── wenyan.py     # 对话 API
│   │   ├── core/
│   │   │   ├── config.py     # 配置管理
│   │   │   ├── database.py   # 数据库连接
│   │   │   └── timezone.py   # 时区工具
│   │   ├── models/
│   │   │   ├── wenyan.py     # 对话模型
│   │   │   └── llm_provider.py # LLM 配置模型
│   │   └── schemas/
│   │   │   └── wenyan.py     # 对话 Schema
│   ├── scripts/
│   │   └── init_db.py        # 数据库初始化
│   ├── init-scenarios.sql    # 预设场景数据
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html            # 首页（场景列表）
│   ├── scenario.html         # 场景详情
│   ├── create.html           # 创建场景
│   ├── sessions.html         # 对话历史
│   ├── chat.html             # 对话页面
│   └── api/
│   │   └── client.js         # API 客户端
├── README.md
└── LICENSE
```

## 预设场景

项目包含经典历史场景：

- **鸿门宴**（秦末汉初，公元前206年）- 包含项羽、刘邦、范增、张良等角色

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

## 许可证

MIT License