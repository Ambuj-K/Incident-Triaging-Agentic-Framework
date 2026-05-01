from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState
import json

# Build graph without interrupts for automated testing
graph = build_graph(interrupt_on_human_review=False)

test_cases = [
    {
        "name": "Inventory sync failure — should escalate",
        "incident": "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    },
    {
        "name": "Low severity dashboard — should auto resolve",
        "incident": "One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved.",
    },
    {
        "name": "Empty input — should fail validation",
        "incident": "",
    },
    {
        "name": "Vague input — should escalate due to low confidence",
        "incident": "something seems wrong with the system",
    },
    {
        "name": "ML forecast regression — should escalate",
        "incident": "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    },
]

for case in test_cases:
    print(f"\n{'='*70}")
    print(f"TEST: {case['name']}")
    print(f"{'='*70}")

    initial_state = AgentState(
        incident_description=case["incident"]
    )

    config = {"configurable": {"thread_id": case["name"]}}

    final_state = graph.invoke(initial_state, config=config)

    print(f"Steps taken: {final_state['steps_taken']}")

    if final_state.get("final_report"):
        report = final_state["final_report"]
        print(f"Severity: {report.severity}")
        print(f"Confidence: {report.system_specific_confidence}")
        print(f"Escalate: {report.escalate}")
        print(f"Auto resolved: {final_state.get('auto_resolved', False)}")
        print(f"Requires human review: {final_state.get('requires_human_review', False)}")
    elif final_state.get("validation_error"):
        print(f"Validation error: {final_state['validation_error']}")
    elif final_state.get("error_occurred"):
        print(f"Error: {final_state['error_message']}")

    print()
