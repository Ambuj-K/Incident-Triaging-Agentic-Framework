def get_capability_summary(
    retrieved_runbooks: list[dict],
    retrieved_incidents: list[dict],
    tool_results: dict,
) -> str:
    """
    Derives capabilities dynamically from what was actually retrieved.
    Injected into Pass 2 system prompt so the LLM knows exactly
    what context it has available for this investigation.
    """
    lines = ["**INVESTIGATION CONTEXT — READ BEFORE RESPONDING**\n"]

    # Runbooks available
    if retrieved_runbooks:
        runbook_ids = [r["doc_id"] for r in retrieved_runbooks]
        lines.append(f"Runbooks available: {', '.join(runbook_ids)}")
    else:
        lines.append("Runbooks available: None")

    # Past incidents available
    if retrieved_incidents:
        incident_ids = [i["doc_id"] for i in retrieved_incidents]
        lines.append(f"Past incidents available: {', '.join(incident_ids)}")
    else:
        lines.append("Past incidents available: None")

    # System status
    system_statuses = tool_results.get("system_statuses", [])
    degraded = [
        s["system"] for s in system_statuses
        if s.get("status") in ("degraded", "down")
    ]
    unknown = [
        s["system"] for s in system_statuses
        if s.get("status") == "unknown"
    ]

    if degraded:
        lines.append(f"Systems currently degraded: {', '.join(degraded)}")
    if unknown:
        lines.append(
            f"Systems not in monitoring registry: {', '.join(unknown)}"
        )
    if not degraded and not unknown:
        lines.append("System status: all checked systems operational")

    # Escalation contacts
    if tool_results.get("escalation_contacts"):
        team = tool_results["escalation_contacts"]["team"]
        contact = tool_results["escalation_contacts"]["primary_contact"]
        lines.append(f"Escalation contacts available: {team} — {contact}")
    else:
        lines.append("Escalation contacts: not retrieved")

    lines.append("\n**Confidence conventions:**")
    lines.append("— confidence < 0.4: insufficient context for reliable diagnosis")
    lines.append("— confidence > 0.7: well-grounded diagnosis")
    lines.append("— confidence DROP Pass1→Pass2: retrieved context not relevant")
    lines.append("— confidence RISE Pass1→Pass2: relevant context found")

    lines.append("\n**I CANNOT determine:**")
    lines.append("— Systems not listed in available runbooks")
    lines.append(
        "— Root causes requiring logs or diagnostic data not provided"
    )
    lines.append("— Infrastructure changes or fix execution")

    return "\n".join(lines)
