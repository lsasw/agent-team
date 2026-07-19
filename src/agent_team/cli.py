"""
多智能体协作 Demo — 入口

用法:
  1. 复制 .env.example 为 .env，填入 DeepSeek API Key
  2. pip install -r requirements.txt
  3. python main.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from agent_team.core.team import TeamOrchestrator

# 项目根目录 (src/agent_team/cli.py → 向上 3 级)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        print("❌ 请先设置 DEEPSEEK_API_KEY 环境变量")
        print("   复制 .env.example 为 .env 并填入你的 API Key")
        return

    client = OpenAI(api_key=api_key, base_url=base_url)

    # ── Demo 任务 ──
    requirement = """
用 Python 实现一个斐波那契数列计算工具，要求：

1. 实现函数 fib(n: int) -> int，返回第 n 个斐波那契数（F(0)=0, F(1)=1）
2. 处理非法输入：n 为负数时抛出 ValueError，n 不是整数时抛出 TypeError
3. 支持两种计算方式：递归和迭代，通过参数 method 选择（默认迭代）
4. 包含 if __name__ == "__main__" 测试入口，打印 F(0) 到 F(10) 的测试结果
5. 代码写入 workspace/fib.py
"""

    print("=" * 60)
    print("🚀 多智能体软件开发团队启动")
    print(f"   LLM: {model}")
    print(f"   需求: {requirement.strip()[:100]}...")
    print("=" * 60)

    team = TeamOrchestrator(
        client=client,
        model=model,
        max_iterations=3,
        verbose=True,
    )

    result = team.run(requirement)
    # TeamOrchestrator.run(team, requirement)  # 输出结果

    # ── 输出结果 ──
    print("\n\n" + "=" * 60)
    print("📋 最终结果")
    print("=" * 60)

    print(f"\n{'─'*40}")
    print("🏗️ 架构设计")
    print(f"{'─'*40}")
    print(result["design"][:1500])

    for i, it in enumerate(result["iterations"], 1):
        print(f"\n{'─'*40}")
        print(f"🔄 迭代 {i} — {'✅ 通过' if it['passed'] else '❌ 不通过'}")
        print(f"{'─'*40}")
        print(f"\n📝 程序员输出:\n{it['code'][:800]}")
        print(f"\n🔍 测试员审查:\n{it['review'][:800]}")

    # 保存完整结果
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n📁 完整结果已保存到 output/result.json")

    # 检查实际代码文件
    workspace = PROJECT_ROOT / "workspace"
    if workspace.exists():
        print(f"\n📁 工作区文件:")
        for root, dirs, files in os.walk(workspace):
            for file in files:
                filepath = os.path.join(root, file)
                print(f"   {filepath}")
                with open(filepath, "r") as f:
                    print(f"   {'─'*40}")
                    print(f.read())


if __name__ == "__main__":
    main()
