import os
os.environ["LANGGRAPH_STRICT_MSGPACK"] = "false"

from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState
from incident_triage.models.incident_report import Severity

graph = build_graph(interrupt_on_human_review=True)

incident = "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked."

config = {"configurable": {"thread_id": "hitl-test-001"}}
initial_state = AgentState(incident_description=incident)

print("=== RUNNING AGENT (will pause at human_review) ===\n")

result = graph.invoke(initial_state, config=config)

print(f"Agent paused at: {result['steps_taken'][-1]}")
print(f"Review reason: {result['human_review_reason']}")
print(f"\nFinal report before human review:")
if result.get("final_report"):
    print(result["final_report"].model_dump_json(indent=2))

print("\n=== SIMULATING HUMAN REVIEW ===")
print("Human overrides severity to critical and adds context\n")

# Verify model_copy works correctly before passing to graph
updated_report = result["final_report"].model_copy(update={
    "severity": Severity.CRITICAL,
    "immediate_actions": [
        "Page DC operations leads immediately",
        "Manually verify stock levels at all 3 DCs",
        "Trigger emergency replenishment for perishable categories",
    ]
})
print(f"Human updated severity: {updated_report.severity.value}")

# Update checkpointed state as if human_review node made the change
graph.update_state(
    config=config,
    values={
        "final_report": updated_report,
        "human_review_reason": "Reviewed — confirmed critical, affecting peak trading window",
        "requires_human_review": True,
    },
    as_node="human_review",
)

print("\n=== RESUMING AFTER HUMAN REVIEW ===\n")

# Resume from checkpoint with None input
resumed_result = graph.invoke(None, config=config)

print(f"Steps after resume: {resumed_result['steps_taken']}")
print(f"\nFinal state:")
print(f"  Severity: {resumed_result['final_report'].severity.value}")
print(f"  Requires human review: {resumed_result['requires_human_review']}")
print(f"  Auto resolved: {resumed_result.get('auto_resolved', False)}")
print(f"  Human review reason: {resumed_result['human_review_reason']}")
print(f"\nHuman-modified actions:")
for action in resumed_result["final_report"].immediate_actions:
    print(f"  - {action}")
