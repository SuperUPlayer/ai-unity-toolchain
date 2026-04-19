#!/usr/bin/env python3
"""
AI Unity 工具链 — 命令行入口

用法：
    python main.py review <文件或目录>
    python main.py review-diff
    python main.py gen <需求描述> [-p 项目路径] [-o 输出目录]
    python main.py config <需求描述> [-c 已有配置目录] [-o 输出文件]
    python main.py test <C#文件> [-o 输出目录]
"""

import argparse
import json
import os
import subprocess
import sys


def cmd_review(args):
    """代码审查"""
    from agents.code_review import CodeReviewAgent
    agent = CodeReviewAgent()

    if os.path.isfile(args.path):
        print(f"🔍 审查文件: {args.path}\n")
        print(agent.review_file(args.path))
    elif os.path.isdir(args.path):
        print(f"🔍 审查目录: {args.path}\n")
        results = agent.review_directory(args.path)
        for f, r in results.items():
            print(f"\n{'=' * 60}")
            print(f"📄 {f}")
            print('=' * 60)
            print(r)
    else:
        print(f"❌ 路径不存在: {args.path}")
        sys.exit(1)


def cmd_review_diff(args):
    """审查 Git 变更"""
    from agents.code_review import CodeReviewAgent

    diff = subprocess.run(
        ["git", "diff", "HEAD~1", "--", "*.cs"],
        capture_output=True, text=True
    ).stdout

    if not diff.strip():
        print("没有 C# 文件变更。")
        return

    agent = CodeReviewAgent()
    print("🔍 审查 Git 变更...\n")
    print(agent.review_diff(diff))


def cmd_gen(args):
    """代码生成"""
    from agents.code_gen import CodeGenAgent
    agent = CodeGenAgent(project_path=args.project)

    print(f"🔨 生成代码: {args.requirement}\n")
    files = agent.generate(args.requirement)
    saved = agent.save(files, args.output)
    print(f"\n✅ 共生成 {len(saved)} 个文件 → {args.output}")


def cmd_config(args):
    """配置生成"""
    from agents.config_gen import ConfigGenAgent
    agent = ConfigGenAgent(config_dir=args.config_dir)

    print(f"📋 生成配置: {args.requirement}\n")
    config = agent.generate(args.requirement)
    errors = agent.validate(config)

    if errors:
        print("⚠️ 校验警告:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("✅ 校验通过")

    print(json.dumps(config, ensure_ascii=False, indent=2))

    if args.output:
        agent.save(config, args.output)


def cmd_test(args):
    """测试生成"""
    from agents.test_gen import TestGenAgent
    agent = TestGenAgent()

    print(f"🧪 为 {args.file} 生成测试...\n")
    files = agent.generate(args.file)
    agent.save(files, args.output)
    print(f"\n✅ 共生成 {len(files)} 个测试文件")


def main():
    parser = argparse.ArgumentParser(
        description="AI Unity 工具链",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py review Assets/Scripts/Player/
  python main.py review-diff
  python main.py gen "创建对象池系统" -p Assets/Scripts -o generated/
  python main.py config "新英雄：火焰法师" -c Configs/Heroes/ -o generated/fire_mage.json
  python main.py test Assets/Scripts/Combat/DamageSystem.cs
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # review
    p_review = sub.add_parser("review", help="审查代码文件或目录")
    p_review.add_argument("path", help="C# 文件或目录路径")

    # review-diff
    sub.add_parser("review-diff", help="审查最近一次 Git 提交的变更")

    # gen
    p_gen = sub.add_parser("gen", help="根据描述生成代码")
    p_gen.add_argument("requirement", help="自然语言需求描述")
    p_gen.add_argument("-p", "--project", default=None, help="Unity 项目 Scripts 路径")
    p_gen.add_argument("-o", "--output", default="generated/", help="输出目录")

    # config
    p_config = sub.add_parser("config", help="生成游戏配置 JSON")
    p_config.add_argument("requirement", help="配置需求描述")
    p_config.add_argument("-c", "--config-dir", default=None, help="已有配置目录")
    p_config.add_argument("-o", "--output", default=None, help="输出文件路径")

    # test
    p_test = sub.add_parser("test", help="为 C# 文件生成单元测试")
    p_test.add_argument("file", help="待测试的 C# 文件")
    p_test.add_argument("-o", "--output", default="generated/", help="输出目录")

    args = parser.parse_args()

    commands = {
        "review": cmd_review,
        "review-diff": cmd_review_diff,
        "gen": cmd_gen,
        "config": cmd_config,
        "test": cmd_test,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()