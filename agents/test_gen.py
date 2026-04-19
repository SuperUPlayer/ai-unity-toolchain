"""
测试生成 Agent

用法：
    agent = TestGenAgent()
    result = agent.generate("path/to/SourceCode.cs")
    agent.save(result)
"""

import os
import re
from agents.base import BaseAgent


class TestGenAgent(BaseAgent):
    def __init__(self):
        super().__init__(prompt_file="prompts/test_gen.md")

    def generate(self, source_file: str) -> dict:
        code = self._read_file_safe(source_file)
        if code.startswith("[错误]"):
            return {"_error": code}

        file_name = os.path.basename(source_file)

        response = self.llm.chat_with_context(
            system_prompt=self.system_prompt,
            context=f"被测文件：{file_name}\n\n```csharp\n{code}\n```",
            question=f"为 {file_name} 中所有公开方法生成单元测试。分别输出 EditMode 和 PlayMode 测试（如果需要的话）。",
        )
        print("=" * 60)
        print("AI 原始响应:")
        print(response)
        print("=" * 60)
        return self._parse_tests(response, file_name)
    
    def _parse_tests(self, response: str, source_name: str) -> dict:
        files = {}
        
        # 1. 如果响应以 ```csharp 开头，去掉这一行
        if response.strip().startswith('```csharp'):
            response = response.strip()[9:].lstrip()  # 去掉 ```csharp 及后面的换行
        
        # 2. 尝试提取完整的 ```csharp ... ``` 代码块
        code_blocks = re.findall(r'```csharp\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            base_name = source_name.replace(".cs", "")
            for i, block in enumerate(code_blocks):
                block = block.strip().strip('`').strip()
                if not block:
                    continue
                if "UnityTest" in block or "IEnumerator" in block:
                    path = f"Tests/PlayMode/{base_name}PlayModeTests.cs"
                else:
                    path = f"Tests/EditMode/{base_name}Tests.cs"
                if path not in files:
                    files[path] = block
            return files
        
        # 3. 如果没有完整代码块，则将整个响应作为代码内容（已经去掉了开头的 ```csharp）
        cleaned = response.strip()
        # 去掉结尾可能的不完整行（例如最后一行是 "public" 且没有结束）
        lines = cleaned.split('\n')
        if lines and lines[-1].strip().startswith('public') and not lines[-1].strip().endswith('}'):
            lines.pop()
        cleaned = '\n'.join(lines)
        
        if cleaned:
            base_name = source_name.replace(".cs", "")
            path = f"Tests/EditMode/{base_name}Tests.cs"
            files[path] = cleaned
        
        return files

    def save(self, files: dict, output_dir: str = "generated/") -> list:
        """保存测试文件"""
        saved = []
        for path, code in files.items():
            if path.startswith("_"):
                continue
            full_path = os.path.join(output_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
            saved.append(full_path)
            print(f"  ✅ 已保存: {full_path}")
        return saved


# ===== 快速测试 =====
if __name__ == "__main__":
    # 先创建一个待测试的源文件
    test_source = '''using UnityEngine;

/// <summary>血量组件</summary>
public class HealthComponent : MonoBehaviour
{
    [SerializeField] private float _maxHp = 100f;
    private float _currentHp;

    public float CurrentHp => _currentHp;
    public float MaxHp => _maxHp;
    public bool IsDead => _currentHp <= 0;

    public event System.Action OnDeath;

    public void Initialize(float maxHp)
    {
        _maxHp = maxHp;
        _currentHp = maxHp;
    }

    public void TakeDamage(float damage)
    {
        if (IsDead) return;
        _currentHp = Mathf.Max(0, _currentHp - damage);
        if (IsDead) OnDeath?.Invoke();
    }

    public void Heal(float amount)
    {
        if (IsDead) return;
        _currentHp = Mathf.Min(_maxHp, _currentHp + amount);
    }
}
'''
    os.makedirs("generated", exist_ok=True)
    with open("generated/HealthComponent.cs", "w") as f:
        f.write(test_source)

    agent = TestGenAgent()
    print("=" * 60)
    print("🧪 测试生成")
    print("=" * 60)
    files = agent.generate("generated/HealthComponent.cs")
    agent.save(files)