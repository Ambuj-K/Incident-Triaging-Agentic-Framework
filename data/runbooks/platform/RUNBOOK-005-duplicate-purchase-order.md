---
doc_id: RUNBOOK-005
doc_type: runbook
team: platform_engineering
incident_family: supply_side
severity_range: [high, critical]
systems:
  - purchase_order_system
  - procurement_model
  - supplier_integration_api
  - finance_reporting
last_verified: 2026-02-20
last_incident: 2025-12-11
status: active
---

RUNBOOK-005: Duplicate Purchase Order Submission
Team: Platform Engineering (Purchase Order System ownership) with Commodity Team notification
Last verified: 2026-02-20
Last incident: 2025-12-11
Status: Active
Metadata

Runbook ID: RUNBOOK-005
Related runbooks: RUNBOOK-002 (Commodity Price Feed), RUNBOOK-004 (Supplier API), RUNBOOK-003 (ML Forecast)
Severity range: high, critical

Overview
Duplicate purchase order submission occurs when the automated purchase order system submits the same order more than once to one or more suppliers. Root causes include idempotency failures in the PO submission pipeline, retry logic misfiring after a timeout, message queue double-delivery, or operator error in manual order submission workflows. Financial exposure scales directly with order value and number of affected suppliers. This incident requires immediate containment to prevent suppliers from fulfilling duplicate orders and issuing invoices.
Trigger Conditions

Duplicate PO detection job alert: same PO reference submitted >1 time within 24 hour window
Supplier callback received for PO reference already marked as acknowledged
Finance team reports unexpected invoice from supplier for order not in system
Procurement operations reports supplier querying duplicate order
Automated PO volume exceeds expected daily threshold by >20%
Message queue consumer lag spike followed by sudden processing burst

Severity Classification

Critical if: duplicate orders submitted to multiple suppliers AND combined value >$500,000
Critical if: suppliers have already confirmed duplicate orders (fulfillment may have started)
High if: duplicate orders submitted, suppliers not yet confirmed, combined value >$100,000
High if: duplicate orders submitted for perishable category (time-sensitive cancellation window)
Medium if: single supplier, low value (<$50,000), order not yet confirmed
Low if: duplicate detected in staging/test environment only, no production orders affected

Diagnostic Steps

Confirm and scope the duplication

Query PO system for duplicate reference numbers: SELECT po_reference, count(*) FROM purchase_orders WHERE created_at > now() - interval '24 hours' GROUP BY po_reference HAVING count(*) > 1
Identify affected suppliers, commodity categories, and total order value
Check order status for each duplicate — pending, acknowledged, or fulfillment started


Identify root cause category

Check PO submission pipeline logs for the time window of duplicate submission
Check message queue (Kafka/RabbitMQ) for duplicate message delivery — consumer group offsets
Check if a retry storm occurred — timed-out submission that was retried after the original succeeded
Check if manual submission was also run alongside automated submission for same order
Check if idempotency key was missing, null, or incorrectly generated


Check supplier confirmation status

For each affected supplier, check acknowledgement status via supplier API
If supplier has confirmed: treat as Critical, fulfillment may have started
If supplier has not confirmed: containment window is open, move to resolution immediately


Assess financial exposure

Calculate total value of duplicate orders
Check if duplicate orders are for contract-priced commodities or spot market
Check contract terms for cancellation fees if applicable
Notify finance team with exposure estimate immediately regardless of resolution status


Check for systemic vs isolated failure

Was this a single order duplicated or multiple orders affected?
Is the PO submission pipeline still running? If yes, is it still producing duplicates?
If systemic: halt automated PO generation immediately before continuing diagnosis



Resolution Steps

Immediate containment (do before root cause investigation if exposure is high):

Halt automated purchase order generation pipeline
Place system-level hold on outbound API calls to affected suppliers
This stops the bleeding — do not skip this step to investigate first if value is >$100,000


Contact affected suppliers:

Call supplier account manager directly — do not rely on API or email for time-sensitive cancellation
Provide duplicate PO reference numbers and request cancellation of duplicate orders
Get written confirmation of cancellation from each supplier
If supplier has already started fulfillment: escalate to Commodity Team lead and Legal immediately


Mark duplicates in system:

Flag duplicate PO records with status: DUPLICATE_CANCELLED or DUPLICATE_SUPPLIER_NOTIFIED
Do not delete records — maintain full audit trail
Link duplicate records to original order with relationship type DUPLICATE_OF


Fix root cause before re-enabling:

If idempotency key failure: patch and deploy fix before resuming
If retry storm: implement exponential backoff and max retry cap, deploy before resuming
If message queue double-delivery: investigate consumer group offset reset, fix before resuming
If manual + automated overlap: implement submission lock that prevents both running simultaneously
Each root cause requires a code fix and deployment — do not resume automated PO generation on the same code that produced duplicates


Re-enable with verification:

Process one test order through the fixed pipeline in staging
Confirm idempotency: submit same order twice deliberately, verify only one PO created
Get platform engineering lead sign-off before re-enabling production
Monitor first 10 orders after re-enable manually


Post-incident:

File postmortem within 24 hours
Update duplicate detection job thresholds if they failed to catch this early enough
Review all supplier invoices for the period to ensure no duplicate invoices were generated



Escalation Criteria

Escalate to Platform Engineering lead immediately upon detection
Escalate to Commodity Team lead immediately — they manage supplier relationships
Escalate to Finance VP if financial exposure >$500,000
Escalate to Legal if supplier has started fulfillment of duplicate order
Escalate to CPO if total exposure >$2,000,000
SLA: Containment (halt pipeline + supplier notification) within 30 minutes of detection regardless of severity

Related Systems

Upstream: Procurement Model (generates order requests), ML Demand Forecast (drives order quantities), Commodity Price Feed (drives order pricing)
Downstream: Supplier systems, Finance invoicing, DC receiving, Inventory Management
Related runbooks: RUNBOOK-004 (Supplier API), RUNBOOK-002 (Commodity Price Feed), RUNBOOK-001 (Inventory Sync)

Historical Notes

Both historical occurrences were caused by retry logic firing after a supplier API timeout — the original request succeeded but response was lost, retry submitted a second order without checking if first succeeded. Idempotency key on PO reference is the fix but must be enforced at the API gateway layer not just application layer
Perishable category duplicates are highest risk — produce suppliers start fulfillment within hours of acknowledgement, cancellation window is very short
Finance team has a duplicate invoice detection job that runs nightly — this has caught duplicate POs that the PO system missed twice. Cross-check with finance team if suspecting systemic issue
One occurrence was caused by a manual resubmission by a procurement analyst who did not know the automated system had already submitted — implement submission status visibility in the procurement operations dashboard to prevent this
