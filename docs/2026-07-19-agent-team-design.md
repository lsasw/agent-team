# 多智能体协作 Demo — 设计文档

## 目标

从零手写一个多 Agent 协作系统，用于理解 Agent 的 ReAct 循环、工具调用、以及多 Agent 间的反馈循环机制。

## 架构

```
agent.py     — ReAct 核心循环（think → act → observe → 循环）
tools.py     — 工具系统（read_file / write_file）
team.py      — 团队编排（架构师 → 程序员 ⇄ 测试员，带反馈循环）
main.py      — 入口，组装并运行
```

## 核心技术点

### 1. ReAct 循环 (agent.py)
- LLM 接收 system prompt + 任务 + 可用工具描述
- 解析响应：区分纯文本和工具调用（JSON 格式）
- 执行工具，结果喂回 LLM，继续循环
- `max_turns` 防止无限循环

### 2. 工具系统 (tools.py)
- 工具注册：name + description + parameters schema
- 文件工具：read_file / write_file
- 工具描述生成：自动生成 LLM 可理解的 tool spec

### 3. 团队编排 (team.py)
- 架构师 Agent → 产出设计文档
- 程序员 Agent → 根据设计写代码
- 测试员 Agent → 审查代码，输出通过/问题列表
- **反馈循环**：测试不通过 → 问题描述 + 代码 → 回到程序员 → 重新修改 → 再测试
- 收敛控制：max_iterations，改进衰减检测

### 4. LLM 后端
- DeepSeek API（OpenAI 兼容接口）
- 使用 openai Python SDK

## Demo 场景

让 Agent 团队协作实现：用 Python 写一个斐波那契数列计算函数，包含错误处理。

## 文件结构

```
agent-team/
├── docs/
│   └── 2026-07-19-agent-team-design.md
├── agent.py          # ReAct 核心
├── tools.py          # 工具系统
├── team.py           # 团队编排
├── main.py           # 入口
├── requirements.txt  # openai + python-dotenv
└── .env              # DEEPSEEK_API_KEY
```
