"""
团队编排器 — 管理多个 Agent 的协作流程，包含反馈循环。

流程:
  架构师 → 程序员 ⇄ 测试员（反馈循环直到通过或达到上限）
"""

from openai import OpenAI
from agent_team.core.agent import Agent
from agent_team.core.tools import ToolRegistry, create_default_registry


class TeamOrchestrator:
    """编排一个软件开发的 Agent 团队。

    架构师 → 设计
    程序员 → 编码
    测试员 → 审查
    如果有问题 → 反馈给程序员 → 重新编码 → 再审查
    """

    def __init__(
        self,
        client: OpenAI,
        model: str,
        max_iterations: int = 3,
        verbose: bool = True,
    ):
        self.client = client
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose

        # ── 初始化工具 ──
        self.architect_tools = ToolRegistry()  # 架构师不需要工具
        self.programmer_tools = create_default_registry()  # 程序员可以读写文件
        self.tester_tools = create_default_registry()  # 测试员可以读取文件

        # ── 初始化 Agent ──
        self.architect = Agent(
            name="架构师",
            system_prompt="""你是一位资深软件架构师。你的职责是：
1. 分析用户需求，拆解为可实现的模块
2. 设计代码结构：函数签名、类结构、模块划分
3. 考虑边界情况、错误处理、性能要求
4. 输出清晰、详细的技术设计方案

你的设计文档应该包含：
- 整体结构说明
- 每个函数/类的签名和职责
- 输入输出格式
- 错误处理策略
- 测试要点

不要写实现代码，只输出设计方案。""",
            tools=self.architect_tools,
            client=client,
            model=model,
        )

        self.programmer = Agent(
            name="程序员",
            system_prompt="""你是一位严谨的程序员。你的职责是：
1. 根据架构设计文档编写完整、可运行的 Python 代码
2. 处理所有边界情况和错误
3. 代码必须有清晰的注释
4. 使用 write_file 工具将代码写入工作区

编码规范：
- 使用类型注解
- 函数要有 docstring
- 包含 if __name__ == "__main__" 测试入口
- 确保代码可以直接运行""",
            tools=self.programmer_tools,
            client=client,
            model=model,
        )

        self.tester = Agent(
            name="测试员",
            system_prompt="""你是一位严格的测试工程师。你的职责是：
1. 仔细阅读代码，检查逻辑是否正确
2. 验证是否满足设计文档的所有要求
3. 检查边界情况是否处理
4. 检查错误处理是否完善
5. 检查代码风格和可读性

审查维度：
- 功能完整性：是否实现了所有需求？
- 正确性：逻辑是否正确？有无 bug？
- 健壮性：边界情况和异常处理是否完善？
- 可读性：命名是否清晰？注释是否到位？

最终给出明确的结论：✅ 通过 或 ❌ 不通过。
如果不通过，必须列出具体问题，并给出修改建议。
如果通过，简要说明审查结果。""",
            tools=self.tester_tools,
            client=client,
            model=model,
        )

    def run(self, requirement: str) -> dict:
        """
        运行完整的团队协作流程。

        返回:
            {
                "requirement": str,
                "design": str,
                "iterations": [{"code": str, "review": str, "passed": bool}, ...],
                "final_code": str,
                "passed": bool,
            }
        """
        result = {
            "requirement": requirement,
            "design": "",
            "iterations": [],
            "final_code": "",
            "passed": False,
        }

        # ── 阶段 1: 架构师设计 ──
        if self.verbose:
            print(f"\n{'🏗️'*30}")
            print("阶段 1/3: 架构师设计")
            print(f"{'🏗️'*30}")

        design = self.architect.run(
            task=f"请为以下需求设计技术方案：\n\n{requirement}",
        )
        result["design"] = design
        if self.verbose:
            print(f"\n📋 设计完成: {design[:300]}...")

        # ── 阶段 2: 反馈循环：程序员 ⇄ 测试员 ──
        feedback = ""  # 初始无反馈

        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n{'🔄'*30}")
                print(f"阶段 2/3: 迭代 {iteration}/{self.max_iterations}")
                print(f"{'🔄'*30}")

            # 程序员写代码
            task = "请根据以下设计文档编写代码。将代码写入 workspace/ 目录。"
            context = f"## 设计文档\n{design}"
            if feedback:
                context += f"\n\n## ⚠️ 上一轮测试反馈（请务必修复这些问题）\n{feedback}"

            code = self.programmer.run(task=task, context=context)

            # 测试员审查
            review_task = f"请审查代码是否满足以下需求：\n\n{requirement}"
            review_context = f"## 设计文档\n{design}\n\n## 代码（已写入工作区，请用 read_file 查看）\n{code[:2000]}"

            review = self.tester.run(task=review_task, context=review_context)

            # 判断是否通过 — 检查明确的结论标识
            passed = self._is_passed(review)

            result["iterations"].append({
                "iteration": iteration,
                "code": code,
                "review": review,
                "passed": passed,
            })

            if self.verbose:
                status = "✅ 通过" if passed else "❌ 不通过"
                print(f"\n📊 迭代 {iteration} 结果: {status}")

            if passed:
                result["final_code"] = code
                result["passed"] = True
                break

            # 准备下一轮反馈
            feedback = f"测试员审查结果（第 {iteration} 轮）：\n{review}"

            # ── 检测改进幅度 ──
            if iteration > 1:
                prev_review = result["iterations"][-2]["review"]
                if self._detect_stagnation(prev_review, review):
                    if self.verbose:
                        print("\n⚠️ 检测到测试反馈停滞（连续两轮问题相同），停止迭代")
                    break

        if not result["passed"] and result["iterations"]:
            result["final_code"] = result["iterations"][-1]["code"]

        # ── 阶段 3: 总结 ──
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"📊 团队协作完成")
            print(f"   设计阶段: ✅")
            print(f"   编码测试: {len(result['iterations'])} 轮迭代")
            print(f"   最终结果: {'✅ 通过' if result['passed'] else '❌ 未通过'}")
            print(f"{'='*60}")

        return result

    def _is_passed(self, review: str) -> bool:
        """从测试员的审查报告中判断是否通过"""
        import re
        # 匹配明确的结论行: "✅ 通过" / "❌ 不通过" / "结论：通过" 等
        conclusion = re.search(
            r"(?:结论|结果|判定)[:：]\s*(.+)",
            review,
        )
        if conclusion:
            text = conclusion.group(1)
            if any(w in text for w in ["通过", "合格", "✅"]):
                return True
            if any(w in text for w in ["不通过", "不合格", "❌", "失败"]):
                return False

        # 兜底：整段文本中出现"不通过"优先判不通过
        if "不通过" in review or "❌" in review:
            return False
        if "通过" in review or "✅" in review:
            return True
        return False

    def _detect_stagnation(self, prev_review: str, curr_review: str, threshold: float = 0.6) -> bool:
        """简单检测两个审查结果是否高度相似（可能卡住了）"""
        # 提取问题行（以 - 或 * 开头的行）
        import re
        def extract_issues(text: str) -> set:
            lines = re.findall(r"^[\s]*[-*]\s*(.+)", text, re.MULTILINE)
            return set(line.strip().lower() for line in lines)

        prev = extract_issues(prev_review)
        curr = extract_issues(curr_review)

        if not prev or not curr:
            return False

        overlap = len(prev & curr) / len(prev | curr) if (prev | curr) else 0
        return overlap >= threshold
