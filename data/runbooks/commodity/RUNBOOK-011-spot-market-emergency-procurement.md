---
doc_id: RUNBOOK-011
doc_type: runbook
team: commodity_team
incident_family: supply_side
severity_range: [high, critical]
systems:
  - procurement_model
  - purchase_order_system
  - supplier_integration_api
  - inventory_management_system
last_verified: 2026-02-20
last_incident: 2026-02-01
status: active
---
RUNBOOK-011: Spot Market Emergency Procurement

Team: Commodity Team
Last verified: 2026-02-20
Last incident: 2026-02-01
Status: Active

Overview
Spot market emergency procurement is activated when normal supply channels fail and DC stockout is imminent for critical commodity categories. Triggers include primary supplier failure, commodity price feed failures that blocked normal procurement, duplicate order cancellations leaving supply gaps, or unexpected demand spikes exceeding contracted supply. Spot market purchases are typically at premium prices (10-40% above contract rates) and require elevated approval thresholds due to financial exposure. This runbook covers both the decision process and the operational steps for emergency sourcing.
Trigger Conditions

DC inventory below critical safety stock threshold for any staple commodity category
Primary and secondary supplier both unable to confirm delivery within required window
Procurement model blocked from generating orders due to data feed failure
Duplicate order cancellation creating supply gap within 72 hour stockout window
Demand forecast showing stockout probability >70% within 5 days for any DC
Manual trigger by Commodity Team lead or VP Commodity

Severity Classification

Critical if: Stockout probability >90% within 48 hours for staple category (bread, rice, flour, dairy)
Critical if: Multiple DCs simultaneously at stockout risk for same category
High if: Stockout probability >70% within 72 hours, single DC
High if: Primary supplier confirmed unable to deliver, secondary supplier lead time borderline
Medium if: Supply risk identified >7 days out, time available for standard procurement process

Diagnostic Steps

Confirm stockout risk

Query current DC inventory levels for affected categories
Query: SELECT dc_location, sku_category, current_stock_units, safety_stock_units, days_of_supply FROM dc_inventory WHERE days_of_supply < 5 AND category IN ('staple_categories')
Verify demand forecast for affected category and DCs over next 7 days
Confirm that normal supply channels cannot meet gap within required timeframe


Assess supply gap size

Calculate units required to bring affected DCs to 7-day safety stock level
Convert to commodity weight or volume for spot market sourcing
Identify which DCs are highest priority based on days of supply remaining


Check secondary supplier capacity

Verify secondary supplier can supply required volume within stockout window
Confirm secondary supplier pricing — note premium vs contract rate for approval
If secondary supplier also cannot meet requirement: proceed to spot market


Identify spot market options

Commodity traders to identify available spot market sources
Check commodity exchange for available physical delivery contracts
Contact spot market brokers for immediate availability and pricing
Compare spot market pricing to contract rates and document premium


Calculate financial exposure

Total spot market purchase value
Premium over contract rate in absolute terms
Cost of stockout scenario if spot market not activated (lost sales, customer impact)
Present both options to approving authority



Resolution Steps

Approval process (mandatory before any spot market purchase):

<$100,000: Commodity Team lead approval
$100,000-$500,000: VP Commodity approval required


$500,000: Chief Procurement Officer approval required




$2,000,000: CFO approval required


Document approval in procurement system with approver name, timestamp, and rationale


Execute spot market purchase:

Create manual purchase order in procurement system with type: EMERGENCY_SPOT
Flag order with stockout incident reference number
Confirm delivery logistics — spot market suppliers may require different DC receiving arrangements
Notify DC operations teams of incoming emergency delivery with estimated arrival


Update inventory planning:

Notify demand forecast team of emergency procurement to prevent double-ordering
Update inventory system with expected spot market delivery to adjust replenishment calculations
Flag affected SKUs for manual review until normal supply chain restored


Address root cause of supply gap:

If caused by supplier failure: follow RUNBOOK-004 (Supplier API) for supplier restoration
If caused by procurement model failure: follow relevant runbook for model restoration
If caused by demand spike: notify demand forecast team for model update
Document root cause in incident report for procurement process review


Post-incident financial reconciliation:

Calculate total premium paid over contract rates
Submit financial impact report to Finance and CPO within 48 hours
Review whether supply chain resilience investment (secondary supplier capacity, safety stock levels) is adequate



Escalation Criteria

Escalate to VP Commodity immediately upon activation of this runbook
Escalate to CFO if total emergency procurement value >$2,000,000
Notify Finance team of any spot market purchase >$100,000 within 1 hour
Notify Store Operations of any category where stockout cannot be fully prevented
SLA: Approval and order placement must be completed within 2 hours of stockout risk confirmation

Related Systems

Upstream: Inventory management, demand forecasting, procurement model, supplier APIs
Downstream: DC operations, store operations, finance reporting, customer availability
Related runbooks: RUNBOOK-002 (Commodity Price Feed), RUNBOOK-004 (Supplier API), RUNBOOK-010 (Futures Feed), RUNBOOK-005 (Duplicate PO)

Historical Notes

Both historical activations were during weather events affecting regional agricultural supply — maintain pre-approved spot market broker relationships for top 5 commodity categories
Spot market price premium has ranged from 12% to 38% above contract rates in historical incidents — factor this range into stockout cost-benefit analysis
DC receiving teams need 4 hours notice minimum for non-standard deliveries — factor into spot market lead time calculations
Finance team requires spot market purchases to be categorized separately in reporting — ensure EMERGENCY_SPOT order type is used consistently
Post-incident reviews have consistently recommended higher safety stock levels for staple categories during weather risk seasons — this recommendation has not yet been fully implemented
