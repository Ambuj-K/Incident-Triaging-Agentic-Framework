from incident_triage.agent.state import AgentState
from incident_triage.clients.llm_client import LLMClient
from incident_triage.retrieval.retriever import retrieve_for_incident
from incident_triage.pipeline.triage_pipeline import format_context check_report_consistency
from incident_triage.config.llm_config import DEFAULT_CONFIG


llm_client = LLMClient(config=DEFAULT_CONFIG)


def validate_input(state: AgentState) -> dict:
    """
    Node 1 — Validate incident input before any LLM calls.
    Catches empty, too short, or obviously malformed input.
    """
    description = state.incident_description.strip()

    if not description:
        return {
            "input_valid": False,
            "validation_error": "Incident description is empty",
            "steps_taken": state.steps_taken + ["validate_input: failed - empty"],
        }

    if len(description.split()) < 5:
        return {
            "input_valid": False,
            "validation_error": f"Incident description too short ({len(description.split())} words). Minimum 5 words required.",
            "steps_taken": state.steps_taken + ["validate_input: failed - too short"],
        }

    if len(description) > 5000:
        return {
            "input_valid": False,
            "validation_error": "Incident description exceeds maximum length of 5000 characters.",
            "steps_taken": state.steps_taken + ["validate_input: failed - too long"],
        }

    return {
        "input_valid": True,
        "steps_taken": state.steps_taken + ["validate_input: passed"],
    }


def request_clarification(state: AgentState) -> dict:
    """
    Node 2 — Handle invalid input.
    Returns structured error state for upstream handling.
    """
    return {
        "requires_human_review": True,
        "human_review_reason": f"Input validation failed: {state.validation_error}",
        "steps_taken": state.steps_taken + ["request_clarification"],
    }


def classify_incident(state: AgentState) -> dict:
    """
    Node 3 — Pass 1 LLM call.
    Classify incident and identify affected systems.
    No retrieval context yet — builds the retrieval query.
    """
    try:
        initial_report = llm_client.triage_incident(
            state.incident_description
        )

        return {
            "initial_report": initial_report,
            "steps_taken": state.steps_taken + [
                f"classify_incident: severity={initial_report.severity}, "
                f"confidence={initial_report.system_specific_confidence}"
            ],
        }

    except Exception as e:
        return {
            "error_occurred": True,
            "error_message": f"Classification failed: {str(e)}",
            "steps_taken": state.steps_taken + [f"classify_incident: error - {str(e)}"],
        }


def investigate_with_context(state: AgentState) -> dict:
    """
    Node 5 — Pass 2 LLM call.
    Produce grounded investigation report using retrieved context.
    """
    if state.error_occurred and state.initial_report is None:
        return {
            "steps_taken": state.steps_taken + ["investigate_with_context: skipped - error state"],
        }

    try:
        context = state.context_formatted or "No relevant context found."

        final_report = llm_client.triage_with_context(
            incident_description=state.incident_description,
            context=context,
        )

        # Consistency check between Pass 1 and Pass 2
        consistency = check_report_consistency(
            state.initial_report,
            final_report,
        )

        # Determine human review reason
        review_reason = ""
        if consistency["requires_review"]:
            review_reason = f"Consistency flags: {', '.join(consistency['consistency_flags'])}"
        elif final_report.escalate:
            review_reason = f"Severity {final_report.severity.value} requires escalation"
        elif final_report.system_specific_confidence < 0.4:
            review_reason = f"Low confidence ({final_report.system_specific_confidence}) — insufficient context"
        elif final_report.contradiction_detected:
            review_reason = "Contradictory information in incident description"
        elif final_report.insufficient_context:
            review_reason = "Insufficient context for reliable triage"

        return {
            "final_report": final_report,
            "consistency_flags": consistency["consistency_flags"],
            "human_review_reason": review_reason,
            "steps_taken": state.steps_taken + [
                f"investigate_with_context: severity={final_report.severity.value}, "
                f"confidence={final_report.system_specific_confidence}, "
                f"escalate={final_report.escalate}, "
                f"consistency_flags={len(consistency['consistency_flags'])}"
            ],
        }

    except Exception as e:
        return {
            "final_report": state.initial_report,
            "error_occurred": True,
            "error_message": f"Investigation failed: {str(e)}, using initial report",
            "steps_taken": state.steps_taken + [f"investigate_with_context: error - {str(e)}"],
        }


def human_review(state: AgentState) -> dict:
    """
    Node 6 — Human in the loop interrupt point.
    Graph pauses here when requires_human_review is True.
    Human can modify state before graph resumes.
    """
    return {
        "steps_taken": state.steps_taken + [
            f"human_review: waiting - reason={state.human_review_reason}"
        ],
    }


def auto_resolve(state: AgentState) -> dict:
    """
    Node 7 — Auto resolution for simple, high confidence incidents.
    Marks incident as resolved without human review.
    """
    return {
        "auto_resolved": True,
        "steps_taken": state.steps_taken + ["auto_resolve: completed"],
    }
