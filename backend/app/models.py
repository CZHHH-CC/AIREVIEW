"""请求/响应数据结构。"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Resume(BaseModel):
    id: str
    name: str
    title: str = ""                 # 期望/当前职位
    years: float = 0                # 工作年限
    education: str = ""
    skills: List[str] = Field(default_factory=list)
    summary: str = ""               # 一句话亮点
    experience: str = ""            # 经历正文


class SettingsUpdate(BaseModel):
    """前端配置面板提交的字段，均可选；bailian_api_key 留空表示不修改。"""
    provider: Optional[str] = None          # bailian | ollama
    bailian_api_key: Optional[str] = None
    bailian_base_url: Optional[str] = None
    bailian_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None


class RecommendRequest(BaseModel):
    jd: str = Field(..., description="岗位需求 / JD 文本")
    top_n: int = Field(5, ge=1, le=20)


class Recommendation(BaseModel):
    resume_id: str
    name: str
    title: str = ""
    match_score: int = Field(0, ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)   # 推荐理由（匹配点）
    gaps: List[str] = Field(default_factory=list)       # 差距 / 风险
    summary: str = ""                                    # AI 的一句话总评
    resume: Optional[Resume] = None                      # 回填的完整简历


class RecommendResponse(BaseModel):
    provider: str
    model: str
    overall: str = ""               # 对整体候选池的总结
    recommendations: List[Recommendation] = Field(default_factory=list)
