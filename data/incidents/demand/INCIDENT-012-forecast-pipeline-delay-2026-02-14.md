yaml---
doc_id: INCIDENT-012
doc_type: incident_report
team: demand_forecast_team
incident_family: demand_side
related_runbook: RUNBOOK-012
severity: high
complexity: medium
resolution_outcome: delayed
duration_minutes: 178
date: 2026-02-14
status: closed
tags: [forecast-pipeline, promotional-campaign, valentines-day, resource-contention, replenishment, delay]
---
INCIDENT-012: Forecast Pipeline Delay — Promotional Campaign Impact

Incident Summary
Demand forecast pipeline failed to complete its scheduled 06:00 EST run on Valentine's Day 2026. The pipeline's inference stage ran out of memory at 07:15 EST due to resource contention with a concurrent model retrain job that had been rescheduled from Sunday to Saturday evening without notifying the demand forecast team. The pipeline was restarted at 09:30 EST after the retrain job completed and memory was freed. Forecast outputs were not available to the replenishment system until 11:45 EST — 5 hours 45 minutes behind schedule. The delay coincided with Valentine's Day promotional campaign replenishment orders which were due to generate at 08:00 EST. Replenishment team manually held orders until forecasts were available. No stockouts resulted but 3 stores in the northeast reported low stock on chocolate and floral arrangements by mid-afternoon.
Timeline

2026-02-13 22:00 EST — Model retrain job rescheduled from Sunday to Saturday evening (not communicated to demand forecast team)
2026-02-14 01:00 EST — Model retrain job started — consuming significant compute resources
2026-02-14 06:00 EST — Forecast pipeline scheduled run started
2026-02-14 07:15 EST — Forecast pipeline inference stage failed — out of memory error
2026-02-14 07:18 EST — Pipeline monitoring alert fired
2026-02-14 07:22 EST — Demand forecast on-call engineer paged
2026-02-14 07:30 EST — Replenishment team notified of forecast pipeline delay
2026-02-14 07:35 EST — Replenishment team placed manual hold on Valentine's Day promotional orders
2026-02-14 07:45 EST — Root cause identified — memory contention with retrain job
2026-02-14 07:50 EST — Decision made to wait for retrain completion rather than kill retrain
2026-02-14 09:15 EST — Model retrain job completed
2026-02-14 09:30 EST — Forecast pipeline restarted
2026-02-14 11:30 EST — Forecast pipeline completed successfully
2026-02-14 11:45 EST — Forecast outputs distributed to replenishment system
2026-02-14 12:00 EST — Replenishment orders released — 4 hours behind schedule
2026-02-14 14:30 EST — 3 northeast stores reported low stock on chocolate and floral
2026-02-14 15:00 EST — Emergency inter-store transfer initiated for worst-affected stores
2026-02-14 16:30 EST — Incident closed

Root Cause
Model retrain job rescheduled to Saturday evening without notifying the demand forecast team. Retrain and forecast pipeline ran concurrently on shared compute infrastructure. Memory demand from both jobs simultaneously exceeded available capacity causing the forecast pipeline inference stage to fail with an out of memory error.
Contributing Factors

No change communication process for job schedule changes affecting shared infrastructure
Shared compute cluster had no resource reservation system — first-come-first-served allocation
Valentine's Day was a known high-stakes promotional day — forecast pipeline should have been pre-prioritized
Decision to wait for retrain rather than kill it cost 90 minutes — a faster decision framework was needed
3 stores reached low stock before emergency transfers arrived — inter-store transfer lead time too long for same-day response

Resolution
Waited for retrain completion. Restarted forecast pipeline. Released held replenishment orders. Emergency inter-store transfers for worst-affected stores.
Impact

Forecast pipeline delayed 5 hours 45 minutes on Valentine's Day
Promotional replenishment orders delayed 4 hours
3 stores reached low stock on chocolate and floral arrangements
No confirmed stockouts — low stock situations resolved by inter-store transfer
Customer complaints about product availability received at 2 northeast locations

Follow-up Actions

 Implement job schedule change communication process — notify affected teams 48 hours before rescheduling jobs on shared infrastructure — completed 2026-02-17
 Implement resource reservation for forecast pipeline on promotional event days — guaranteed compute allocation — Owner: Infrastructure — Due: 2026-03-31
 Define decision escalation framework for kill-vs-wait decisions during resource contention — Owner: Demand Forecast Team Lead — Due: 2026-03-15
 Reduce inter-store transfer lead time for same-day emergency transfers — Owner: Logistics — Due: 2026-04-30
 Add promotional event calendar to infrastructure scheduling system — block competing jobs during high-stakes promotional windows — Owner: Platform Engineering — Due: 2026-03-31

Related Runbook
RUNBOOK-012
Lessons Learned
Shared infrastructure requires shared scheduling visibility. A job schedule change that is invisible to other teams is a change that will cause contention. On high-stakes promotional days the forecast pipeline is more important than a model retrain — priority must be explicit not assumed. The decision to wait for retrain completion was made too slowly — a pre-defined kill threshold (if retrain will take >X more minutes and forecast delay will exceed Y, kill the retrain) would have saved 90 minutes.
