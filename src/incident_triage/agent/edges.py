from incident_triage.agent.state import AgentState
from incident_triage.models.incident_report import Severity, Complexity


def route_after_validation(state: AgentState) -> str:
    """
    After input validation:
    - Invalid input → request clarification
    - Valid input → classify incident
    """
    if not state.input_valid:
        return "request_clarification"
    return "classify_incident"


def route_after_classification(state: AgentState) -> str:
    """
    After Pass 1 classification:
    - Error occurred → human review
    - No initial report → human review
    - Otherwise → retrieve context
    """
    if state.error_occurred or state.initial_report is None:
        return "human_review"
    return "retrieve_context"


def route_after_investigation(state: AgentState) -> str:
    """
    After Pass 2 investigation — the core routing decision.

    Routes to human_review when:
    - Final report requires escalation
    - System specific confidence is low (< 0.4) — model not confident
    - Complexity is complex — novel situation needs human judgment
    - Contradiction detected — conflicting information
    - Insufficient context — not enough info to triage reliably
    - Error occurred during investigation

    Routes to auto_resolve when:
    - Low severity (low/medium)
    - High confidence (>= 0.6)
    - Simple or medium complexity
    - No flags raised
    """
    if state.error_occurred:
        return "human_review"

    report = state.final_report
    if report is None:
        return "human_review"

    # Escalation triggers → human review
    if report.escalate:
        return "human_review"

    if report.system_specific_confidence < 0.4:
        return "human_review"

    if report.complexity == Complexity.COMPLEX:
        return "human_review"

    if report.contradiction_detected:
        return "human_review"

    if report.insufficient_context:
        return "human_review"

    # Safe to auto-resolve
    if report.severity in (Severity.LOW, Severity.MEDIUM):
        if report.system_specific_confidence >= 0.6:
            return "auto_resolve"

    # Auto-resolve: low severity, not escalating, no flags raised
    if report.severity in (Severity.LOW, Severity.MEDIUM):
        if not report.escalate:
            if not report.contradiction_detected:
                if not report.insufficient_context:
                    # Lower confidence threshold for low severity
                    if report.system_specific_confidence >= 0.3:
                        return "auto_resolve"

    return "human_review"
