"""
工具系统 — Agent 可用的工具集。

每个工具包含：名称、描述、参数 schema、执行函数。
工具注册表负责管理所有工具，并生成 LLM 可理解的工具描述。
"""

import json
import os
from typing import Callable, Any

WORKSPACE = os.path.join(os.path.dirname(__file__), "workspace")


def ensure_workspace():
    os.makedirs(WORKSPACE, exist_ok=True)


class Tool:
    def __init__(self, name: str, description: str, parameters: dict, func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters  # JSON Schema
        self.func = func

    def execute(self, **kwargs) -> str:
        return self.func(**kwargs)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def execute(self, name: str, params: dict) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"错误: 工具 '{name}' 不存在。可用工具: {list(self._tools.keys())}"
        try:
            return tool.execute(**params)
        except Exception as e:
            return f"工具执行出错: {e}"

    def describe(self) -> str:
        """生成 LLM prompt 中的工具描述"""
        lines = []
        for tool in self._tools.values():
            params_desc = json.dumps(tool.parameters, ensure_ascii=False, indent=2)
            lines.append(f"### {tool.name}\n{tool.description}\n参数: {params_desc}\n")
        return "\n".join(lines)


# ── 内置工具 ──────────────────────────────────────────

def _read_file(path: str) -> str:
    """读取工作区中的文件"""
    ensure_workspace()
    full_path = os.path.join(WORKSPACE, path)
    # 安全检查：防止路径穿越
    if not os.path.realpath(full_path).startswith(os.path.realpath(WORKSPACE)):
        return "错误: 不允许访问工作区以外的路径"
    if not os.path.exists(full_path):
        return f"文件不存在: {path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def _write_file(path: str, content: str) -> str:
    """写入文件到工作区"""
    ensure_workspace()
    full_path = os.path.join(WORKSPACE, path)
    if not os.path.realpath(full_path).startswith(os.path.realpath(WORKSPACE)):
        return "错误: 不允许写入工作区以外的路径"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"文件已写入: {path} ({len(content)} 字符)"


def _list_files(path: str = "") -> str:
    """列出工作区中的文件"""
    ensure_workspace()
    target = os.path.join(WORKSPACE, path) if path else WORKSPACE
    if not os.path.exists(target):
        return f"路径不存在: {path}"
    if os.path.isfile(target):
        return _read_file(path)
    files = os.listdir(target)
    if not files:
        return "工作区为空"
    return "\n".join(f"  - {f}" for f in sorted(files))


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(Tool(
        name="read_file",
        description="读取工作区中的一个文件，返回文件内容。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要读取的文件路径（相对于工作区）"}
            },
            "required": ["path"]
        },
        func=_read_file
    ))

    registry.register(Tool(
        name="write_file",
        description="将内容写入工作区中的一个文件。如果文件已存在则覆盖。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要写入的文件路径"},
                "content": {"type": "string", "description": "要写入的文件内容"}
            },
            "required": ["path", "content"]
        },
        func=_write_file
    ))

    registry.register(Tool(
        name="list_files",
        description="列出工作区中的文件。如果指定了路径，则列出该路径下的文件。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "可选，子目录路径"}
            },
            "required": []
        },
        func=_list_files
    ))

    return registry
