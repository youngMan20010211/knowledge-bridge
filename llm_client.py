import os
import httpx
from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        # 仅在本地开发环境绕过代理，云端环境自动跳过
        if os.environ.get("STREAMLIT_SERVER_MODE") != "cloud":
            os.environ.setdefault("NO_PROXY", "*")
            os.environ.setdefault("no_proxy", "*")

        http_client = httpx.Client(proxy=None, trust_env=False)
        self.client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        self.model = model

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
