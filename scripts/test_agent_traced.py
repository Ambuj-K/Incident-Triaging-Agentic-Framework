import warnings
warnings.filterwarnings(
    "ignore",
    message=".*Deserializing unregistered type.*",
)

from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState
from incident_triage.observability.tracer import get_langfuse

graph = build_graph(interrupt_on_human_review=False)
lf = get_langfuse()

test_incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved.",
]

import time

for incident in test_incidents:
    print(f"\nIncident: {incident[:60]}...")

    # Create top-level trace for this investigation
    trace = lf.trace(
        name="incident_investigation",
        input={"incident": incident},
        metadata={"source": "test_script"},
    )

    config = {
        "configurable": {
            "thread_id": f"trace-test-{hash(incident)}"
        }
    }

    initial_state = AgentState(incident_description=incident)
    result = graph.invoke(initial_state, config=config)

    # Update trace with final outcome
    trace.update(
        output={
            "severity": result["final_report"].severity.value if result.get("final_report") else "unknown",
            "auto_resolved": result.get("auto_resolved", False),
            "requires_human_review": result.get("requires_human_review", False),
            "consistency_flags": result.get("consistency_flags", []),
            "steps_taken": result.get("steps_taken", []),
        }
    )

    print(f"  Severity: {result['final_report'].severity.value if result.get('final_report') else 'unknown'}")
    print(f"  Auto resolved: {result.get('auto_resolved', False)}")
    print(f"  Human review: {result.get('requires_human_review', False)}")
    print(f"  Trace ID: {trace.id}")

    lf.flush()
    time.sleep(15)

print("\nCheck your Langfuse dashboard for traces.")
