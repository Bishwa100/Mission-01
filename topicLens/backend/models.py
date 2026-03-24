from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SearchRequest(BaseModel):
    topic: str


class SearchResponse(BaseModel):
    job_id: str
    status: str


class InsightsModel(BaseModel):
    summary: str
    trends: List[str]
    action_plan: List[str]


class ResultItem(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    source: Optional[str] = None


class JobStatus(BaseModel):
    id: str
    topic: str
    status: str
    step: Optional[str] = None
    progress: Optional[int] = None
    results: Optional[Dict[str, Any]] = None
    insights: Optional[InsightsModel] = None
    total_results: Optional[int] = None
