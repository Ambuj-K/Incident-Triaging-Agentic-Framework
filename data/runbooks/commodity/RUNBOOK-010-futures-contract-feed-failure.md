---
doc_id: RUNBOOK-010
doc_type: runbook
team: commodity_team
incident_family: supply_side
severity_range: [medium, high, critical]
systems:
  - futures_contract_feed
  - commodity_price_feed
  - procurement_model
  - purchase_order_system
last_verified: 2026-03-01
last_incident: 2026-01-22
status: active
---
RUNBOOK-010: Futures Contract Data Feed Failure

Team: Commodity Team
Last verified: 2026-03-01
Last incident: 2026-01-22
Status: Active

Overview
The futures contract data feed ingests commodity futures pricing from exchange data providers covering wheat, corn, soybean, dairy, and produce indices. Futures data informs procurement model decisions on whether to source via existing contracts, spot market, or new futures positions. Unlike spot price feeds (RUNBOOK-002), futures data covers forward delivery windows of 30, 60, 90, and 180 days. Feed failures cause the procurement model to make sourcing decisions without forward price visibility, increasing financial risk on large volume purchases and long-lead-time commodities.
Trigger Conditions

Futures feed last update age exceeds 4 hours during exchange trading hours
Futures feed last update age exceeds 12 hours outside trading hours
Forward curve data missing for any active commodity contract month
Futures price deviation >20% from previous session close with no market event explanation
Procurement model alert: futures_data_stale = true
Exchange connectivity heartbeat failing

Severity Classification

Critical if: Feed down during active procurement window AND forward contract decisions pending >$1,000,000 value
Critical if: Feed down for >24 hours — procurement model operating without any forward price visibility
High if: Feed down during procurement window, decisions can be deferred <4 hours
High if: Single commodity futures feed down for commodity at seasonal price risk
Medium if: Feed degraded (partial contract months missing) but near-term months current
Medium if: Feed down outside procurement window, next window >8 hours away
Low if: Single non-critical commodity futures data delayed, spot data current

Diagnostic Steps

Identify scope of feed failure

Check which commodity futures feeds are affected: wheat, corn, soy, dairy, produce indices
Check which contract months are missing: near-term (30/60 day) vs far-term (90/180 day)
Verify if spot price feed (RUNBOOK-002) is also affected — simultaneous failure suggests shared infrastructure
Check exchange trading hours — futures data intentionally paused outside trading sessions


Check exchange connectivity

Verify connectivity to primary exchange data provider
Check exchange status page for reported outages or data delays
Verify API credentials and session tokens are valid
Check if exchange has moved to emergency trading mode (affects data format)


Check feed ingestion pipeline

Review ingestion job logs for parsing errors, connection drops, or authentication failures
Check if exchange changed data format or API version without notice
Verify message queue is receiving exchange data — distinguish connectivity failure from processing failure


Check procurement model dependency

Determine which pending procurement decisions depend on futures data
Check forward contract positions currently open and their mark-to-market status
Identify any automatic roll decisions scheduled in next 24 hours


Assess financial exposure

Calculate value of procurement decisions pending futures data
Identify commodities where forward price risk is highest given current market conditions
Check if any hedge positions need adjustment based on delayed futures data



Resolution Steps

If exchange connectivity failure:

Switch to secondary exchange data provider if available
Verify secondary provider covers same contract months and commodities
Notify commodity team lead of provider switch and data quality implications
Contact primary provider support for restoration ETA


If API authentication failure:

Rotate exchange API credentials per security runbook
Note: exchange credential rotation may require exchange-side approval — allow up to 2 hours
Use cached futures curve as read-only reference while credentials are restored


If data format change from exchange:

Do not attempt to parse new format without understanding changes
Contact exchange technical support for format change documentation
Update parser in staging, validate against sample data, deploy
This is a code change — requires standard deployment process


If feed cannot be restored within procurement window:

Switch procurement model to manual approval mode — no automated decisions on futures-dependent orders
Commodity traders to make forward sourcing decisions manually using alternative data sources (Bloomberg, Reuters)
Document all manual decisions with rationale for audit trail
Quantify decisions made without futures data for post-incident financial review


Restoration verification:

Confirm all contract months loading correctly for all active commodities
Verify forward curve shape is consistent with market conditions (no obviously corrupted values)
Run procurement model in simulation mode before re-enabling automated decisions
Commodity team lead sign-off required before resuming automated forward sourcing



Escalation Criteria

Escalate to Commodity Team lead immediately if procurement decisions pending >$500,000
Escalate to Chief Procurement Officer if feed down >24 hours
Escalate to Finance if open hedge positions cannot be monitored
Notify Risk Management team if forward price exposure unmonitored >4 hours
SLA: Manual procurement approval mode must be activated within 1 hour of confirmed feed failure during active procurement window

Related Systems

Upstream: Exchange data providers (primary and secondary), market data aggregators
Downstream: Procurement model, purchase order system, contract management, finance risk reporting
Related runbooks: RUNBOOK-002 (Commodity Price Feed), RUNBOOK-004 (Supplier API), RUNBOOK-011 (Spot Market Emergency Procurement)

Historical Notes

Exchange maintenance windows occur quarterly — check exchange calendar before treating scheduled downtime as incident
Daylight saving time transitions in US and EU markets cause temporary feed timing shifts — not an incident
Near-term contract months (30-day) are most critical for operational procurement — far-term months can tolerate longer delays
Two historical incidents caused by exchange migrating to new API version without adequate notice — subscribe to exchange developer newsletter and review API deprecation notices monthly
Futures data for agricultural commodities is most volatile during USDA crop report releases (monthly) — elevated alert thresholds appropriate on report days
