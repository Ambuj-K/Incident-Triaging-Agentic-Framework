---
doc_id: INCIDENT-004
doc_type: incident_report
team: commodity_team
incident_family: supply_side
related_runbook: RUNBOOK-004
severity: high
complexity: complex
resolution_outcome: partial
duration_minutes: 143
date: 2026-02-18
status: closed
tags: [supplier-api, grain-supplier, timeout, delivery-schedule, root-cause-unknown]
---

INCIDENT-004: Supplier API Timeout — Root Cause Never Fully Determined

Incident Summary
Primary grain supplier API began returning timeouts at 14:30 EST. Delivery schedule confirmations for 14 DC locations could not be processed. Secondary supplier API was available but had insufficient capacity to cover the full shortfall. Issue self-resolved at 17:00 EST when supplier API returned to normal response times. Root cause was never definitively confirmed — supplier technical team attributed it to internal infrastructure maintenance but provided no detailed RCA. One DC location (Wiltfordshire) was unable to get delivery confirmation within the required window and required a manual delivery arrangement.
Timeline

14:30 EST — Grain supplier API response times began increasing (800ms vs normal 300ms)
14:45 EST — API response times exceeded 10 second timeout threshold — automated retries beginning
14:52 EST — Monitoring alert fired: supplier_api_last_success_age > 30 minutes
14:55 EST — On-call commodity engineer began investigation
15:05 EST — Supplier status page checked — no reported incidents
15:10 EST — Internal network connectivity confirmed healthy — issue isolated to supplier side
15:15 EST — Supplier technical support contacted via phone
15:20 EST — Secondary supplier API confirmed available — capacity check initiated
15:35 EST — Secondary supplier confirmed can cover 11 of 14 DC delivery requirements
15:40 EST — 11 DC delivery confirmations rerouted to secondary supplier
15:55 EST — Wiltfordshire DC identified as unable to be covered by secondary supplier (capacity constraint)
16:10 EST — Commodity team lead authorized manual delivery arrangement for Wiltfordshire DC
16:30 EST — Manual delivery arrangement confirmed with regional logistics team
17:00 EST — Primary grain supplier API returned to normal response times
17:15 EST — Delivery confirmations for remaining 3 DCs processed via primary supplier
17:13 EST — Incident closed

Root Cause
Not definitively determined. Primary grain supplier attributed the degradation to internal infrastructure maintenance. No formal RCA was provided by supplier. Internal investigation found no evidence of rate limiting, credential issues, or network problems on our side.
Contributing Factors

Supplier did not proactively notify of planned maintenance
No pre-established SLA with supplier for API availability during business hours
Secondary supplier capacity insufficient to fully cover primary supplier failover
Wiltfordshire DC had tighter delivery window than other DCs — less tolerance for delay

Resolution
Rerouted 11 of 14 DC delivery confirmations to secondary supplier. Manual delivery arrangement for 1 DC. Remaining 3 DCs processed via primary supplier after self-resolution.
Impact

143 minutes of degraded primary supplier API
11 DC delivery confirmations delayed 60-90 minutes
1 DC required manual delivery arrangement
No stockouts resulted
No financial impact

Follow-up Actions

 Negotiate API availability SLA with primary grain supplier — include in contract renewal — Owner: Commodity Procurement Lead — Due: 2026-06-01
 Increase secondary supplier contracted capacity to 100% primary supplier coverage — Owner: VP Commodity — Due: 2026-04-30
 Request post-incident RCA from supplier in writing — Owner: Commodity Team Lead — Due: 2026-03-01
 Add Wiltfordshire DC to priority list for delivery window flexibility negotiation — Owner: Logistics — Due: 2026-04-01

Related Runbook
RUNBOOK-004
Lessons Learned
Not all incidents have knowable root causes. When supplier systems are involved, you are dependent on their transparency and RCA quality. The more important lesson is capacity planning for failover — secondary supplier at 78% coverage is not a true failover. Full coverage requires either secondary supplier at 100% capacity or a tertiary option. This incident was low impact because demand was normal — during a demand surge this gap would have caused stockouts.
