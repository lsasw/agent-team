"""
ReAct Agent 核心 — LLM 驱动的「思考 → 行动 → 观察」循环。

这是一个纯手工实现的 Agent，不依赖任何 Agent 框架。
核心流程：
  1. 将任务 + 工具列表发给 LLM
  2. LLM 返回 Thought + Action（或 Final Answer）
  3. 如果是 Action → 执行工具 → 将 Observation 喂回 LLM → 回到步骤 2
  4. 如果是 Final Answer → 结束循环，返回结果
"""

import json
import re
from openai import OpenAI
from tools import ToolRegistry


class Agent:
    """一个 ReAct Agent。

    每个 Agent 有自己的角色（name/system_prompt）、工具集、和 LLM 客户端。
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: ToolRegistry,
        client: OpenAI,
        model: str,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.client = client
        self.model = model

    # ── 构建 prompt ────────────────────────────────────

    def _build_system_message(self) -> str:
        tool_desc = self.tools.describe() if self.tools else "（无可用工具）"
        return f"""{self.system_prompt}

## 工作方式

你是一个 AI Agent，使用 ReAct 模式完成任务。

### 可用工具
{tool_desc}

### 响应格式

当需要获取信息或执行操作时，严格按以下格式响应：

Thought: <你的推理过程，分析当前状态并决定下一步做什么>
Action: <工具名称>
Action Input: <JSON 格式的参数>

我会立即执行该工具并把结果返回给你。

当任务完成时，使用以下格式给出最终答案：

Thought: 任务已完成。
Final Answer: <你的最终答案，详细、完整地总结你的工作成果>

### 重要规则
1. 每次只能调用一个工具。
2. 工具执行后你会立即看到结果，然后决定下一步。
3. 先读后写：修改文件前先用 read_file 查看当前内容。
4. 代码写入时确保完整可运行。
5. 遇到错误不要放弃，分析原因并尝试修复。
"""

    # ── 解析 LLM 响应 ──────────────────────────────────

    def _extract_json(self, text: str) -> dict:
        """从文本中提取 JSON 对象，正确处理嵌套大括号"""
        start = text.find("{")
        if start == -1:
            return {}
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        return {}
        return {}

    def _parse_response(self, text: str) -> dict:
        """解析 LLM 响应，提取 Thought / Action / Final Answer"""
        # 检查是否包含 Final Answer（也可能用中文「最终答案」）
        final_match = re.search(
            r"(?:Final Answer|最终答案)[:：]\s*(.*)", text, re.DOTALL | re.IGNORECASE
        )
        if final_match:
            return {
                "type": "final",
                "thought": self._extract_thought(text),
                "answer": final_match.group(1).strip(),
            }

        # 检查是否包含 Action
        action_match = re.search(r"Action[:：]\s*(\S+)", text, re.IGNORECASE)
        if action_match:
            action_name = action_match.group(1).strip()
            params = {}
            if input_match := re.search(
                r"Action Input[:：]\s*", text, re.IGNORECASE
            ):
                params = self._extract_json(text[input_match.end() :])
            return {
                "type": "action",
                "thought": self._extract_thought(text),
                "action": action_name,
                "params": params,
            }

        # 无法解析 — 可能是纯文本/思考
        return {"type": "text", "content": text}

    def _extract_thought(self, text: str) -> str:
        m = re.search(
            r"(?:Thought|思考)[:：]\s*(.*?)(?:\n(?:Action|Final Answer|最终答案)|$)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        return m.group(1).strip() if m else ""

    # ── ReAct 主循环 ───────────────────────────────────

    def run(self, task: str, context: str = "", max_turns: int = 10) -> str:
        """
        运行 ReAct 循环。

        参数:
            task: 当前任务描述
            context: 附加上下文（如上一步的输出、测试反馈等）
            max_turns: 最大交互轮数

        返回:
            Agent 的最终答案
        """
        messages = [
            {"role": "system", "content": self._build_system_message()},
        ]

        user_msg = f"## 任务\n{task}"
        if context:
            user_msg += f"\n\n## 上下文 / 参考资料\n{context}"
        messages.append({"role": "user", "content": user_msg})

        print(f"\n{'='*60}")
        print(f"🤖 {self.name} 启动")
        print(f"{'='*60}")

        for turn in range(1, max_turns + 1):
            print(f"\n--- 第 {turn}/{max_turns} 轮 ---")

            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            text = response.choices[0].message.content
            print(f"📥 LLM 响应 ({len(text)} 字符):")

            parsed = self._parse_response(text)

            if parsed["type"] == "final":
                print(f"✅ 任务完成")
                print(f"   结果: {parsed['answer'][:500]}...")
                return parsed["answer"]

            if parsed["type"] == "action":
                action = parsed["action"]
                params = parsed["params"]
                print(f"🔧 调用工具: {action}({json.dumps(params, ensure_ascii=False)})")

                result = self.tools.execute(action, params)
                print(f"📤 工具结果: {result[:300]}...")

                # 将本轮对话追加到消息历史
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": f"Observation: {result}"})
                continue

            # 纯文本响应或无法解析 — 提示 LLM 按格式继续
            print(f"💬 纯文本: {text[:200]}...")
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": "请继续。如果需要使用工具，请按格式调用；如果任务已完成，请给出 Final Answer。"})

        print(f"\n⚠️ 达到最大轮数 {max_turns}，强制结束")
        return self._force_final_answer(messages)

    def _force_final_answer(self, messages: list) -> str:
        """达到 max_turns 时，强制 LLM 给出最终答案"""
        messages.append({
            "role": "user",
            "content": "已达到最大交互轮数。请基于现有信息，直接给出你的最终答案（Final Answer 格式）。"
        })
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception:
            return "（Agent 未能在限定的轮数内完成任务）"


# ── 快捷工厂函数 ────────────────────────────────────────

def make_agent(
    name: str,
    role: str,
    tools: ToolRegistry,
    client: OpenAI,
    model: str,
) -> Agent:
    """用角色描述快速创建 Agent"""
    prompt = f"你是 {name}，角色是: {role}。请根据你的专业领域完成任务。"
    return Agent(name=name, system_prompt=prompt, tools=tools, client=client, model=model)
