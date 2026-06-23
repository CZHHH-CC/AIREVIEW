"""FastAPI 入口：提供推荐 API、简历管理 API，并托管前端静态页。"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, store
from .models import RecommendRequest, RecommendResponse, Resume
from .recommender import recommend

app = FastAPI(title="JDReview · AI 简历推荐", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def get_config():
    """前端用来展示当前 AI 提供方/模型。"""
    return config.provider_info()


@app.get("/api/resumes")
def list_resumes():
    return store.load_resumes()


@app.post("/api/resumes", response_model=Resume)
def create_resume(resume: Resume):
    return store.add_resume(resume)


@app.delete("/api/resumes/{resume_id}")
def remove_resume(resume_id: str):
    if not store.delete_resume(resume_id):
        raise HTTPException(404, "简历不存在")
    return {"deleted": resume_id}


@app.post("/api/recommend", response_model=RecommendResponse)
def do_recommend(req: RecommendRequest):
    if not req.jd.strip():
        raise HTTPException(400, "JD 不能为空")
    try:
        return recommend(req.jd, req.top_n)
    except Exception as e:
        raise HTTPException(502, f"AI 调用失败：{e}")


# ---- 托管前端（放在最后，避免覆盖 /api 路由）----
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
