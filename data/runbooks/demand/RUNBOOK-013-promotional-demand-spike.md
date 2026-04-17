---
doc_id: RUNBOOK-013
doc_type: runbook
team: demand_forecast_team
incident_family: demand_side
severity_range: [medium, high]
systems:
  - ml_forecasting_system
  - promotional_planning_system
  - inventory_management_system
  - replenishment_system
last_verified: 2026-02-25
last_incident: 2026-02-08
status: active
---
RUNBOOK-013: Promotional Demand Spike Not Captured in Forecast

Team: Demand & Sales Forecast Team
Last verified: 2026-02-25
Last incident: 2026-02-08
Status: Active

Overview
Promotional demand spikes occur when a marketing campaign, price promotion, or external event drives demand significantly above the model's baseline forecast. When these spikes are not captured in the forecast model prior to the promotion going live, the replenishment system under-orders promotional SKUs, DCs and stores go out of stock during peak demand, and revenue opportunity is lost. Root causes include promotional calendar not updated in forecast system, campaign details changed after forecast was generated, or model failing to generalize from historical promotional lifts.
Trigger Conditions

Promotional campaign live AND forecast for promotional SKUs not updated from baseline
Actual sales velocity for promotional SKUs >40% above current forecast during campaign window
Replenishment system generating orders based on baseline forecast during active promotion
Store operations reporting stockouts on advertised promotional items
Promotional planning team alert: forecast not updated before campaign launch

Severity Classification

High if: Active promotion with confirmed stockouts across multiple stores or DCs
High if: Campaign launched with no promotional uplift applied to forecast for high-volume SKUs
Medium if: Forecast uplift applied but undersized — actual demand exceeding forecast by 20-40%
Medium if: Stockout risk identified before stockout occurs — time to act
Low if: Minor promotional item, limited store count, stockout impact minimal

Diagnostic Steps

Confirm forecast has not been updated for promotion

Check promotional calendar system for campaign details and SKU list
Query forecast system for promotional SKUs — compare forecast values to baseline
If forecast equals baseline during campaign window: promotional uplift was not applied
Check when last forecast update ran and whether promotional calendar data was available


Assess current inventory position

Query DC and store inventory for all promotional SKUs
Calculate days of supply at actual current sales velocity (not forecast)
Identify which SKUs and locations are at highest stockout risk
Check inbound replenishment orders already placed — when will they arrive


Identify scope of promotional campaign

Get full SKU list from promotional planning team
Get expected promotional lift percentages from historical similar campaigns
Identify campaign duration and affected store/DC locations
Get expected traffic volume from marketing team


Check why forecast was not updated

Was promotional calendar data not available in forecast system at time of last run
Was campaign added after last forecast generation
Did forecast pipeline fail to ingest promotional calendar update
Was promotional uplift model not triggered for this campaign type



Resolution Steps

Immediate demand forecast update:

Manually apply promotional uplift to affected SKUs in forecast system
Use historical promotional lift multipliers for similar campaign types
If no historical data for this campaign type: use conservative 1.5x baseline as starting point
Trigger emergency forecast pipeline run for promotional SKUs only (faster than full pipeline)


Emergency replenishment order generation:

Provide updated forecast to replenishment system immediately
Trigger emergency replenishment order generation for high-risk SKUs
Expedite orders for SKUs with <3 days of supply at actual sales velocity
Coordinate with DC operations on expedited receiving for emergency orders


Supplier coordination:

Contact suppliers for promotional SKUs to increase delivery volumes
Check supplier capacity — can they fulfill increased order on short notice
If primary supplier cannot: check secondary supplier availability
Authorize spot market sourcing for critical promotional SKUs if suppliers cannot respond in time (requires approval per RUNBOOK-011)


Store inventory rebalancing:

If some stores have excess stock while others are at stockout risk: trigger inter-store transfer
Coordinate with store operations and logistics for transfer feasibility
Inter-store transfers require logistics team approval for routes and timing


Prevent recurrence for current campaign:

Implement daily forecast refresh for all promotional SKUs for campaign duration
Set up monitoring alert for actual vs forecast variance >30% on promotional SKUs
Daily review of promotional SKU stock levels by demand planning team for campaign duration



Escalation Criteria

Escalate to Demand Forecast Team lead immediately upon detection
Escalate to VP Merchandising if active stockouts on advertised promotional items
Notify Store Operations lead if customer-facing stockouts confirmed
Notify Marketing team to adjust promotional messaging if stockouts cannot be resolved within 24 hours
SLA: Updated forecast must be in replenishment system within 2 hours of detection. Emergency orders placed within 4 hours.

Related Systems

Upstream: Promotional planning system, marketing calendar, ML demand forecasting model
Downstream: Replenishment system, DC operations, store operations, procurement model
Related runbooks: RUNBOOK-003 (ML Forecast), RUNBOOK-012 (Forecast Pipeline), RUNBOOK-011 (Spot Market), RUNBOOK-001 (Inventory Sync)

Historical Notes

Most common root cause: promotional calendar updated in marketing system after weekly forecast run — forecast system only ingests promotional calendar data at run time, not in real time — real-time promotional calendar sync is on the engineering backlog
Highest risk campaigns: weekly circular promotions and flash sales announced with <48 hours notice — these consistently challenge the forecast update cycle
Historical promotional lifts by category: produce 1.8-2.2x, packaged goods 1.4-1.7x, dairy 1.3-1.5x — use these as starting multipliers when historical data for specific campaign is unavailable
Inter-store transfers have a 6-hour minimum logistics lead time — factor into stockout response timing
Marketing team expects advance notice if stockouts will require promotional messaging change — do not surprise them during campaign
