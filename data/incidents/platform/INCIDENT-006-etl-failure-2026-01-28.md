yaml---
doc_id: INCIDENT-006
doc_type: incident_report
team: platform_engineering
incident_family: data_pipeline
related_runbook: RUNBOOK-006
severity: high
complexity: complex
resolution_outcome: delayed
duration_minutes: 194
date: 2026-01-28
status: closed
tags: [etl, data-pipeline, schema-change, delayed-diagnosis, demand-forecast, replenishment]
---
INCIDENT-006: ETL Job Failure — Delayed Diagnosis

Incident Summary
ETL job ingesting POS transaction data into the demand forecast feature table failed silently at 02:00 EST batch run. The job completed with exit code 0 but wrote zero records due to an undocumented schema change in the POS transactions table deployed the previous evening. Downstream demand forecast pipeline consumed stale feature data from the previous day and generated a full set of forecasts without flagging data staleness. Replenishment orders were generated on stale forecasts for 6 hours before a demand analyst noticed order volumes were identical to the previous day — an extremely unlikely pattern. Root cause diagnosis was delayed by 94 minutes because the initial investigation focused on the forecast pipeline rather than the upstream ETL job.
Timeline

2026-01-27 22:30 EST — POS transactions table schema change deployed (new column payment_method_detail added, existing column payment_method renamed to payment_method_legacy)
2026-01-28 02:00 EST — ETL job started, attempted to read payment_method column — column not found
2026-01-28 02:03 EST — ETL job completed with exit code 0, zero records written to feature table
2026-01-28 02:15 EST — Demand forecast pipeline started, consumed previous day feature data (no staleness check)
2026-01-28 04:30 EST — Forecast pipeline completed, outputs distributed to replenishment system
2026-01-28 06:00 EST — Replenishment order generation began on stale forecasts
2026-01-28 08:45 EST — Demand analyst noticed replenishment orders identical to previous day
2026-01-28 08:52 EST — Platform engineering on-call paged
2026-01-28 09:05 EST — Initial investigation focused on forecast pipeline — no issues found
2026-01-28 09:45 EST — Investigation expanded to upstream ETL jobs — zero records issue identified
2026-01-28 10:19 EST — Schema change identified as root cause after reviewing deployment log
2026-01-28 10:35 EST — ETL job updated to handle renamed column
2026-01-28 10:45 EST — ETL job re-run successfully — records written confirmed
2026-01-28 11:15 EST — Demand forecast pipeline re-run with correct feature data
2026-01-28 13:14 EST — Updated forecasts distributed to replenishment system
2026-01-28 13:30 EST — Replenishment orders regenerated on correct forecasts
2026-01-28 13:54 EST — Incident closed

Root Cause
Undocumented schema change to POS transactions table renamed a column that the ETL job depended on. The ETL job was written to fail silently when expected columns were missing — it treated a column not found error as an empty result set and returned exit code 0. The demand forecast pipeline had no input data staleness check and consumed whatever was in the feature table regardless of age.
Contributing Factors

Schema change deployed without notifying data engineering team
No schema change registry or automated compatibility check in deployment pipeline
ETL job error handling treated column not found as empty result — should have been a fatal error
Demand forecast pipeline had no input staleness guard
Diagnosis delayed 94 minutes because investigation started at wrong layer (forecast pipeline not ETL)
Replenishment system had no order pattern anomaly detection — identical orders to previous day should have triggered alert

Resolution
Updated ETL job to reference renamed column. Re-ran ETL job, forecast pipeline, and replenishment order generation sequentially.
Impact

6 hours of replenishment orders generated on previous day stale forecasts
847 replenishment orders required review and partial regeneration
No stockouts resulted — stale forecasts were close enough to actual demand for ambient categories
194 minutes from detection to replenishment system updated with correct forecasts

Follow-up Actions

 ETL job updated to treat column not found as fatal error not empty result — completed 2026-01-29
 Implement schema change registry — all table changes require data engineering sign-off — Owner: Platform Engineering — Due: 2026-03-15
 Add input data staleness check to demand forecast pipeline — Owner: Demand Forecast Team — Due: 2026-02-28
 Add replenishment order pattern anomaly detection — alert if daily orders identical to previous day — Owner: Platform Engineering — Due: 2026-03-15
 Create cross-team deployment notification process for schema changes — Owner: Engineering Lead — Due: 2026-03-01

Related Runbook
RUNBOOK-006
Lessons Learned
Silent failures in data pipelines propagate invisibly through downstream systems. An ETL job that returns exit code 0 while writing zero records is more dangerous than one that fails visibly — every downstream system continues operating with false confidence. Diagnosis always starts at the correct layer — upstream data quality issues masquerade as downstream system failures. When a downstream system produces suspicious output, check data freshness at every upstream dependency before investigating the downstream system itself.