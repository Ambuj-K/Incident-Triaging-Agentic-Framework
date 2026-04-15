---
doc_id: RUNBOOK-002
doc_type: runbook
team: commodity_team
incident_family: supply_side
severity_range: [medium, high, critical]
systems:
  - commodity_price_feed
  - procurement_model
  - purchase_order_system
last_verified: 2026-03-01
last_incident: 2026-01-22
status: active
---

RUNBOOK-002: Commodity Price Feed Failure

Overview
The commodity price feed ingests real-time and futures pricing data for grain, produce, and dairy commodities from external market data providers. This feed drives the procurement model's sourcing decisions including purchase order generation, supplier selection, and contract vs spot market decisions. Stale or missing price data causes procurement model to operate on incorrect assumptions, potentially generating financially significant erroneous purchase orders.
Trigger Conditions

Price feed last update age exceeds 2 hours during market hours (09:00-17:00 IST)
Price feed last update age exceeds 6 hours outside market hours
Commodity price variance >15% from previous close with no market event explanation
Procurement model alert: operating_on_stale_price_data = true
Zero new price records ingested in last feed cycle

Severity Classification

Critical if: feed down during active procurement window AND purchase orders already submitted on stale data
High if: feed down during active procurement window, orders not yet submitted
High if: feed down outside procurement window but orders scheduled within 4 hours
Medium if: feed down outside procurement window, next procurement run >6 hours away
Low if: single commodity category affected, spot price only, futures data intact

Diagnostic Steps

Check feed ingestion pipeline status

Verify feed ingestion job last run time and exit status
Check ingestion logs for connection errors, authentication failures, or malformed data
Verify external market data provider API credentials are valid


Check external provider status

Primary provider status page: [provider URL]
Check if market hours are active — feed intentionally paused outside exchange hours
Verify API rate limits not exceeded


Check price data freshness per commodity

Query: SELECT commodity, max(price_timestamp), count(*) FROM commodity_prices WHERE price_timestamp > now() - interval '4 hours' GROUP BY commodity
Identify which commodity categories are stale vs current
Cross-reference with procurement model's active commodity list


Check procurement model operating status

Verify whether procurement model has flagged stale data internally
Check if any purchase orders have been generated in the stale window
If orders submitted on stale data, treat as Critical regardless of initial classification


Assess financial exposure

Query purchase orders submitted in last 6 hours
Cross-reference order timestamps with feed failure start time
Calculate total order value potentially affected



Resolution Steps

If provider API authentication failure:

Rotate API credentials per security runbook
Restart feed ingestion job
Verify new records appearing within 5 minutes


If provider outage:

Switch to secondary price feed provider if available
If no secondary: pause procurement model automated order generation immediately
Notify procurement team to hold manual orders pending feed restoration
Monitor provider status page for restoration ETA


If purchase orders already submitted on stale data:

Immediately halt further automated order generation
Pull list of potentially affected orders
Contact suppliers to place on hold pending price verification
Notify procurement lead and finance team
This is now a financial incident — escalate immediately regardless of feed status


Feed restoration verification:

Confirm new price records ingesting correctly
Verify price values within expected range (not corrupted)
Run procurement model in simulation mode before re-enabling automated orders
Get procurement lead sign-off before re-enabling automated order generation



Escalation Criteria

Escalate to Procurement Engineering lead immediately if orders submitted on stale data
Escalate to Finance and Procurement VP if financial exposure >$500,000
Escalate to Chief Procurement Officer if exposure >$2,000,000
SLA: Feed must be restored or procurement model paused within 30 minutes of detection

Related Systems

Upstream: External market data providers (primary and secondary)
Downstream: Procurement Model, Purchase Order System, Contract Management System, Finance Reporting
Related runbooks: RUNBOOK-003 (Purchase Order System), RUNBOOK-004 (Procurement Model), RUNBOOK-011 (Supplier API)

Historical Notes

Provider credentials expire every 6 months — most common cause of unexpected feed failures
Market data provider has scheduled maintenance windows first Sunday of each month 02:00-04:00 UTC — expected downtime, not an incident
Wheat and corn futures data arrives 15 minutes delayed vs spot data by design — do not alert on this lag
During major weather events affecting agricultural regions, price volatility can trigger false positive variance alerts — cross-check with weather and news feeds before treating as data quality issue