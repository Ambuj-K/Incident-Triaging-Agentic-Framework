from typing import Optional
from pydantic import BaseModel
from incident_triage.models.incident_report import IncidentReport


class AgentState(BaseModel):
    """
    Shared state across all agent nodes.
    Every field is optional — nodes add to state progressively.
    """

    # Input
    incident_description: str = ""

    # Validation
    input_valid: bool = False
    validation_error: Optional[str] = None

    # Pass 1 output
    initial_report: Optional[IncidentReport] = None

    # Retrieval output
    retrieved_runbooks: list[dict] = []
    retrieved_incidents: list[dict] = []
    context_formatted: str = ""
    retrieval_attempted: bool = False

    # Pass 2 output
    consistency_flags: list[str] = []
    final_report: Optional[IncidentReport] = None

    # Routing signals
    requires_human_review: bool = False
    human_review_reason: str = ""
    auto_resolved: bool = False

    # Audit trail
    steps_taken: list[str] = []
    error_occurred: bool = False
    error_message: str = ""

    class Config:
        arbitrary_types_allowed = True
