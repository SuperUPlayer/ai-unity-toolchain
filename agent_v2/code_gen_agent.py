"""
带自纠错能力的代码生成 Agent（增强版）

与第一部分 agents/code_gen.py 的区别：
- 第一部分：生成后交给你看
- 这里：生成 → 自审 → 自修 → 再审 → 通过后保存
"""

import re
from agent_v2.smart_agent import UnitySmartAgent


class CodeGenAgentV2(UnitySmartAgent):
    """能自我纠错的代码生成 Agent（增强版）"""

    def generate_with_self_review(self, requirement: str) -> str:
        """
        生成代码并自动审查修复。
        
        完整流程：
        1. 了解项目结构和代码风格
        2. 搜索相关已有代码
        3. 生成代码
        4. 自我审查（检查性能、规范、安全）
        5. 发现问题就修，修完再审
        6. 通过后保存文件
        """
        prompt = f"""请完成以下 Unity 代码生成任务。

## 需求
{requirement}

## 执行步骤（严格按顺序，不可跳过）

### 阶段一：调研
1. 用 list_directory 查看项目 Assets/Scripts/ 的目录结构
2. 用 search_code 搜索与需求相关的已有类/接口
3. 用 read_file 读取 1-2 个相关文件，学习项目的：
   - 命名规范（PascalCase? _camelCase?）
   - 基类/接口风格
   - 常用的设计模式

### 阶段二：生成
4. 生成完整的 C# 代码，要求：
   - 完整可编译（包含所有 using）
   - 遵循已有代码风格
   - 包含 XML 注释
   - 使用 [SerializeField] private 代替 public
   - **每个文件前必须用 `// === 相对路径 ===` 单独一行标记路径**
   - **代码必须放在 ```csharp 和 ``` 之间**

### 阶段三：自审（关键！）
5. 调用 read_file 读取你刚生成的所有代码文件
6. 逐项检查：
   - ❌ Update/FixedUpdate 中是否有 new / ToString / string拼接 / LINQ ?
   - ❌ Update 中是否调用了 GetComponent / Find / Camera.main ?
   - ❌ 事件订阅 (+= ) 是否有对应的 OnDestroy 取消 (-= ) ?
   - ❌ 是否引用了不存在的类或命名空间 ?
   - ❌ 命名是否符合项目已有规范 ?

7. 如果发现任何问题：
   - 明确指出哪里有问题
   - 调用 write_file 修复代码
   - 再次调用 read_file 复查，直到没有任何问题

### 阶段四：保存与报告
8. 确认所有代码已通过自审后，输出最终报告，格式如下：
✅ 代码生成完成
生成的文件：

路径1（作用说明）

路径2（作用说明）
自审修复的问题：

问题1描述

问题2描述
使用示例：
// 示例代码

## ⚠️ 输出格式强制规则
- 在阶段二生成代码时，**只能输出代码块和路径标记**，禁止输出任何解释性文字。
- 代码块必须以 ```csharp 开头，以 ``` 结尾。
- 路径标记格式：`// === Assets/Scripts/xxx.cs ===`
- 违反上述规则将导致任务失败，请严格遵守。
"""
        result = self.run(prompt, max_rounds=50)
        
        # 后处理：清理可能残留的 Markdown 标记（防止保存到文件）
        cleaned = self._clean_markdown_artifacts(result)
        if cleaned != result:
            print("⚠️ 检测到输出中的 Markdown 残留，已自动清理。")
        return cleaned
 
    def _clean_markdown_artifacts(self, text: str) -> str:
        """清理文本中可能残留的 ```csharp 和 ``` 标记（非代码块位置）"""
        # 移除开头和结尾的 ```csharp 或 ```
        text = re.sub(r'^```csharp\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        # 移除代码块外单独出现的 ```
        text = re.sub(r'(?<!```)\n```(?!```)', '', text)
        return text.strip()


# ===== 快速测试 =====
if __name__ == "__main__":
    agent = CodeGenAgentV2(project_path=".")
    print("=" * 60)
    print("🤖 自纠错代码生成测试（增强版）")
    print("=" * 60)
    result = agent.generate_with_self_review(
        "创建一个通用对象池系统 ObjectPool<T>，要求：\n"
        "- 支持预热（预创建对象）\n"
        "- 池空时自动扩容\n"
        "- 回收时自动 SetActive(false)\n"
        "- 有池容量上限防止无限增长\n"
        "- 实现 IPoolable 接口让对象池化时能重置状态"
    )
    print("\n" + "=" * 60)
    print("最终结果：")
    print(result)