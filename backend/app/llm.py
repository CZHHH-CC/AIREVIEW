"""AI 调用层：百炼与 Ollama 都兼容 OpenAI API，统一用 openai SDK，靠配置切换。

客户端按当前配置构建；前端改动配置后（config.revision 变化）自动重建。
"""
from openai import OpenAI

from . import config

_client: OpenAI | None = None
_client_rev = -1


def _get_client() -> OpenAI:
    global _client, _client_rev
    if _client is None or _client_rev != config.revision():
        _client = OpenAI(base_url=config.active_base_url(), api_key=config.active_api_key())
        _client_rev = config.revision()
    return _client


def chat_json(system: str, user: str) -> str:
    """请求模型返回 JSON 字符串。优先用 json_object 模式，不支持则降级。"""
    client = _get_client()
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


def test_connection() -> dict:
    """用当前配置发一个最小请求，验证连通性。"""
    if not config.is_ready():
        return {"ok": False, "error": "尚未配置 API Key"}
    try:
        client = _get_client()
        client.chat.completions.create(
            model=config.active_model(),
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        return {"ok": True, "model": config.active_model()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
