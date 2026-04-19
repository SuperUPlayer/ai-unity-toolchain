"""
LLM 统一调用封装

支持智谱GLM-5 / 通义千问 / 任何 OpenAI 兼容 API。
自动降级：主力挂了切备用。
"""

import os
import time
import yaml
from openai import OpenAI


class LLM:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self._clients = {}

    def _load_config(self, path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {
                "llm": {
                    "primary": {
                        "model": "glm-5",
                        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
                        "temperature": 0.2,
                        "max_tokens": 4096,
                    }
                },
                "safety": {"max_tokens_per_request": 8192, "max_file_chars": 15000},
            }

    def _get_client(self, provider: str) -> tuple[OpenAI, str]:
        if provider in self._clients:
            return self._clients[provider]

        config = self.config["llm"].get(provider, self.config["llm"]["primary"])

        key_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "QWEN_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "primary": "ZHIPU_API_KEY",
            "fallback": "QWEN_API_KEY",
            "reasoning": "DEEPSEEK_API_KEY",
        }
        env_key = key_map.get(provider, "ZHIPU_API_KEY")
        api_key = os.getenv(env_key)

        if not api_key:
            raise ValueError(f"未设置环境变量 {env_key}")

        client = OpenAI(api_key=api_key, base_url=config.get("base_url", "https://open.bigmodel.cn/api/paas/v4/"))
        model = config["model"]
        self._clients[provider] = (client, model)
        return client, model

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        primary_cfg = self.config["llm"]["primary"]
        temp = temperature if temperature is not None else primary_cfg.get("temperature", 0.2)
        tokens = max_tokens or primary_cfg.get("max_tokens", 4096)

        for provider in ["primary", "fallback"]:
            try:
                client, model = self._get_client(provider)
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temp,
                    max_tokens=tokens,
                    timeout=180,
                )
                return response.choices[0].message.content
            except ValueError:
                if provider == "fallback":
                    raise
                continue
            except Exception as e:
                print(f"⚠️  {provider} 调用失败: {e}")
                if provider == "fallback":
                    raise
                print("   → 切换到备用模型...")
                time.sleep(1)
                continue

        raise RuntimeError("所有 LLM 提供商均不可用")

    def chat_with_context(self, system_prompt: str, context: str, question: str) -> str:
        max_chars = self.config.get("safety", {}).get("max_file_chars", 15000)
        if len(context) > max_chars:
            context = context[:max_chars] + f"\n\n... [内容过长，已截断到 {max_chars} 字符] ..."

        user_message = f"【上下文】\n{context}\n\n【任务】\n{question}"
        return self.chat(system_prompt, user_message)


if __name__ == "__main__":
    llm = LLM()
    print(llm.chat("你是Unity专家", "Unity中如何避免Update里的GC Alloc？回答简洁。"))