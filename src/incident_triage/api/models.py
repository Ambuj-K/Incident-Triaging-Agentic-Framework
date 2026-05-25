from pydantic import BaseModel
from typing import Optional


class InvestigateRequest(BaseModel):
    incident: str
    thread_id: Optional[str] = None


class InvestigateResponse(BaseModel):
    thread_id: str
    routing: str
    severity: Optional[str] = None
    complexity: Optional[str] = None
    confidence: Optional[float] = None
    escalate: Optional[bool] = None
    summary: Optional[str] = None
    immediate_actions: list[str] = []
    affected_systems: list[str] = []
    consistency_flags: list[str] = []
    human_review_reason: Optional[str] = None
    auto_resolved: bool = False
    requires_human_review: bool = False
    steps_taken: list[str] = []
    tool_results: dict = {}
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model: str
    corpus_chunks: int
    version: str = "1.0.0"
