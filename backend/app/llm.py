"""AI 调用层：百炼与 Ollama 都兼容 OpenAI API，统一用 openai SDK，靠配置切换。"""
from functools import lru_cache

from openai import OpenAI

from . import config


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if config.PROVIDER == "ollama":
        # Ollama 的 OpenAI 兼容端点不校验 key，用占位符即可
        return OpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")
    return OpenAI(base_url=config.BAILIAN_BASE_URL, api_key=config.BAILIAN_API_KEY or "EMPTY")


def chat_json(system: str, user: str) -> str:
    """请求模型返回 JSON 字符串。优先用 json_object 模式，不支持则降级。"""
    client = _client()
    model = config.active_model()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception:
        # 部分本地模型不支持 response_format，降级为普通调用
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
    return resp.choices[0].message.content or ""
