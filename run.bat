@echo off
cd /d %~dp0backend
if not exist .venv (
    echo [JDReview] 创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate
echo [JDReview] 安装依赖...
pip install -q -r requirements.txt
if not exist .env (
    copy .env.example .env >nul
    echo [JDReview] 已生成 .env，请填入 DASHSCOPE_API_KEY 或切换 Ollama
)
echo [JDReview] 启动: http://localhost:8000
uvicorn app.main:app --reload --port 8000
