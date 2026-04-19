---
doc_id: INCIDENT-009
doc_type: incident_report
team: platform_engineering
incident_family: supply_side
related_runbook: RUNBOOK-005
severity: critical
complexity: complex
resolution_outcome: escalated
duration_minutes: 340
date: 2025-12-11
status: closed
tags: [duplicate-purchase-order, supplier-fulfilled, financial-incident, retry-storm, idempotency, legal]
---

INCIDENT-009: Duplicate Purchase Order — Supplier Already Fulfilled

Incident Summary
A retry storm in the purchase order submission pipeline caused 6 duplicate purchase orders to be submitted to 4 produce suppliers during the morning procurement run on 2025-12-11. The duplication was caused by a supplier API timeout that returned no response — the submission pipeline retried the order without checking whether the original submission had succeeded. Combined duplicate order value was $847,000. Three suppliers had already acknowledged and begun fulfillment preparations for duplicate orders before the issue was detected. Two of those suppliers had perishable goods pre-allocated and could not cancel without financial penalty. Total financial exposure including cancellation fees and excess inventory: approximately $156,000.
Timeline

2025-12-11 08:00 EST — Morning procurement run started
2025-12-11 08:14 EST — Supplier API for primary produce supplier timed out on first submission attempt
2025-12-11 08:14 EST — Retry logic fired — resubmitted order without checking original submission status
2025-12-11 08:14 EST — Both original and retry submission processed by supplier — duplicate created
2025-12-11 08:15 EST — Same pattern repeated for 5 additional orders across 3 other suppliers
2025-12-11 08:30 EST — Procurement run completed — no internal alert fired
2025-12-11 09:45 EST — Supplier 1 called procurement operations to query duplicate order reference
2025-12-11 09:48 EST — Commodity team lead notified
2025-12-11 09:52 EST — Automated PO generation halted immediately
2025-12-11 10:00 EST — All 6 duplicate orders identified via database query
2025-12-11 10:15 EST — Supplier contact initiated for all 4 suppliers simultaneously
2025-12-11 10:30 EST — Supplier 2 confirmed duplicate cancelled — no fulfillment started
2025-12-11 10:45 EST — Supplier 3 confirmed duplicate cancelled — no fulfillment started
2025-12-11 11:00 EST — Supplier 1 confirmed partial fulfillment started — perishables pre-allocated
2025-12-11 11:15 EST — Supplier 4 confirmed fulfillment preparation started — cancellation fee applies
2025-12-11 11:30 EST — Legal team notified — two suppliers with fulfillment exposure
2025-12-11 12:00 EST — Finance team notified — $156,000 exposure estimate
2025-12-11 13:00 EST — VP Commodity and CFO briefed
2025-12-11 14:00 EST — Platform engineering deployed emergency fix — idempotency key added to submission pipeline
2025-12-11 15:00 EST — Fix validated in staging
2025-12-11 15:30 EST — Automated PO generation re-enabled with platform engineering lead sign-off
2025-12-11 16:00 EST — Incident operationally closed — financial reconciliation ongoing

Root Cause
Purchase order submission pipeline had no idempotency key. When a supplier API call timed out with no response, the retry logic resubmitted the order without verifying whether the original submission had been received by the supplier. Both the original and retry requests were processed independently by the supplier system, creating duplicate orders.
Contributing Factors

Idempotency not implemented at API gateway layer — only at application layer for some but not all order types
Retry logic did not check submission status before retrying — assumed timeout meant failure
No duplicate detection job running in real time — daily batch job would have caught this next morning
Procurement run completion did not validate order counts against expected volume
Detection relied on supplier calling us — internal detection would not have fired until next day

Resolution
Emergency deployment of idempotency key to purchase order submission pipeline. Supplier negotiations for cancellation and financial settlement of fulfilled duplicates.
Impact

$847,000 in duplicate purchase orders across 4 suppliers
$156,000 financial exposure after cancellations and fees
2 suppliers with perishable goods pre-allocated — excess inventory received
Excess perishable inventory partially sold via markdown, partially donated
Legal review of supplier contracts for cancellation terms
340 minutes from first duplicate to automated PO generation re-enabled

Follow-up Actions

 Idempotency key implemented at API gateway layer for all PO submissions — completed 2025-12-12
 Real-time duplicate detection job implemented — runs every 15 minutes — completed 2025-12-19
 Implement submission status check before retry — verify original not received before resubmitting — Owner: Platform Engineering — Due: 2026-01-31
 Add PO volume anomaly alert — flag if daily order count exceeds expected by >10% — Owner: Platform Engineering — Due: 2026-01-31
 Legal review of all supplier contracts for cancellation fee terms — document in supplier registry — Owner: Legal — Due: 2026-03-01
 Finance reconciliation of $156,000 exposure — Owner: Finance — Due: 2026-01-15

Related Runbook
RUNBOOK-005
Lessons Learned
Idempotency is not optional for financial transactions. A retry that does not check whether the original succeeded is not a retry — it is a duplicate submission waiting to happen. The cost of implementing idempotency keys is measured in hours of engineering time. The cost of not implementing them is measured in hundreds of thousands of dollars and supplier relationship damage. Detection that relies on suppliers calling you is not detection — it is luck.
