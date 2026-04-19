"""Agent 基类，所有 Agent 继承这个"""

import os
from utils.llm import LLM


class BaseAgent:
    """所有 Agent 的基类"""

    def __init__(self, prompt_file: str = None):
        self.llm = LLM()
        self.system_prompt = ""
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, encoding="utf-8") as f:
                self.system_prompt = f.read()

    def _read_file_safe(self, file_path: str) -> str:
        """安全读取文件，处理编码和不存在的情况"""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"[错误] 文件不存在: {file_path}"
        except UnicodeDecodeError:
            try:
                with open(file_path, encoding="gbk") as f:
                    return f.read()
            except Exception:
                return f"[错误] 无法读取文件（编码问题）: {file_path}"