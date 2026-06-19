from incident_triage.agent.state import AgentState
from incident_triage.clients.llm_client import LLMClient
from incident_triage.retrieval.retriever import retrieve_for_incident
from incident_triage.pipeline.triage_pipeline import format_context, check_report_consistency
from incident_triage.config.llm_config import DEFAULT_CONFIG
from langfuse import get_client, observe
from incident_triage.agent.tools import (
    check_system_status,
    get_escalation_contacts,
)
from incident_triage.agent.capability_registry import get_capability_summary

langfuse = get_client()


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


@observe(name="classify_incident")
def classify_incident(state: AgentState) -> dict:
    """Node 3 — Pass 1 LLM call."""
    langfuse.update_current_span(
        input={"incident": state.incident_description[:200]},
    )

    try:
        initial_report = llm_client.triage_incident(
            state.incident_description
        )

        langfuse.update_current_span(
            output={
                "severity": initial_report.severity.value,
                "affected_systems": initial_report.affected_systems,
                "confidence": initial_report.system_specific_confidence,
            }
        )

        return {
            "initial_report": initial_report,
            "steps_taken": state.steps_taken + [
                f"classify_incident: severity={initial_report.severity}, "
                f"confidence={initial_report.system_specific_confidence}"
            ],
        }

    except Exception as e:
        langfuse.update_current_span(
            output={"error": str(e)},
            level="ERROR",
        )
        return {
            "error_occurred": True,
            "error_message": f"Classification failed: {str(e)}",
            "steps_taken": state.steps_taken + [
                f"classify_incident: error - {str(e)}"
            ],
        }


@observe(name="retrieve_context")
def retrieve_context(state: AgentState) -> dict:
    """Node 4 — Retrieve relevant runbooks and past incidents."""
    if state.error_occurred or state.initial_report is None:
        return {
            "retrieval_attempted": False,
            "steps_taken": state.steps_taken + [
                "retrieve_context: skipped - no initial report"
            ],
        }

    langfuse.update_current_span(
        input={
            "affected_systems": state.initial_report.affected_systems,
            "incident": state.incident_description[:200],
        }
    )

    try:
        affected_systems = [
            s.lower().replace(" ", "_").replace("-", "_")
            for s in state.initial_report.affected_systems
        ]

        results = retrieve_for_incident(
            incident_description=state.incident_description,
            top_k=3,
            affected_systems=affected_systems,
            use_hybrid=True,
        )

        runbooks = results.get("runbooks", [])
        incidents = results.get("past_incidents", [])
        context = format_context(results)

        langfuse.update_current_span(
            output={
                "runbooks_retrieved": [r["doc_id"] for r in runbooks],
                "incidents_retrieved": [i["doc_id"] for i in incidents],
                "top_score": runbooks[0].get(
                    "rrf_score", runbooks[0].get("similarity", 0)
                ) if runbooks else 0,
            }
        )

        return {
            "retrieved_runbooks": runbooks,
            "retrieved_incidents": incidents,
            "context_formatted": context,
            "retrieval_attempted": True,
            "steps_taken": state.steps_taken + [
                f"retrieve_context: {len(runbooks)} runbooks, "
                f"{len(incidents)} incidents"
            ],
        }

    except Exception as e:
        langfuse.update_current_span(
            output={"error": str(e)},
            level="ERROR",
        )
        return {
            "retrieval_attempted": True,
            "context_formatted": "Retrieval failed — proceeding without context.",
            "error_occurred": True,
            "error_message": f"Retrieval failed: {str(e)}",
            "steps_taken": state.steps_taken + [
                f"retrieve_context: error - {str(e)}"
            ],
        }


@observe(name="investigate_with_context")
def investigate_with_context(state: AgentState) -> dict:
    """Node 5 — Pass 2 LLM call with tool enrichment.

    Order of operations:
      1. Check system status for systems identified in Pass 1
         (state.initial_report.affected_systems) — this can run
         before Pass 2 because we already know candidate systems
         from Pass 1 classification.
      2. Build capability summary from retrieval + live tool results
         so Pass 2 reasoning is grounded in what is actually known
         right now, not just retrieved documents.
      3. Run Pass 2 LLM call with retrieved context + capability summary.
      4. Get escalation contacts if the Pass 2 report escalates.
      5. Return final report + audit trail.

    NOTE: This is the single definition of investigate_with_context.
    A previous version of this file had two functions with this same
    name — the second silently overwrote the first, so the capability
    registry integration was dead code until this merge. Do not
    re-introduce a duplicate definition.
    """
    if state.error_occurred and state.initial_report is None:
        return {
            "steps_taken": state.steps_taken + [
                "investigate_with_context: skipped - error state"
            ],
        }

    langfuse.update_current_span(
        input={
            "incident": state.incident_description[:200],
            "context_length": len(state.context_formatted),
            "runbooks_used": [r["doc_id"] for r in state.retrieved_runbooks],
            "incidents_used": [i["doc_id"] for i in state.retrieved_incidents],
        }
    )

    try:
        tool_results = {}

        # Step 1 — check status of systems identified in Pass 1.
        # Pass 1's affected_systems is the best signal available
        # before Pass 2 has run.
        system_statuses = []
        for system in state.initial_report.affected_systems[:3]:
            status = check_system_status(system)
            system_statuses.append(status)
        tool_results["system_statuses"] = system_statuses

        # Step 2 — build capability summary grounding Pass 2 in
        # both retrieved context and live system state.
        capability_summary = get_capability_summary(
            retrieved_runbooks=state.retrieved_runbooks,
            retrieved_incidents=state.retrieved_incidents,
            tool_results=tool_results,
        )

        context = state.context_formatted or "No relevant context found."
        full_context = capability_summary + "\n\n---\n\n" + context

        # Step 3 — Pass 2 LLM call, grounded in full_context.
        final_report = llm_client.triage_with_context(
            incident_description=state.incident_description,
            context=full_context,
        )

        consistency = check_report_consistency(
            state.initial_report,
            final_report,
        )

        confidence_delta = (
            final_report.system_specific_confidence
            - state.initial_report.system_specific_confidence
        )

        # Step 4 — escalation contacts, now that we know whether
        # Pass 2 actually wants to escalate.
        escalation_contacts = None
        if final_report.escalate and state.retrieved_runbooks:
            top_runbook = state.retrieved_runbooks[0]
            team = top_runbook.get("team", "platform_engineering")
            escalation_contacts = get_escalation_contacts(team)
            tool_results["escalation_contacts"] = escalation_contacts

        langfuse.update_current_span(
            output={
                "severity": final_report.severity.value,
                "confidence": final_report.system_specific_confidence,
                "confidence_delta": round(confidence_delta, 3),
                "escalate": final_report.escalate,
                "consistency_flags": consistency["consistency_flags"],
                "systems_checked": len(system_statuses),
                "escalation_contacts_retrieved": escalation_contacts is not None,
            }
        )

        review_reason = ""
        if consistency["requires_review"]:
            review_reason = (
                f"Consistency flags: "
                f"{', '.join(consistency['consistency_flags'])}"
            )
        elif final_report.escalate:
            review_reason = (
                f"Severity {final_report.severity.value} requires escalation"
            )
        elif final_report.system_specific_confidence < 0.4:
            review_reason = (
                f"Low confidence ({final_report.system_specific_confidence})"
                f" — insufficient context"
            )
        elif final_report.contradiction_detected:
            review_reason = "Contradictory information in incident description"
        elif final_report.insufficient_context:
            review_reason = "Insufficient context for reliable triage"

        return {
            "final_report": final_report,
            "consistency_flags": consistency["consistency_flags"],
            "human_review_reason": review_reason,
            "tool_results": tool_results,
            "steps_taken": state.steps_taken + [
                f"investigate_with_context: "
                f"severity={final_report.severity.value}, "
                f"confidence={final_report.system_specific_confidence}, "
                f"escalate={final_report.escalate}, "
                f"consistency_flags={len(consistency['consistency_flags'])}, "
                f"tools_called={len(tool_results)}"
            ],
        }

    except Exception as e:
        return {
            "final_report": state.initial_report,
            "error_occurred": True,
            "error_message": (
                f"Investigation failed: {str(e)}, using initial report"
            ),
            "steps_taken": state.steps_taken + [
                f"investigate_with_context: error - {str(e)}"
            ],
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