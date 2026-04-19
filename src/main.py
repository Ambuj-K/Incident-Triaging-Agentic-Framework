from clients.llm_client import LLMClient
from config.llm_config import DEFAULT_CONFIG
import time
import logging

logging.getLogger("instructor").setLevel(logging.DEBUG)

client = LLMClient(config=DEFAULT_CONFIG)

incidents = [
    "Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
    "Checkout latency spiked from 200ms to 4.2s at 6pm Friday. Correlated with promo campaign going live. Cart abandonment up 34%. No errors in logs.",
    "ML demand forecasting model producing negative values for produce categories since yesterday's model retrain. Downstream procurement orders look wrong but have not been sent yet.",
    "Payment processor Stripe returning intermittent 402s for 3% of transactions. No pattern in affected users or card types. Started 40 minutes ago.",
    "Data pipeline from POS systems to data warehouse delayed by 6 hours. Yesterday's sales data not available for morning executive dashboard.",
    "One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved.",
        # CRITICAL SEVERITY
    "Payment gateway completely down. Zero transactions processing across all channels for the last 8 minutes. All checkout attempts returning 503. Estimated revenue loss $12,000 per minute.",

    "Primary database cluster unresponsive. All services dependent on main DB returning errors. Complete platform outage affecting 100% of users. Failover not triggering automatically.",

    # SUPPLY SIDE
    "Wheat commodity price feed not updating since 6am. Procurement model making sourcing decisions on stale price data. Three purchase orders totaling $2.3M submitted in last 2 hours may be based on incorrect prices.",

    "Primary grain supplier API returning timeouts. Cannot confirm delivery schedules for next week. 14 DC locations at risk of stockout on bread category within 4 days if not resolved.",

    "Automated purchase order system submitted duplicate orders for produce category. Same order sent twice to 6 suppliers. Combined duplicate value approximately $800,000.",

    # DEMAND SIDE
    "Promotional campaign for weekend sale went live but demand forecast was not updated to reflect expected traffic. Forecasting model still using baseline assumptions. Risk of stockouts on promotional SKUs.",

    "Regional demand anomaly detected in northern stores. Flour and rice purchase velocity 340% above forecast with no known external trigger. Pattern started 3 hours ago.",

    # DATA QUALITY
    "Schema change deployed to transactions table in production without migration. Downstream ETL jobs failing with column not found errors. 4 hours of transaction data not ingested into warehouse.",

    "Duplicate records detected in customer transaction table. Estimated 12,000 duplicate rows inserted during last nights batch job. Revenue reporting showing inflated numbers.",

    # EDGE CASES
    "",

    "everything is broken nothing is working please help urgent",

    "System is fully operational and all services are healthy. System is completely down and no services are responding.",

    # SECURITY ADJACENT
    "Unusual bulk data export detected. Single service account downloaded 2.3 million customer records in last 20 minutes. No scheduled job matches this activity.",

    # VAGUE BUT REAL
    "Finance team says the numbers look wrong in the morning report."
]

for incident in incidents:
    print(f"\nIncident: {incident[:60]}...")
    try:
        report = client.triage_incident(incident)
        print(report.model_dump_json(indent=2))
    except Exception as e:
        print(f"Failed after max retries: {e}")
    print("---")
    time.sleep(20)
