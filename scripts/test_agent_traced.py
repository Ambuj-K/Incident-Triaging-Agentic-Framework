import warnings
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

import os
import time
from dotenv import load_dotenv
load_dotenv()

os.environ["LANGFUSE_PUBLIC_KEY"] = os.environ["LANGFUSE_PUBLIC_KEY"]
os.environ["LANGFUSE_SECRET_KEY"] = os.environ["LANGFUSE_SECRET_KEY"]
os.environ["LANGFUSE_HOST"] = os.environ["LANGFUSE_HOST"]

from langfuse import observe, langfuse_context
from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState

graph = build_graph(interrupt_on_human_review=False)


@observe(name="incident_investigation")
def run_investigation(incident: str, thread_id: str):
    langfuse_context.update_current_trace(
        input={"incident": incident},
        metadata={"source": "test_script"},
    )

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = AgentState(incident_description=incident)
    result = graph.invoke(initial_state, config=config)

    if result.get("final_report"):
        langfuse_context.update_current_trace(
            output={
                "severity": result["final_report"].severity.value,
                "auto_resolved": result.get("auto_resolved", False),
                "requires_human_review": result.get("requires_human_review", False),
                "consistency_flags": result.get("consistency_flags", []),
            }
        )

    return result


test_incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved.",
]

for incident in test_incidents:
    print(f"\nIncident: {incident[:60]}...")
    result = run_investigation(
        incident=incident,
        thread_id=f"trace-test-{hash(incident)}",
    )
    if result.get("final_report"):
        print(f"  Severity: {result['final_report'].severity.value}")
        print(f"  Auto resolved: {result.get('auto_resolved', False)}")
        print(f"  Human review: {result.get('requires_human_review', False)}")
    time.sleep(15)

print("\nCheck your Langfuse dashboard for traces.")
