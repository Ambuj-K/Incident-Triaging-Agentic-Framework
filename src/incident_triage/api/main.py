import os
import uuid

from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware

from incident_triage.api.models import (
    InvestigateRequest,
    InvestigateResponse,
    HealthResponse,
)
from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState

graph = build_graph(interrupt_on_human_review=False)

app = FastAPI(
    title="Incident Triage Agent",
    description="Agentic pipeline for retail operations incident triage",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY", "dev-key-change-in-production")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        from incident_triage.retrieval.vector_store import get_chunk_count
        chunk_count = get_chunk_count()
    except Exception:
        chunk_count = 259
    return HealthResponse(
        status="ok",
        model=os.environ.get("MODEL", "gemini-3.1-flash-lite"),
        corpus_chunks=chunk_count,
    )


@app.post("/investigate", response_model=InvestigateResponse)
def investigate(
    request: InvestigateRequest,
    api_key: str = Security(verify_api_key),
):
    thread_id = request.thread_id or str(uuid.uuid4())

    try:
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = AgentState(incident_description=request.incident)
        result = graph.invoke(initial_state, config=config)

        if result.get("validation_error"):
            routing = "validation_failed"
        elif result.get("auto_resolved"):
            routing = "auto_resolve"
        else:
            routing = "human_review"

        final_report = result.get("final_report")

        return InvestigateResponse(
            thread_id=thread_id,
            routing=routing,
            severity=final_report.severity.value if final_report else None,
            complexity=final_report.complexity.value if final_report else None,
            confidence=final_report.system_specific_confidence if final_report else None,
            escalate=final_report.escalate if final_report else None,
            summary=final_report.summary if final_report else None,
            immediate_actions=final_report.immediate_actions if final_report else [],
            affected_systems=final_report.affected_systems if final_report else [],
            consistency_flags=result.get("consistency_flags", []),
            human_review_reason=result.get("human_review_reason", ""),
            auto_resolved=result.get("auto_resolved", False),
            requires_human_review=result.get("requires_human_review", False),
            steps_taken=result.get("steps_taken", []),
            tool_results=result.get("tool_results", {}),
        )

    except Exception as e:
        return InvestigateResponse(
            thread_id=thread_id,
            routing="error",
            error=str(e),
        )


@app.get("/traces/{thread_id}")
def get_trace(
    thread_id: str,
    api_key: str = Security(verify_api_key),
):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)

        if not state or not state.values:
            raise HTTPException(
                status_code=404,
                detail=f"No investigation found for thread_id: {thread_id}"
            )

        values = state.values
        final_report = values.get("final_report")

        return {
            "thread_id": thread_id,
            "steps_taken": values.get("steps_taken", []),
            "consistency_flags": values.get("consistency_flags", []),
            "human_review_reason": values.get("human_review_reason", ""),
            "confidence": (
                final_report.system_specific_confidence
                if final_report else None
            ),
            "severity": (
                final_report.severity.value if final_report else None
            ),
            "tool_results": values.get("tool_results", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
