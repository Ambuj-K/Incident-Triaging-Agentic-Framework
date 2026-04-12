yaml---
doc_id: INCIDENT-007
doc_type: incident_report
team: platform_engineering
incident_family: data_pipeline
related_runbook: RUNBOOK-007
severity: high
complexity: medium
resolution_outcome: clean
duration_minutes: 112
date: 2025-11-29
status: closed
tags: [pos-feed, black-friday, volume-spike, integration-layer, scaling, replenishment]
---
INCIDENT-007: POS Data Feed Delay — Holiday Period Volume Spike

Incident Summary
POS data feed integration layer became overwhelmed during Black Friday peak trading hours on 2025-11-29. Transaction volume reached 4.2x normal baseline at 14:00 EST, exceeding the integration layer's configured processing capacity. Feed ingestion began falling behind at 13:45 EST and reached a 47-minute lag by 15:30 EST. Integration layer was scaled horizontally at 15:35 EST and lag cleared by 16:37 EST. No data loss occurred as the integration layer queue buffered transactions during the backlog period. Demand forecast team was notified proactively and delayed their afternoon model inference run by 90 minutes to ensure complete data availability.
Timeline

2025-11-29 06:00 EST — Black Friday trading began — transaction volumes above normal from store open
2025-11-29 13:45 EST — Integration layer processing lag first detected — 8 minutes behind
2025-11-29 14:00 EST — Transaction volume peaked at 4.2x normal baseline
2025-11-29 14:15 EST — Monitoring alert fired: pos_feed_last_record_age > 20 minutes
2025-11-29 14:18 EST — Platform engineering on-call acknowledged
2025-11-29 14:25 EST — Integration layer CPU at 94%, memory at 87% — resource saturation confirmed
2025-11-29 14:30 EST — Demand forecast team notified of feed delay proactively
2025-11-29 14:35 EST — Decision made to scale integration layer horizontally
2025-11-29 15:35 EST — Additional integration layer instances provisioned and healthy
2025-11-29 15:40 EST — Processing lag began reducing
2025-11-29 16:37 EST — Feed lag fully cleared — integration layer current
2025-11-29 16:45 EST — Demand forecast team notified feed current — inference run resumed
2025-11-29 17:30 EST — Incident closed after 45 minute stability monitoring period

Root Cause
Integration layer was not pre-scaled for Black Friday volume. Capacity planning exercise conducted in October 2025 identified 3x scaling requirement for Black Friday. Actual volume reached 4.2x — 40% above the planned scaling target. Pre-scaling action item from October planning was assigned to the team but not completed before the event.
Contributing Factors

Pre-scaling action item from October capacity planning not completed
Historical Black Friday volume underestimated — 2024 actual volume was 3.1x, 2025 was 4.2x (35% year-over-year growth not accounted for)
No automated pre-scaling policy for known high-volume events
Scaling took 60 minutes from decision to healthy instances — too slow for real-time event response

Resolution
Horizontal scaling of integration layer. Queue buffered all transactions during backlog — no data loss. Feed lag cleared within 57 minutes of scaling completion.
Impact

112 minutes from first lag detection to feed current
47 minutes maximum feed lag at peak
No data loss — queue buffered all transactions
Demand forecast inference run delayed 90 minutes — no replenishment impact as orders not due until following morning
No customer-facing impact

Follow-up Actions

 Implement automated pre-scaling policy for integration layer on known high-volume event dates — completed 2025-12-15
 Update capacity planning model to include year-over-year growth factor — Owner: Platform Engineering — Due: 2026-01-31
 Reduce scaling time from 60 minutes to <15 minutes using pre-warmed instance pool — Owner: Infrastructure — Due: 2026-03-31
 Add integration layer queue depth monitoring as leading indicator — alert at 15 minute lag not 20 — Owner: Platform Engineering — Due: 2026-01-15

Related Runbook
RUNBOOK-007
Lessons Learned
Capacity planning for known events must include year-over-year growth projections not just historical actuals. A system that handled 3.1x last year needs to be planned for 4x this year at minimum. Pre-scaling must be completed and verified before the event — an action item that misses its deadline due to competing priorities directly caused this incident. Automated pre-scaling policies remove the human dependency from known scaling events.