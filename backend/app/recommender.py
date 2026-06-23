"""核心推荐逻辑：把 JD + 候选简历压缩成 prompt，让 AI 排序并给出理由。"""
import json
import re
from typing import Dict, List

from . import config, llm
from .models import Recommendation, RecommendResponse, Resume

SYSTEM_PROMPT = """你是一位资深的招聘顾问。你的任务是：根据给定的岗位需求(JD)，\
从候选简历列表中挑选最匹配的人选，按匹配度排序，并用中文给出有依据的推荐理由。

要求：
1. 只能从给定的候选简历中挑选，不得编造候选人。
2. 评分基于：技能匹配、工作年限、行业/项目经历、学历等，综合给出 0-100 的 match_score。
3. reasons 写具体的匹配亮点（引用简历中的事实），gaps 写与 JD 的差距或风险。
4. 严格输出 JSON，不要输出多余文字。

输出 JSON 结构：
{
  "overall": "对候选池整体匹配情况的一句话总结",
  "recommendations": [
    {
      "resume_id": "候选简历的 id",
      "match_score": 85,
      "reasons": ["匹配点1", "匹配点2"],
      "gaps": ["差距1"],
      "summary": "一句话总评"
    }
  ]
}
recommendations 按 match_score 从高到低排序，最多返回 top_n 个。"""


def _compact(resumes: List[Resume]) -> str:
    """把简历压成紧凑文本，节省 token。"""
    lines = []
    for r in resumes:
        skills = "、".join(r.skills) if r.skills else "—"
        lines.append(
            f"[id={r.id}] {r.name} | 职位:{r.title or '—'} | "
            f"{r.years}年 | {r.education or '—'} | 技能:{skills}\n"
            f"  亮点:{r.summary or '—'}\n"
            f"  经历:{(r.experience or '—')[:400]}"
        )
    return "\n".join(lines)


def _parse_json(text: str) -> dict:
    text = text.strip()
    # 去掉可能的 ```json ``` 包裹
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 容错：抓取第一个 {...} 块
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def recommend(jd: str, top_n: int = 5) -> RecommendResponse:
    from .store import load_resumes

    resumes = load_resumes()
    by_id: Dict[str, Resume] = {r.id: r for r in resumes}

    if not resumes:
        return RecommendResponse(
            provider=config.provider(),
            model=config.active_model(),
            overall="简历库为空，请先导入简历。",
            recommendations=[],
        )

    user_prompt = (
        f"岗位需求(JD)：\n{jd}\n\n"
        f"候选简历列表（共 {len(resumes)} 份）：\n{_compact(resumes)}\n\n"
        f"请返回最匹配的前 {top_n} 位候选人。"
    )

    raw = llm.chat_json(SYSTEM_PROMPT, user_prompt)
    data = _parse_json(raw)

    recs: List[Recommendation] = []
    for item in data.get("recommendations", [])[:top_n]:
        rid = str(item.get("resume_id", ""))
        resume = by_id.get(rid)
        if not resume:
            continue  # AI 给了不存在的 id，丢弃
        recs.append(
            Recommendation(
                resume_id=rid,
                name=resume.name,
                title=resume.title,
                match_score=int(item.get("match_score", 0)),
                reasons=item.get("reasons", []) or [],
                gaps=item.get("gaps", []) or [],
                summary=item.get("summary", ""),
                resume=resume,
            )
        )

    recs.sort(key=lambda x: x.match_score, reverse=True)
    return RecommendResponse(
        provider=config.PROVIDER,
        model=config.active_model(),
        overall=data.get("overall", ""),
        recommendations=recs,
    )
