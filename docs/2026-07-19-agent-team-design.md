# 多智能体协作 Demo — 设计文档

> 最后更新: 2026-07-20

## 目标

从零手写一个多 Agent 协作系统，逐步扩展为集 Agent、RAG、Web 于一体的学习项目。

## 版本演进

### v0.1 — ReAct Agent 核心

从零手写 ReAct Agent，理解「思考 → 行动 → 观察」循环机制。

**模块:**
- `agent.py` — ReAct 循环（Think → Act → Observe）
- `tools.py` — 工具系统（read_file / write_file / list_files）
- `team.py` — 团队编排（架构师 → 程序员 ⇄ 测试员，带反馈循环）
- `main.py` → 现更名为 `cli.py`

### v0.2 — RAG 检索增强生成

集成 LangChain + ChromaDB，实现本地文档检索问答。

- `rag_demo.py` — LangChain LCEL 链式调用
- 本地 Embedding 模型: BAAI/bge-small-zh-v1.5（免费、离线）
- 向量库: ChromaDB（持久化到磁盘）

### v0.3 — FastAPI Web 应用 + 用户系统

标准化项目结构（`src/` 布局），加入 Python 主流 Web 技术栈。

- FastAPI 异步 Web 框架
- SQLAlchemy 2.0 异步 ORM + SQLite
- bcrypt 密码哈希 + JWT 认证
- Jinja2 服务端渲染
- httpOnly Cookie 安全策略

## 架构

```
src/agent_team/
├── core/          # v0.1 — ReAct Agent 核心
├── rag/           # v0.2 — RAG 检索增强
├── web/           # v0.3 — Web 应用
└── cli.py         # CLI 入口
```

## 核心技术点

### 1. ReAct 循环 (core/agent.py)

- LLM 接收 system prompt + 任务 + 可用工具描述
- 正则解析响应：区分 Thought / Action / Final Answer
- 执行工具，Observation 喂回 LLM，继续循环
- `max_turns` 防止无限循环，强制结束兜底

### 2. 工具系统 (core/tools.py)

- 工具注册：name + description + parameters schema
- 文件工具：read_file / write_file / list_files
- 路径穿越安全检查（os.path.realpath）
- JSON Schema 自动生成供 LLM 理解

### 3. 团队编排 (core/team.py)

- 架构师 Agent → 产出设计文档
- 程序员 Agent → 根据设计写代码
- 测试员 Agent → 审查代码，输出通过/问题列表
- **反馈循环**: 测试不通过 → 问题反馈 → 程序员修改 → 再测试
- **收敛控制**: max_iterations + 停滞检测（连续两轮问题相同则停止）

### 4. RAG (rag/rag_demo.py)

- 文档加载: DirectoryLoader + TextLoader
- 文本分块: RecursiveCharacterTextSplitter (500 字/块, 100 字重叠)
- 向量化: HuggingFaceEmbeddings (BAAI/bge-small-zh-v1.5, 384 维)
- 向量存储: ChromaDB (HNSW 图索引, 磁盘持久化)
- 检索链: LCEL 管道式组装 (`retriever | format_docs → prompt → llm → parser`)

### 5. Web 应用 (web/)

- **安全**: bcrypt 密码哈希, JWT 认证, httpOnly Cookie
- **ORM**: SQLAlchemy 2.0 Mapped 风格, 异步引擎, 声明式基类
- **验证**: Pydantic Schema + HTML5 Form 双重校验
- **模板**: Jinja2 模板继承 (base → login/register/dashboard)
- **数据库**: 启动时自动建表, 依赖注入管理会话生命周期

### 6. LLM 后端

- DeepSeek API（OpenAI 兼容接口）
- 使用 openai Python SDK
- Embedding 阶段使用本地模型（无需 API Key）

## Demo 场景

### Agent 协作: 斐波那契数列

让 Agent 团队协作实现 Python 版斐波那契数列函数，包含：
- 递归和迭代两种计算方式
- 参数校验（负数 ValueError, 非整数 TypeError）
- `if __name__ == "__main__"` 测试入口

### RAG 问答: 项目文档检索

基于项目设计文档和源码回答技术问题。

### Web 应用: 用户注册登录

完整的注册 → 登录 → 仪表盘 → 登出流程。

## 项目结构（当前）

```
agent-team/
├── src/agent_team/
│   ├── core/                      # v0.1 — ReAct Agent
│   ├── rag/                       # v0.2 — RAG
│   ├── web/                       # v0.3 — Web 应用
│   │   ├── main.py                #   FastAPI 入口
│   │   ├── config.py              #   配置
│   │   ├── database.py            #   DB 引擎
│   │   ├── models.py              #   ORM 模型
│   │   ├── schemas.py             #   Pydantic Schema
│   │   ├── auth.py                #   认证（bcrypt + JWT）
│   │   ├── routers/auth.py        #   路由
│   │   ├── templates/             #   模板
│   │   └── static/                #   静态资源
│   └── cli.py                     # CLI 入口
├── docs/
│   └── 2026-07-19-agent-team-design.md
├── tests/
├── README.md
├── pyproject.toml
└── .env.example
```
