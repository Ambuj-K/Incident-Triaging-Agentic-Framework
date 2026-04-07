RUNBOOK-004: Supplier API Timeout / Connectivity Failure
Team: Commodity Team
Last verified: 2026-03-01
Last incident: 2026-02-18
Status: Active
Metadata

Runbook ID: RUNBOOK-004
Related runbooks: RUNBOOK-002 (Commodity Price Feed), RUNBOOK-001 (Inventory Sync), RUNBOOK-006 (Futures Contract Feed)
Severity range: medium, high, critical

Overview
Supplier APIs provide real-time delivery schedules, available inventory commitments, pricing confirmations, and order acknowledgements from primary commodity suppliers. These APIs are third-party owned and operated — connectivity failures are outside direct engineering control but have significant downstream impact on procurement decisions, delivery scheduling, and DC inventory planning. Grain, produce, and dairy suppliers each have separate API integrations with different SLAs and fallback behaviors.
Trigger Conditions

Supplier API response time exceeds 10 seconds (normal <500ms)
Supplier API returning 5xx errors for >5% of requests over 10 minute window
Supplier API health check failing: GET /api/v1/health returning non-200
Delivery schedule confirmation requests timing out
Order acknowledgement not received within 2 hours of PO submission
Monitoring alert: supplier_api_last_success_age > 30 minutes

Severity Classification

Critical if: API failure prevents confirmation of orders already submitted AND DC stockout risk within 48 hours for any perishable category
Critical if: All supplier APIs failing simultaneously (suggests internal network issue not supplier-side)
High if: Primary supplier API down for category where DC stock below safety threshold
High if: API failure duration exceeds 2 hours during active procurement window
Medium if: Single supplier API degraded but backup supplier API available
Medium if: API failing outside procurement window, next window >6 hours away
Low if: Intermittent timeouts <5% error rate, orders processing with retries

Diagnostic Steps

Identify scope of failure

Check which supplier APIs are affected: grain, produce, dairy, or all
Check internal API gateway logs for outbound requests to supplier endpoints
Determine if failure is total (no response) or degraded (slow, intermittent)
Check if failure is affecting reads only, writes only, or both


Distinguish internal vs supplier-side failure

Ping supplier API health endpoint directly from multiple internal hosts
Check internal network connectivity and DNS resolution for supplier domains
Check if other external API calls are also failing (suggests internal network issue)
Check supplier status pages if available
If all supplier APIs failing simultaneously: escalate to network/infra team immediately — this is an internal issue not a supplier issue


Check API credentials and rate limits

Verify API keys have not expired (rotation schedule varies by supplier — check credential registry)
Check rate limit headers on recent API responses
Verify IP allowlist has not changed (some suppliers allowlist by IP)


Assess downstream impact

Query pending purchase orders awaiting supplier acknowledgement
Check DC inventory levels for affected commodity categories against safety stock thresholds
Identify delivery schedules due for confirmation in next 24 and 48 hours
Check if procurement model is blocked on supplier confirmation before generating new orders


Check fallback supplier availability

Verify secondary supplier API status for affected categories
Check secondary supplier capacity and pricing for emergency sourcing
Confirm secondary supplier lead times are compatible with stockout risk window



Resolution Steps

If supplier-side outage confirmed:

Contact supplier technical support immediately with incident reference
Switch order routing to secondary supplier if available and capacity permits
Place manual holds on any automated orders pending primary supplier confirmation
Notify commodity team lead and procurement operations of routing switch
Log all manual interventions for audit trail


If internal network or DNS issue:

Escalate to infrastructure team immediately
Do not attempt supplier API workarounds — fix the internal issue first
Pause automated procurement order generation until connectivity restored


If credential or IP allowlist issue:

Rotate credentials per security runbook
Contact supplier to update IP allowlist if required
Test connectivity after each change before resuming order processing


If rate limiting:

Implement request throttling: reduce outbound request frequency by 50%
Batch non-urgent API calls (schedule confirmations, inventory queries) to off-peak window
Contact supplier to discuss rate limit increase if this is recurring


If DC stockout risk is imminent:

This escalates to Critical regardless of API issue root cause
Authorize emergency spot market purchase if secondary supplier unavailable
Requires commodity team lead approval for spot market orders >$100,000
Requires VP Commodity approval for spot market orders >$500,000


Restoration verification:

Confirm API returning 200s with correct response schema
Process one test order acknowledgement before resuming automated flow
Verify delivery schedule data is current and not stale from before outage
Re-enable automated order processing only after commodity team lead sign-off



Escalation Criteria

Escalate to Commodity Team lead immediately if DC stockout risk within 48 hours
Escalate to VP Commodity and Supply Chain if spot market purchase required
Escalate to Infrastructure team if all external APIs failing simultaneously
Escalate to Legal/Contracts if supplier SLA breach threshold reached (check contract for specifics per supplier)
SLA: High severity must have mitigation (secondary supplier or manual hold) within 1 hour. Critical within 30 minutes.

Related Systems

Upstream: Supplier systems (third-party, outside direct control)
Downstream: Procurement Model, Purchase Order System, DC Inventory Planning, Delivery Scheduling System
Related runbooks: RUNBOOK-002 (Commodity Price Feed), RUNBOOK-005 (Duplicate PO Submission), RUNBOOK-001 (Inventory Sync)

Historical Notes

Most common cause: IP allowlist changes on supplier side after their infrastructure updates — they do not always notify in advance
Grain supplier API has known instability during CBOT trading hours (09:30-16:00 US Central) — high volume period, timeouts expected to increase, alert thresholds should be relaxed during this window
Produce supplier API has rate limit of 100 requests/minute — automated order burst during procurement window has hit this twice, implement request queuing
All supplier APIs simultaneously failing has occurred once — was an internal BGP routing issue, not supplier-side, took 3 hours to diagnose because team assumed supplier-side first
Supplier API credentials rotate on different schedules per supplier — maintain a credential expiry calendar, check monthly