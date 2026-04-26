from incident_triage.pipeline.triage_pipeline import TriagePipeline
from incident_triage.config.llm_config import DEFAULT_CONFIG
import json

pipeline = TriagePipeline(config=DEFAULT_CONFIG)

test_incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "Payment processor Stripe returning intermittent 402s for 3% of transactions. No pattern in affected users or card types. Started 40 minutes ago.",
]

for incident in test_incidents:
    print(f"\n{'='*70}")
    print(f"INCIDENT: {incident[:70]}...")
    print(f"{'='*70}")

    result = pipeline.run(incident, verbose=True)

    print("\n[FINAL REPORT]")
    print(result["final_report"].model_dump_json(indent=2))
    print()
