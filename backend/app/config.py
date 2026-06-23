"""运行时可变配置：以 .env 为默认值，可被前端修改并持久化到 settings.json。

百炼 / Ollama 都走 OpenAI 兼容协议，靠这里的 provider 字段切换。
"""
import json
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "settings.json"

# .env 提供初始默认值
DEFAULTS: Dict[str, str] = {
    "provider": os.getenv("LLM_PROVIDER", "bailian").strip().lower(),
    "bailian_api_key": os.getenv("DASHSCOPE_API_KEY", "").strip(),
    "bailian_base_url": os.getenv(
        "BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ).strip(),
    "bailian_model": os.getenv("BAILIAN_MODEL", "qwen-plus").strip(),
    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip(),
    "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5").strip(),
}

_settings: Dict[str, str] = dict(DEFAULTS)

# 占位密钥视为“未配置”，避免 .env.example 里的 sk-xxxx 被误判为已就绪
_PLACEHOLDER_KEYS = {"", "sk-xxxxxxxxxxxxxxxx"}

# 被前端改动时由 llm 层重建客户端
_revision = 0


def _load() -> None:
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            _settings.update({k: v for k, v in saved.items() if k in DEFAULTS})
        except (json.JSONDecodeError, OSError):
            pass


def _save() -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(_settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


_load()


# ---- 读取当前生效值 ----
def provider() -> str:
    return _settings["provider"]


def revision() -> int:
    return _revision


def active_model() -> str:
    return _settings["ollama_model"] if provider() == "ollama" else _settings["bailian_model"]


def active_base_url() -> str:
    return _settings["ollama_base_url"] if provider() == "ollama" else _settings["bailian_base_url"]


def active_api_key() -> str:
    # Ollama 不校验 key，用占位符
    return "ollama" if provider() == "ollama" else (_settings["bailian_api_key"] or "EMPTY")


def _has_key() -> bool:
    return _settings["bailian_api_key"] not in _PLACEHOLDER_KEYS


def is_ready() -> bool:
    return provider() == "ollama" or _has_key()


# ---- 前端用 ----
def provider_info() -> dict:
    """顶部徽标用：当前提供方/模型，不含密钥。"""
    return {
        "provider": provider(),
        "model": active_model(),
        "base_url": active_base_url(),
        "ready": is_ready(),
    }


def editable_settings() -> dict:
    """配置面板回显用：返回全部可编辑字段，密钥只给“是否已配置”。"""
    return {
        "provider": _settings["provider"],
        "bailian_base_url": _settings["bailian_base_url"],
        "bailian_model": _settings["bailian_model"],
        "bailian_has_key": _has_key(),
        "ollama_base_url": _settings["ollama_base_url"],
        "ollama_model": _settings["ollama_model"],
    }


def update_settings(patch: dict) -> dict:
    """应用前端改动并持久化。空的 bailian_api_key 表示“保持原值不变”。"""
    global _revision
    allowed = set(DEFAULTS) | {"bailian_api_key"}
    for k, v in patch.items():
        if k not in allowed or v is None:
            continue
        if k == "provider":
            v = str(v).strip().lower()
            if v not in ("bailian", "ollama"):
                continue
        if k == "bailian_api_key" and str(v).strip() == "":
            continue  # 留空不覆盖已存密钥
        _settings[k] = str(v).strip()
    _save()
    _revision += 1  # 通知 llm 层重建客户端
    return editable_settings()
