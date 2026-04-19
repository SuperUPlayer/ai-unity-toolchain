"""GitHub Actions CI 中运行的审查脚本"""
import argparse
import subprocess
import os
import sys

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", default="review_result.md")
    args = parser.parse_args()

    diff = subprocess.run(
        ["git", "diff", args.base, "HEAD", "--", "*.cs"],
        capture_output=True, text=True
    ).stdout

    if not diff.strip():
        with open(args.output, "w") as f:
            f.write("✅ 没有 C# 文件变更\n")
        return

    from agents.code_review import CodeReviewAgent
    agent = CodeReviewAgent()
    result = agent.review_diff(diff)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ 审查完成 → {args.output}")


if __name__ == "__main__":
    main()