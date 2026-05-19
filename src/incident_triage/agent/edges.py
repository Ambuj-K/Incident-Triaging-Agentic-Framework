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
    - Error occurred during investigation
    - Consistency flags raised between Pass 1 and Pass 2
      (except confidence_dropped alone on low severity)
    - Final report requires escalation
    - system_specific_confidence < 0.4 (< 0.1 for low severity)
    - Complexity is complex
    - Contradiction detected
    - Insufficient context

    Routes to auto_resolve when:
    - Severity is low or medium
    - system_specific_confidence >= 0.3 (>= 0.1 for low severity corpus gap)
    - No escalation, contradiction, or context flags raised
    """
    if state.error_occurred:
        return "human_review"

    report = state.final_report
    if report is None:
        return "human_review"

    # Consistency flags — severity-aware
    if state.consistency_flags:
        if report.severity == Severity.LOW:
            non_confidence_flags = [
                f for f in state.consistency_flags
                if "confidence_dropped" not in f
            ]
            if non_confidence_flags:
                return "human_review"
            # confidence drop only on low severity — fall through
        else:
            return "human_review"

    if report.escalate:
        return "human_review"

    # Confidence threshold — severity-aware
    if report.system_specific_confidence < 0.4:
        if report.severity == Severity.LOW:
            if report.system_specific_confidence < 0.1:
                return "human_review"
            # confidence 0.1-0.4 on low severity corpus gap — fall through
        else:
            return "human_review"

    if report.complexity == Complexity.COMPLEX:
        return "human_review"

    if report.contradiction_detected:
        return "human_review"

    if report.insufficient_context:
        return "human_review"

    # Safe to auto-resolve
    if report.severity in (Severity.LOW, Severity.MEDIUM):
        if report.system_specific_confidence >= 0.1:
            return "auto_resolve"

    return "human_review"


def route_after_classification(state: AgentState) -> str:
    """
    After Pass 1 classification:
    - Error occurred → human review
    - No initial report → human review
    - Simple, low severity, confident, no flags → auto resolve (fast path)
    - Otherwise → retrieve context
    """
    if state.error_occurred or state.initial_report is None:
        return "human_review"

    from incident_triage.pipeline.triage_pipeline import should_skip_retrieval
    if should_skip_retrieval(state.initial_report):
        return "auto_resolve"

    return "retrieve_context"
