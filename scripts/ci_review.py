import sys
import os
import argparse
import subprocess

# 添加项目根目录到 Python 路径（让导入 agents 等模块生效）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="基准分支（例如 origin/master）")
    parser.add_argument("--output", default="review_result.md", help="输出文件路径")
    args = parser.parse_args()

    # 获取变更的 C# 文件 diff
    diff = subprocess.run(
        ["git", "diff", args.base, "HEAD", "--", "*.cs"],
        capture_output=True, text=True, timeout=30
    ).stdout

    if not diff.strip():
        with open(args.output, "w") as f:
            f.write("✅ 没有 C# 文件变更。")
        print("No C# files changed, exiting.")
        return

    # 导入代码审查 Agent（必须在添加路径之后）
    try:
        from agents.code_review import CodeReviewAgent
    except ImportError as e:
        error_msg = f"❌ 无法导入 CodeReviewAgent: {e}\n请确保 agents 目录存在且包含 code_review.py。"
        print(error_msg)
        with open(args.output, "w") as f:
            f.write(error_msg)
        sys.exit(1)

    agent = CodeReviewAgent()
    result = agent.review_diff(diff)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ 审查完成 → {args.output}")

if __name__ == "__main__":
    main()