"""集中读取环境变量，支持百炼 / Ollama 两种 AI 提供方。"""
import os
from dotenv import load_dotenv

load_dotenv()

# bailian | ollama
PROVIDER = os.getenv("LLM_PROVIDER", "bailian").strip().lower()

# ---- 百炼 / DashScope（OpenAI 兼容） ----
BAILIAN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
BAILIAN_BASE_URL = os.getenv(
    "BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
).strip()
BAILIAN_MODEL = os.getenv("BAILIAN_MODEL", "qwen-plus").strip()

# ---- Ollama（本地，OpenAI 兼容） ----
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5").strip()


def active_model() -> str:
    return OLLAMA_MODEL if PROVIDER == "ollama" else BAILIAN_MODEL


def provider_info() -> dict:
    """前端展示当前 AI 配置（不含密钥）。"""
    return {
        "provider": PROVIDER,
        "model": active_model(),
        "base_url": OLLAMA_BASE_URL if PROVIDER == "ollama" else BAILIAN_BASE_URL,
        "ready": PROVIDER == "ollama" or bool(BAILIAN_API_KEY),
    }
