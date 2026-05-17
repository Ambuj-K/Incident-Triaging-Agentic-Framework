import warnings
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

import time
from dotenv import load_dotenv
load_dotenv()

from incident_triage.pipeline.triage_pipeline import TriagePipeline
from incident_triage.config.llm_config import DEFAULT_CONFIG

pipeline = TriagePipeline(config=DEFAULT_CONFIG)

test_incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "ML demand forecasting model producing negative values for produce categories since yesterday retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "One internal reporting dashboard loading slowly for a single analyst. No other users affected.",
]

print("Measuring cost per investigation...\n")

for incident in test_incidents:
    pipeline.llm_client.reset_usage()

    result = pipeline.run(incident)

    stats = pipeline.llm_client.get_usage_stats()
    print(f"Incident: {incident[:60]}...")
    print(f"  Calls:         {stats['total_calls']}")
    print(f"  Input tokens:  {stats['total_input_tokens']}")
    print(f"  Output tokens: {stats['total_output_tokens']}")
    print(f"  Total tokens:  {stats['total_tokens']}")
    print(f"  Est. cost:     ${stats['estimated_cost_usd']:.6f}")
    print()
    time.sleep(15)

print("At scale:")
avg_tokens = 3000
cost_per = avg_tokens * 0.10 / 1_000_000
print(f"  1,000 investigations/day:  ${cost_per * 1000:.2f}/day")
print(f"  10,000 investigations/day: ${cost_per * 10000:.2f}/day")
