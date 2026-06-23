"""简历存储：小规模场景用单个 JSON 文件即可，无需数据库/向量库。"""
import json
import uuid
from pathlib import Path
from typing import List

from .models import Resume

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "resumes.json"


def _ensure_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_resumes() -> List[Resume]:
    _ensure_file()
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [Resume(**r) for r in raw]


def save_resumes(resumes: List[Resume]) -> None:
    _ensure_file()
    DATA_FILE.write_text(
        json.dumps([r.model_dump() for r in resumes], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_resume(resume: Resume) -> Resume:
    if not resume.id:
        resume.id = uuid.uuid4().hex[:8]
    resumes = load_resumes()
    resumes.append(resume)
    save_resumes(resumes)
    return resume


def delete_resume(resume_id: str) -> bool:
    resumes = load_resumes()
    kept = [r for r in resumes if r.id != resume_id]
    if len(kept) == len(resumes):
        return False
    save_resumes(kept)
    return True
