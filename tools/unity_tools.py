"""
Agent 可用的工具集

每个工具是一个 @tool 装饰的函数。
AI 看到函数的 docstring 就知道这个工具干什么、怎么传参。
"""

import os
import glob
import subprocess
from langchain_core.tools import tool

# ==========================================
# 安全限制（防止 Agent 搞破坏）
# ==========================================

# 允许读取的目录前缀
ALLOWED_READ_DIRS = [
    os.path.normpath("Assets/"),
    os.path.normpath("Configs/"),
    os.path.normpath("Tests/"),
    os.path.normpath("Packages/"),
    os.path.normpath("ProjectSettings/"),
]

# 允许写入的目录前缀（比读取更严格）
ALLOWED_WRITE_DIRS = [
    os.path.normpath("Assets/Scripts/"),
    os.path.normpath("Assets/Tests/"),
    os.path.normpath("Configs/"),
    os.path.normpath("generated/"),
]

# 禁止写入的路径
PROTECTED_PATHS = [
    ".git/",
    "Assets/Plugins/",
    "Library/",
]


def _is_safe_read(path: str) -> bool:
    """检查路径是否允许读取"""
    norm = os.path.normpath(path)
    return any(norm.startswith(d) or os.path.basename(norm).endswith(".cs") for d in ALLOWED_READ_DIRS)


def _is_safe_write(path: str) -> bool:
    """检查路径是否允许写入"""
    norm = os.path.normpath(path)
    for p in PROTECTED_PATHS:
        if norm.startswith(p):
            return False
    return any(norm.startswith(d) for d in ALLOWED_WRITE_DIRS)


# ==========================================
# 工具 1: 读取文件
# ==========================================

@tool
def read_file(file_path: str) -> str:
    """读取指定路径的文件内容。用于查看 C# 代码、JSON 配置、文档等。

    Args:
        file_path: 文件的路径（相对于项目根目录）
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        if len(content) > 15000:
            content = content[:15000] + "\n\n... [文件过长，已截断到 15000 字符] ..."
        return content
    except FileNotFoundError:
        return f"❌ 文件不存在: {file_path}"
    except UnicodeDecodeError:
        return f"❌ 无法读取（编码问题）: {file_path}"


# ==========================================
# 工具 2: 写入文件（带安全检查和自动备份）
# ==========================================

@tool
def write_file(file_path: str, content: str) -> str:
    """将内容写入文件。自动创建不存在的目录。已有文件会自动备份为 .bak。

    只能写入以下目录: Assets/Scripts/, Assets/Tests/, Configs/, generated/

    Args:
        file_path: 要写入的文件路径
        content: 文件内容
    """
    if not _is_safe_write(file_path):
        return f"❌ 安全限制：不允许写入路径 {file_path}。允许的目录: {ALLOWED_WRITE_DIRS}"

    # 已有文件先备份
    if os.path.exists(file_path):
        import shutil
        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ 已写入: {file_path}（{len(content)} 字符）"


# ==========================================
# 工具 3: 列出目录结构
# ==========================================

@tool
def list_directory(directory: str, pattern: str = "*.cs") -> str:
    """列出目录下匹配模式的文件，用于了解项目结构。

    Args:
        directory: 目录路径
        pattern: 匹配模式，默认 *.cs。支持 *.json, *.yaml 等
    """
    try:
        files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
    except Exception as e:
        return f"❌ 目录访问失败: {e}"

    if not files:
        return f"目录 {directory} 下没有匹配 {pattern} 的文件"

    files.sort()
    if len(files) > 50:
        return "\n".join(files[:50]) + f"\n\n... 共 {len(files)} 个文件，只显示前 50 个"
    return "\n".join(files)


# ==========================================
# 工具 4: 搜索代码
# ==========================================

@tool
def search_code(directory: str, keyword: str) -> str:
    """在目录中搜索包含关键词的 C# 代码行。用于找到相关类、方法、接口。

    Args:
        directory: 搜索的目录路径
        keyword: 要搜索的关键词（不区分大小写）
    """
    results = []
    try:
        for cs_file in glob.glob(os.path.join(directory, "**/*.cs"), recursive=True):
            try:
                with open(cs_file, encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            results.append(f"{cs_file}:{i}  {line.rstrip()}")
            except Exception:
                continue
    except Exception as e:
        return f"❌ 搜索失败: {e}"

    if not results:
        return f"未找到包含 '{keyword}' 的代码"
    if len(results) > 30:
        return "\n".join(results[:30]) + f"\n\n... 共 {len(results)} 处匹配，只显示前 30 条"
    return "\n".join(results)


# ==========================================
# 工具 5: Git 操作
# ==========================================

@tool
def git_diff(base: str = "HEAD~1") -> str:
    """获取 Git 代码变更，查看最近修改了哪些 C# 代码。

    Args:
        base: 对比基准，默认 HEAD~1（与上一次提交对比）
    """
    try:
        result = subprocess.run(
            ["git", "diff", base, "--", "*.cs"],
            capture_output=True, text=True, timeout=10
        )
        if not result.stdout.strip():
            return "没有 C# 文件变更"
        output = result.stdout
        if len(output) > 8000:
            output = output[:8000] + "\n\n... [diff 过长，已截断] ..."
        return output
    except subprocess.TimeoutExpired:
        return "❌ Git 命令超时"
    except FileNotFoundError:
        return "❌ Git 未安装或不在 Git 仓库中"
    


# ==========================================
# 工具 6: 文件查找（按名称模糊搜索）
# ==========================================

@tool
def find_file(directory: str, filename_keyword: str) -> str:
    """按文件名关键词查找文件。比 list_directory 更精准。

    Args:
        directory: 搜索的根目录
        filename_keyword: 文件名中包含的关键词（不区分大小写）
    """
    matches = []
    try:
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和 Library
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'Library']
            for f in files:
                if filename_keyword.lower() in f.lower():
                    matches.append(os.path.join(root, f))
    except Exception as e:
        return f"❌ 搜索失败: {e}"

    if not matches:
        return f"未找到文件名包含 '{filename_keyword}' 的文件"
    matches.sort()
    return "\n".join(matches[:30])


# 汇总所有工具
ALL_TOOLS = [read_file, write_file, list_directory, search_code, git_diff, find_file]