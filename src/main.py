from clients.llm_client import LLMClient
from config.llm_config import DEFAULT_CONFIG

client = LLMClient(config=DEFAULT_CONFIG)

incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "Checkout latency spiked from 200ms to 4.2s at 6pm Friday. Correlated with promo campaign going live. Cart abandonment up 34%. No errors in logs.",
    "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "Payment processor Stripe returning intermittent 402s for 3% of transactions. No pattern in affected users or card types. Started 40 minutes ago.",
    "Data pipeline from POS systems to data warehouse delayed by 6 hours. Yesterday's sales data not available for morning executive dashboard.",
    "One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved."
]

for incident in incidents:
    print(f"\nIncident: {incident[:60]}...")
    try:
        report = client.triage_incident(incident)
        print(report.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed after max retries: {e}")
    print("---")