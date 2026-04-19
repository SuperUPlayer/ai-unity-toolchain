"""
代码生成 Agent

用法：
    agent = CodeGenAgent(project_path="/path/to/unity/Assets/Scripts")
    files = agent.generate("创建一个对象池系统，支持泛型和自动扩容")
    agent.save(files)
"""

import os
import re
import glob
from agents.base import BaseAgent


class CodeGenAgent(BaseAgent):
    def __init__(self, project_path: str = None):
        super().__init__(prompt_file="prompts/code_gen.md")
        self.project_path = project_path

    def generate(self, requirement: str, related_code: str = "") -> dict:
        """
        根据需求生成代码。
        
        Args:
            requirement: 自然语言需求描述
            related_code: 相关的已有代码（可选，作为风格参考）
        
        Returns:
            {"文件路径": "代码内容", ...}
        """
        context = ""
        if related_code:
            context += f"【项目中的相关代码（参考风格和接口）】\n{related_code}\n\n"
        elif self.project_path:
            found = self._find_related_code(requirement)
            if found:
                context += f"【项目中的相关代码（参考风格和接口）】\n{found}\n\n"

        response = self.llm.chat_with_context(
            system_prompt=self.system_prompt,
            context=context if context else "（没有已有代码参考，请按标准规范生成）",
            question=requirement,
        )

        return self._parse_response(response)

    def save(self, files: dict, output_dir: str = "generated/") -> list:
        """
        保存生成的文件到输出目录。
        
        不直接写到项目目录，而是写到 generated/，你确认后手动复制。
        
        Returns:
            保存的文件路径列表
        """
        saved = []
        for path, code in files.items():
            full_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
            saved.append(full_path)
            print(f"  ✅ 已保存: {full_path}")
        return saved

    def _find_related_code(self, requirement: str) -> str:
        """简单关键词搜索项目中相关的代码"""
        if not self.project_path or not os.path.isdir(self.project_path):
            return ""

        # 从需求中提取关键词（简单版：按空格和标点拆分）
        keywords = [w.lower() for w in re.split(r'[\s,，。、！？]+', requirement) if len(w) > 1]

        scored_files = []
        for cs_file in glob.glob(os.path.join(self.project_path, "**/*.cs"), recursive=True):
            try:
                with open(cs_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                name = os.path.basename(cs_file).lower()
                score = sum(1 for kw in keywords if kw in name or kw in content.lower())
                if score > 0:
                    scored_files.append((score, cs_file, content))
            except Exception:
                continue

        scored_files.sort(reverse=True, key=lambda x: x[0])

        # 取最相关的 2 个文件，每个最多 150 行
        result = ""
        for _, path, content in scored_files[:2]:
            lines = content.split("\n")[:150]
            result += f"\n// --- {path} ---\n" + "\n".join(lines) + "\n"

        return result

    def _parse_response(self, response: str) -> dict:
        """解析 AI 返回的代码，提取文件路径和内容"""
        files = {}

        # 尝试匹配 // === path === 格式
        parts = re.split(r'//\s*===\s*(.+?)\s*===', response)
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                file_path = parts[i].strip()
                code = parts[i + 1] if i + 1 < len(parts) else ""
                code_match = re.search(r'```csharp\n(.*?)```', code, re.DOTALL)
                if code_match:
                    code_content = code_match.group(1).strip()
                else:
                    code_content = code.strip()
                # 额外清理：移除可能残留的反引号
                code_content = code_content.rstrip('`').strip()
                files[file_path] = code_content
            return files

        # 没有路径标记，提取所有代码块
        code_blocks = re.findall(r'```csharp\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            for i, block in enumerate(code_blocks):
                block = block.strip().rstrip('`').strip()
                class_match = re.search(r'(?:public|internal)\s+(?:class|struct|interface)\s+(\w+)', block)
                name = class_match.group(1) if class_match else f"Generated_{i + 1}"
                files[f"{name}.cs"] = block
        else:
            # AI 没有用代码块包裹，整个响应当作代码
            files["GeneratedCode.cs"] = response.strip().rstrip('`').strip()

        return files


# ===== 快速测试 =====
if __name__ == "__main__":
    agent = CodeGenAgent()
    print("=" * 60)
    print("🔨 代码生成测试")
    print("=" * 60)
    files = agent.generate("创建一个简单的单例基类 Singleton<T>，继承 MonoBehaviour，支持 DontDestroyOnLoad")
    agent.save(files)
    for path, code in files.items():
        print(f"\n📄 {path}:")
        print(code[:500])