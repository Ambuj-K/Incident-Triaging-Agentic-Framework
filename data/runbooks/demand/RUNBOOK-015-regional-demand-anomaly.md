---
doc_id: RUNBOOK-015
doc_type: runbook
team: demand_forecast_team
incident_family: demand_side
severity_range: [medium, high]
systems:
  - ml_forecasting_system
  - sales_systems
  - inventory_management_system
  - replenishment_system
last_verified: 2026-03-01
last_incident: 2026-01-18
status: active
---

RUNBOOK-015: Regional Demand Anomaly With No Known Trigger
Team: Demand & Sales Forecast Team
Last verified: 2026-03-01
Last incident: 2026-01-18
Status: Active

Overview
Regional demand anomalies occur when sales velocity in a specific geographic area deviates significantly from forecast without a known promotional, seasonal, or operational explanation. Causes include unreported local events (natural disasters, civil events, health scares), competitor store closures driving demand to our locations, data quality issues producing false signals, or emerging demand patterns the model has not yet learned. The challenge is distinguishing genuine demand signals requiring supply chain response from data artifacts requiring correction. Acting on a false signal is costly. Missing a genuine signal causes stockouts.
Trigger Conditions

Regional sales velocity >50% above or below forecast for same-day-of-week historical baseline
Anomaly persists for >2 consecutive hours without known explanation
Multiple SKU categories showing simultaneous anomaly in same region (suggests genuine demand, not data issue)
Single SKU category anomaly in isolation (suggests possible data quality issue)
Store operations reporting unusual customer traffic patterns
Social media or news monitoring flagging events in affected region

Severity Classification

High if: Anomaly >100% above forecast AND multiple categories AND inventory risk within 48 hours
High if: Anomaly confirmed as genuine demand with stockout risk for staple categories
Medium if: Anomaly >50% but <100% above forecast, cause under investigation
Medium if: Anomaly is downward (demand drop) — less urgent but needs investigation for overstock risk
Low if: Anomaly in single non-staple category, <50% deviation, likely data artifact

Diagnostic Steps

Validate data integrity first — rule out false signal before acting

Check POS data feed health for affected region (RUNBOOK-007)
Verify transaction counts are plausible — sudden spike may be duplicate records
Check if similar anomaly appeared in same region at same time last year (seasonal pattern)
Check if store count in region changed recently (new store opening, competitor closure)
Run duplicate transaction check for affected region and time window


Check for known external triggers

Check internal promotional calendar — is there an untracked promotion in this region
Check external event calendar: local festivals, sporting events, political events
Check weather forecast for region: extreme weather drives demand for staples
Check local news for events that would explain buying behavior (health scare, emergency)
Check competitor intelligence: store closures in area divert demand to our locations


Assess anomaly pattern

Which SKU categories are affected: staples only, broad categories, or single category
Which stores or DCs are affected: contiguous geographic cluster or scattered
How long has anomaly been running and is it accelerating, stable, or decelerating
Contiguous geographic cluster with multiple categories strongly suggests genuine demand event


Assess inventory risk

Check current inventory levels for affected SKUs in affected DCs and stores
Calculate days of supply at anomalous sales velocity
Identify which SKUs will reach critical stock levels first


Escalate or investigate based on findings

If data integrity issue confirmed: fix data, no supply chain response needed
If genuine demand confirmed: proceed to resolution steps
If uncertain after 2 hours: treat as genuine demand and activate precautionary response



Resolution Steps

If data quality issue confirmed:

Quarantine affected transaction records
Fix data pipeline issue per RUNBOOK-006 or RUNBOOK-007
Reprocess clean data and verify anomaly disappears in reporting
Document false positive in incident report for model training purposes


If genuine demand surge confirmed:

Update demand forecast for affected region and SKUs immediately
Apply demand surge multiplier based on observed velocity vs forecast
Trigger emergency replenishment orders for high-risk SKUs per RUNBOOK-013 process
Notify commodity team if surge affects commodity-sourced categories


If cause is unknown but demand appears genuine:

Apply precautionary forecast uplift of 1.3x for affected categories
Increase replenishment order frequency to daily for affected region until pattern resolves
Assign demand analyst to monitor region hourly for next 48 hours
Escalate to regional store operations for ground-level intelligence gathering


If downward anomaly (demand drop):

Pause replenishment orders for affected SKUs in affected region
Check for overstock risk — if significant inventory in transit, can deliveries be redirected
Investigate cause: store access issues, local economic event, competitor promotion
Do not adjust forecast downward until cause is understood — may be temporary


Model learning:

Document anomaly event, cause (if identified), and magnitude in event registry
Event registry feeds into model as external signal for future similar events
If cause was a recurring event type (annual festival, seasonal weather pattern): update model feature set to include this signal



Escalation Criteria

Escalate to Demand Forecast Team lead if anomaly confirmed genuine and stockout risk within 48 hours
Escalate to Regional Operations lead for ground-level intelligence on unknown causes
Notify Commodity Team if staple category demand affected
Escalate to VP Supply Chain if anomaly affects multiple regions simultaneously
SLA: Data integrity vs genuine demand determination must be made within 2 hours of detection. Supply chain response within 4 hours if genuine.

Related Systems

Upstream: POS systems, sales reporting, external event feeds, weather data
Downstream: Replenishment system, DC inventory planning, procurement model, store operations
Related runbooks: RUNBOOK-003 (ML Forecast), RUNBOOK-007 (POS Feed), RUNBOOK-013 (Promotional Demand), RUNBOOK-012 (Forecast Pipeline)

Historical Notes

Both confirmed genuine anomalies in history were weather events — heavy rainfall driving pantry-loading behavior for staples — weather data feed integration with demand model is the highest value feature addition for this incident type
False positive rate historically 40% — nearly half of regional anomaly alerts are data quality issues not genuine demand — always validate data integrity before activating supply chain response
The 2-hour investigation window before defaulting to precautionary response has been validated in post-incident reviews — do not extend this window under pressure to be certain
Downward anomalies have been more difficult to diagnose than upward ones historically — store operations ground intelligence has been the most reliable signal for downward anomalies
Social media monitoring has identified regional event triggers 30 minutes faster than internal detection in two historical incidents — integrate social monitoring alert into this runbook trigger