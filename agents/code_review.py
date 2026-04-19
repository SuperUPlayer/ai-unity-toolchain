"""
代码审查 Agent

用法：
    agent = CodeReviewAgent()
    result = agent.review_file("path/to/YourScript.cs")
    result = agent.review_diff(git_diff_text)
"""

import os
import glob
import subprocess
from agents.base import BaseAgent


class CodeReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(prompt_file="prompts/code_review.md")

    def review_file(self, file_path: str) -> str:
        """审查单个 C# 文件"""
        code = self._read_file_safe(file_path)
        if code.startswith("[错误]"):
            return code

        return self.llm.chat_with_context(
            system_prompt=self.system_prompt,
            context=f"文件路径：{file_path}\n\n```csharp\n{code}\n```",
            question="请审查这段 Unity C# 代码。",
        )

    def review_diff(self, diff_text: str = None) -> str:
        """审查 Git diff（变更的代码）"""
        if diff_text is None:
            # 自动获取最近一次提交的 diff
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "--", "*.cs"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            diff_text = result.stdout

        if not diff_text.strip():
            return "没有 C# 文件变更。"

        # diff 太长时按文件拆分，分批审查
        if len(diff_text) > 12000:
            return self._review_large_diff(diff_text)

        return self.llm.chat_with_context(
            system_prompt=self.system_prompt,
            context=f"Git Diff:\n```diff\n{diff_text}\n```",
            question="请审查这个 Git 变更中的所有 C# 代码修改。",
        )

    def review_directory(self, directory: str) -> dict:
        """批量审查目录下的所有 C# 文件"""
        cs_files = glob.glob(os.path.join(directory, "**/*.cs"), recursive=True)
        if not cs_files:
            return {"_error": f"目录 {directory} 下没有找到 .cs 文件"}

        results = {}
        for i, f in enumerate(cs_files, 1):
            print(f"  [{i}/{len(cs_files)}] 审查中: {os.path.basename(f)}")
            results[f] = self.review_file(f)
        return results

    def _review_large_diff(self, diff_text: str) -> str:
        """大 diff 拆分审查"""
        chunks = []
        current = []
        for line in diff_text.split("\n"):
            if line.startswith("diff --git") and current:
                chunks.append("\n".join(current))
                current = []
            current.append(line)
        if current:
            chunks.append("\n".join(current))

        results = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  [{i}/{len(chunks)}] 审查 diff 片段...")
            r = self.llm.chat_with_context(
                system_prompt=self.system_prompt,
                context=f"Git Diff 片段:\n```diff\n{chunk}\n```",
                question="请审查这个变更。",
            )
            results.append(r)

        return "\n\n---\n\n".join(results)


# ===== 快速测试 =====
if __name__ == "__main__":
    agent = CodeReviewAgent()

    # 创建一个有问题的测试文件
    test_code = '''using UnityEngine;
using System.Linq;

public class BadExample : MonoBehaviour
{
    public float speed = 5f;

    void Update()
    {
        var rb = GetComponent<Rigidbody>();
        var target = GameObject.Find("Enemy");
        string info = "Pos: " + transform.position.ToString();
        Debug.Log(info);

        var items = FindObjectsOfType<Transform>()
            .Where(t => t.name.Contains("Item"))
            .ToList();
    }
}
'''
    os.makedirs("generated", exist_ok=True)
    with open("generated/BadExample.cs", "w") as f:
        f.write(test_code)

    print("=" * 60)
    print("🔍 代码审查测试")
    print("=" * 60)
    print(agent.review_file("generated/BadExample.cs"))