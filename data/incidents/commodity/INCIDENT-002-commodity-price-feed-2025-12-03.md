---
doc_id: INCIDENT-002
doc_type: incident_report
team: commodity_team
incident_family: supply_side
related_runbook: RUNBOOK-002
severity: critical
complexity: complex
resolution_outcome: escalated
duration_minutes: 187
date: 2025-12-03
status: closed
tags: [commodity-price-feed, procurement-model, stale-data, financial-incident, purchase-orders]
---

INCIDENT-002: Commodity Price Feed — Orders Submitted on Stale Data

Incident Summary
External commodity price feed provider API credentials expired at 06:00 IST. Feed ingestion silently failed — no alert fired because the ingestion job returned exit code 0 despite writing zero records. Procurement model continued operating on 19-hour-old price data. Three automated purchase orders totaling $1.84M were submitted to grain suppliers between 08:00 and 10:30 IST based on stale pricing. Feed failure detected at 10:47 IST by commodity analyst who noticed flat price curves in dashboard. Two of three orders were placed on hold with suppliers. One order ($340,000) was acknowledged and partially fulfilled before hold was applied. Financial exposure from price discrepancy: approximately $67,000.
Timeline

06:00 IST — API credentials expired, feed ingestion job started failing silently
06:15 IST — Ingestion job completed with exit code 0, zero records written — no alert fired
08:00 IST — Procurement model morning run began using 19-hour-old price data
08:34 IST — First purchase order ($620,000 wheat) submitted to primary grain supplier
09:12 IST — Second purchase order ($780,000 corn) submitted
10:05 IST — Third purchase order ($440,000 soy) submitted
10:47 IST — Commodity analyst noticed flat price curves in dashboard — raised concern
10:52 IST — Feed failure confirmed — last actual data timestamp 11:00 IST previous day
10:55 IST — Procurement model automated order generation halted immediately
11:03 IST — Commodity team lead notified — escalated to financial incident
11:15 IST — Supplier contacted for order 1 (wheat) — placed on hold pending price review
11:22 IST — Supplier contacted for order 2 (corn) — placed on hold
11:31 IST — Supplier contacted for order 3 (soy) — partial fulfillment already initiated, $340,000 committed
12:20 IST — API credentials rotated, feed ingestion restored
12:35 IST — Fresh price data confirmed loading correctly
13:10 IST — Procurement model simulation run with correct prices
13:45 IST — Procurement model re-enabled with commodity team lead sign-off
15:00 IST — Finance team notified of $67,000 price discrepancy exposure on partially fulfilled order
17:00 IST — Incident closed pending finance reconciliation

Root Cause
API credentials expired on schedule (every 6 months) but credential rotation reminder was not actioned. The critical secondary failure was the ingestion job returning exit code 0 despite writing zero records — the job treated an authentication failure as a successful empty run, suppressing any alert.
Contributing Factors

No monitoring on records written per ingestion cycle — only job exit code monitored
Credential rotation calendar reminder sent to a team distribution list — no individual owner
Procurement model had no stale data guard — operated on any available data regardless of age
19 hours of stale data before detection is an unacceptably long detection lag

Resolution
Rotated API credentials. Restored feed ingestion. Ran procurement model in simulation mode. Re-enabled automated ordering after commodity team lead verified price data was current and order values were within expected range.
Impact

$1.84M in purchase orders generated on stale price data
$340,000 order partially fulfilled before hold applied
Estimated $67,000 financial exposure from price discrepancy
187 minutes from feed failure to incident detection
2 hours 50 minutes from detection to feed restoration

Follow-up Actions

 Add records-written monitoring to feed ingestion job — alert if zero records written — completed 2025-12-10
 Assign individual owner to credential rotation reminders — no distribution list ownership — completed 2025-12-05
 Add stale data guard to procurement model — halt automated orders if price data age >4 hours — Owner: Commodity Engineering — Due: 2026-01-31
 Implement pre-order price sanity check — flag orders where price deviates >10% from 7-day average — Owner: Commodity Engineering — Due: 2026-01-31
 Finance reconciliation of $67,000 exposure — Owner: Finance — Due: 2026-01-15

Related Runbook
RUNBOOK-002
Lessons Learned
Exit code monitoring is insufficient for data pipelines. A job that runs successfully but writes nothing is worse than a job that fails visibly — it creates false confidence. Every data pipeline needs output volume monitoring alongside job status monitoring. Silent failures are the hardest failures to catch.
