"""
配置生成 Agent

用法：
    agent = ConfigGenAgent(config_dir="path/to/Configs/Heroes")
    config = agent.generate("新英雄：暗影刺客，高攻低血，有隐身和背刺技能")
    errors = agent.validate(config)
"""

import os
import re
import json
from agents.base import BaseAgent


class ConfigGenAgent(BaseAgent):
    def __init__(self, config_dir: str = None):
        super().__init__(prompt_file="prompts/config_gen.md")
        self.config_dir = config_dir
        self.existing_configs = self._load_existing()

    def _load_existing(self) -> dict:
        """加载目录下已有的 JSON 配置"""
        configs = {}
        if not self.config_dir or not os.path.isdir(self.config_dir):
            return configs
        for f in os.listdir(self.config_dir):
            if f.endswith(".json"):
                path = os.path.join(self.config_dir, f)
                try:
                    with open(path, encoding="utf-8") as fp:
                        configs[f] = json.load(fp)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"  ⚠️ 跳过无法解析的配置: {f} ({e})")
        return configs

    def generate(self, requirement: str, schema: str = None) -> dict:
        """自然语言 → JSON 配置"""
        context_parts = []
        if schema:
            context_parts.append(f"【配置 Schema（必须严格遵守）】\n{schema}")

        if self.existing_configs:
            samples = list(self.existing_configs.items())[:3]
            examples = "\n".join(
                f"// {name}\n{json.dumps(cfg, ensure_ascii=False, indent=2)}"
                for name, cfg in samples
            )
            context_parts.append(f"【已有配置（参考格式和数值范围）】\n{examples}")

        response = self.llm.chat_with_context(
            system_prompt=self.system_prompt,
            context="\n\n".join(context_parts) if context_parts else "（无已有配置参考，请按通用格式生成）",
            question=requirement,
        )

        # 提取 JSON
        json_match = re.search(r'```json\n(.*?)```', response, re.DOTALL)
        try:
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response)
        except json.JSONDecodeError:
            print("⚠️ AI 返回的不是合法 JSON，原始输出：")
            print(response[:500])
            return {"_error": "JSON 解析失败", "_raw": response}

    def validate(self, config: dict) -> list:
        """基础校验"""
        errors = []

        if "_error" in config:
            return [config["_error"]]

        # ID 唯一性检查
        if "id" in config:
            for name, existing in self.existing_configs.items():
                if isinstance(existing, dict) and existing.get("id") == config["id"]:
                    errors.append(f"ID {config['id']} 与 {name} 冲突")

        # 数值范围检查
        def _check_values(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _check_values(v, f"{path}.{k}")
            elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
                if obj < 0 and "cost" not in path.lower() and "offset" not in path.lower():
                    errors.append(f"{path} = {obj}（数值为负，请确认是否合理）")

        _check_values(config)
        return errors

    def save(self, config: dict, output_path: str) -> str:
        """保存配置到文件"""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 已保存: {output_path}")
        return output_path


# ===== 快速测试 =====
if __name__ == "__main__":
    agent = ConfigGenAgent()
    print("=" * 60)
    print("📋 配置生成测试")
    print("=" * 60)
    config = agent.generate("新武器：寒冰长弓，远程武器，攻击速度中等，附带冰冻减速效果，暴击率较高")
    errors = agent.validate(config)
    if errors:
        print("⚠️ 校验警告:", errors)
    else:
        print("✅ 校验通过")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    agent.save(config, "generated/frost_bow.json")