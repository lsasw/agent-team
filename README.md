# 🤖 Agent Team

多智能体协作学习项目 — 从零手写 ReAct Agent、团队编排、RAG、FastAPI Web 应用。

## 项目结构

```
agent-team/
├── src/agent_team/
│   ├── core/                      # ReAct Agent 核心
│   │   ├── agent.py               #   ReAct 循环（Think → Act → Observe）
│   │   ├── team.py                #   团队编排（架构师 → 程序员 ⇄ 测试员）
│   │   └── tools.py               #   工具系统（read_file / write_file）
│   │
│   ├── rag/                       # RAG 检索增强生成
│   │   └── rag_demo.py            #   LangChain + ChromaDB + 本地 Embedding
│   │
│   ├── web/                       # FastAPI Web 应用
│   │   ├── main.py                #   应用入口
│   │   ├── config.py              #   配置管理
│   │   ├── database.py            #   SQLAlchemy 异步引擎
│   │   ├── models.py              #   User ORM 模型
│   │   ├── schemas.py             #   Pydantic 数据验证
│   │   ├── auth.py                #   bcrypt 密码哈希 + JWT 认证
│   │   ├── routers/auth.py        #   注册 / 登录 / 登出路由
│   │   ├── templates/             #   Jinja2 页面模板
│   │   └── static/                #   静态资源 (CSS)
│   │
│   └── cli.py                     # 多 Agent 协作 CLI Demo
│
├── docs/                          # 设计文档
├── tests/                         # 测试目录
├── pyproject.toml                 # uv 项目配置
└── .env.example                   # 环境变量模板
```

## 功能模块

### 1. ReAct Agent 核心 (`core/`)

纯手工实现，不依赖任何 Agent 框架：

- **ReAct 循环**: Think → Action → Observation → 循环
- **工具系统**: 文件读写、工具注册、JSON Schema 描述生成
- **团队编排**: 架构师设计 → 程序员编码 → 测试员审查，带反馈循环
- **收敛控制**: max_iterations + 停滞检测

### 2. RAG 检索增强生成 (`rag/`)

基于 LangChain + ChromaDB 的本地向量检索：

- **文档加载**: Markdown + Python 源码
- **文本分块**: RecursiveCharacterTextSplitter
- **向量化**: 本地 BAAI/bge-small-zh-v1.5（免费、离线）
- **向量存储**: ChromaDB 持久化
- **生成**: DeepSeek LLM

### 3. Web 应用 (`web/`)

FastAPI 全栈 Web 应用，用户登录注册：

| 技术 | 用途 |
|------|------|
| FastAPI + Uvicorn | 异步 Web 框架 |
| Jinja2 | 服务端模板渲染 |
| SQLAlchemy 2.0 (async) | ORM |
| SQLite + aiosqlite | 数据库 |
| bcrypt | 密码哈希 |
| JWT (python-jose) | Token 认证 |
| Pydantic | 数据验证 |
| httpOnly Cookie | 防 XSS/CSRF |

## 快速开始

### 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
# 1. 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/lsasw/agent-team.git
cd agent-team

# 3. 安装依赖
uv sync

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### 启动 Web 应用

```bash
uv run uvicorn agent_team.web.main:app --reload
```

浏览器打开 http://127.0.0.1:8000

### 运行 Agent CLI Demo

```bash
uv run python -m agent_team.cli
```

### 运行 RAG 问答

```bash
# 交互模式
uv run python -m agent_team.rag.rag_demo

# 单次查询
uv run python -m agent_team.rag.rag_demo -q "ReAct 模式的核心循环是什么？"

# 查看检索结果
uv run python -m agent_team.rag.rag_demo -s "斐波那契"
```

## 技术栈总览

```
LLM:        DeepSeek API (OpenAI 兼容)
Agent:      自研 ReAct 循环
RAG:        LangChain + ChromaDB + sentence-transformers
Web:        FastAPI + Jinja2 + SQLAlchemy 2.0
数据库:     SQLite (可替换为 PostgreSQL)
包管理:     uv
```
