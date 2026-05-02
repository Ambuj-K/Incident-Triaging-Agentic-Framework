from incident_triage.clients.llm_client import LLMClient
from incident_triage.models.incident_report import IncidentReport
from incident_triage.retrieval.retriever import retrieve_for_incident
from incident_triage.config.llm_config import DEFAULT_CONFIG, LLMConfig


def format_context(retrieval_results: dict) -> str:
    """
    Format retrieved runbooks and past incidents into
    a structured context string for the LLM prompt.
    """
    context_parts = []

    runbooks = retrieval_results.get("runbooks", [])
    if runbooks:
        context_parts.append("## RELEVANT RUNBOOKS")
        for i, doc in enumerate(runbooks[:3], 1):
            context_parts.append(
                f"\n### Runbook {i}: {doc['doc_id']} "
                f"(Team: {doc['team']}, "
                f"Section: {doc['section']})\n"
                f"{doc['content'][:800]}"
            )

    past_incidents = retrieval_results.get("past_incidents", [])
    if past_incidents:
        context_parts.append("\n## RELEVANT PAST INCIDENTS")
        for i, doc in enumerate(past_incidents[:3], 1):
            context_parts.append(
                f"\n### Past Incident {i}: {doc['doc_id']} "
                f"(Team: {doc['team']}, "
                f"Section: {doc['section']})\n"
                f"{doc['content'][:800]}"
            )

    if not context_parts:
        return "No relevant context found in knowledge base."

    return "\n".join(context_parts)

# After Pass 2, if severity or affected_systems changed significantly
# between Pass 1 and Pass 2, flag it for review

def check_report_consistency(
    initial: IncidentReport,
    final: IncidentReport,
) -> dict:
    flags = []

    # Severity escalated between passes — context revealed worse situation
    if final.severity == Severity.CRITICAL and initial.severity != Severity.CRITICAL:
        flags.append("severity_escalated_with_context")

    # Affected systems changed significantly
    initial_systems = set(initial.affected_systems)
    final_systems = set(final.affected_systems)
    if len(final_systems - initial_systems) > 2:
        flags.append("affected_systems_significantly_changed")

    # Confidence dropped despite having context
    if final.system_specific_confidence < initial.system_specific_confidence:
        flags.append("confidence_dropped_with_context")

    return {
        "consistency_flags": flags,
        "requires_review": len(flags) > 0,
    }


class TriagePipeline:
    """
    Two-pass incident triage pipeline:
    Pass 1: Classify incident, identify affected systems
    Pass 2: Retrieve context, produce grounded investigation report
    """

    def __init__(self, config: LLMConfig = DEFAULT_CONFIG):
        self.llm_client = LLMClient(config=config)

    def run(
        self,
        incident_description: str,
        verbose: bool = False,
    ) -> dict:
        """
        Run full two-pass triage pipeline.

        Returns:
            dict with:
            - initial_report: IncidentReport from Pass 1
            - retrieved_context: raw retrieval results
            - final_report: IncidentReport from Pass 2
            - context_used: formatted context string passed to LLM
        """

        # Pass 1 — Initial classification
        if verbose:
            print("\n[Pass 1] Classifying incident...")

        initial_report = self.llm_client.triage_incident(
            incident_description
        )

        if verbose:
            print(f"  Severity: {initial_report.severity}")
            print(f"  Affected systems: {initial_report.affected_systems}")
            print(f"  system_specific_confidence: "
                  f"{initial_report.system_specific_confidence}")

        # Retrieve context using affected systems from Pass 1
        if verbose:
            print("\n[Retrieval] Fetching relevant context...")

        affected_systems = [
            s.lower().replace(" ", "_").replace("-", "_")
            for s in initial_report.affected_systems
        ]

        retrieval_results = retrieve_for_incident(
            incident_description=incident_description,
            top_k=3,
            affected_systems=affected_systems,
            use_hybrid=True,
        )

        if verbose:
            runbooks = retrieval_results.get("runbooks", [])
            incidents = retrieval_results.get("past_incidents", [])
            print(f"  Retrieved {len(runbooks)} runbooks, "
                  f"{len(incidents)} past incidents")
            for r in runbooks:
                print(f"    Runbook: {r['doc_id']} - {r['section']}")
            for i in incidents:
                print(f"    Incident: {i['doc_id']} - {i['section']}")

        # Format context for Pass 2
        context = format_context(retrieval_results)

        # Pass 2 — Grounded investigation with context
        if verbose:
            print("\n[Pass 2] Producing grounded investigation report...")

        final_report = self.llm_client.triage_with_context(
            incident_description=incident_description,
            context=context,
        )

        consistency = check_report_consistency(initial_report, final_report)

        if verbose:
            print(f"  Severity: {final_report.severity}")
            print(f"  system_specific_confidence: "
                  f"{final_report.system_specific_confidence}")
            print(f"  Escalate: {final_report.escalate}")

        return {
            "initial_report": initial_report,
            "retrieved_context": retrieval_results,
            "final_report": final_report,
            "context_used": context,
            "consistency_flags": consistency,
        }
