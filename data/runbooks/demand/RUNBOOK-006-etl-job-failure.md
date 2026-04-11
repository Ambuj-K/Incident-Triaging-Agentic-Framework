yaml---
doc_id: RUNBOOK-006
doc_type: runbook
team: platform_engineering
incident_family: data_pipeline
severity_range: [medium, high, critical]
systems:
  - etl_pipeline
  - data_warehouse
  - pos_systems
  - inventory_management_system
last_verified: 2026-03-01
last_incident: 2026-02-21
status: active
---
RUNBOOK-006: ETL Job Failure
Team: Platform Engineering
Last verified: 2026-03-01
Last incident: 2026-02-21
Status: Active
Overview
ETL jobs ingest, transform, and load data from source systems (POS, WMS, supplier APIs, commodity feeds) into the central data warehouse. Failures prevent downstream systems from accessing current data including executive dashboards, forecasting models, replenishment systems, and finance reporting. ETL jobs run on scheduled intervals ranging from every 15 minutes (POS transactions) to daily (supplier performance metrics). Failure impact scales with job criticality and data freshness requirements of downstream consumers.
Trigger Conditions

ETL job exits with non-zero code
Job runtime exceeds 2x historical average for that job
Data warehouse table last updated timestamp exceeds expected refresh interval by >50%
Downstream system reports stale or missing data
Data quality check post-load fails: null rate, row count, or value range outside expected bounds
Monitoring alert: etl_job_last_success_age > [job_specific_threshold]
Dead letter queue accumulating unprocessed records

Severity Classification

Critical if: POS transaction ETL failing AND sales reporting unavailable AND duration >2 hours
Critical if: Forecasting model input pipeline failing AND replenishment orders due within 6 hours
High if: Any ETL job failing that feeds demand forecast or procurement model inputs
High if: Multiple ETL jobs failing simultaneously (suggests shared infrastructure issue)
Medium if: Single non-critical ETL job failing, downstream consumers have cached data
Medium if: ETL job degraded (running but producing partial output)
Low if: Historical or reporting-only ETL job failing with no operational downstream impact

Diagnostic Steps

Identify failing job and failure type

Check ETL orchestration dashboard for failed job name, start time, failure time
Retrieve job execution logs from orchestration system
Categorize failure: extraction failure, transformation failure, load failure, or orchestration failure
Check if failure is total (job did not run) or partial (job ran but produced incomplete output)


Check source system availability

Verify source system API or database is reachable
Check source system data availability — was expected data present for extraction
Verify source system schema has not changed (column additions, type changes, renames)
Check source system rate limits and connection quotas


Check transformation layer

Review transformation logs for data type errors, null handling failures, or business rule violations
Check if source data contains unexpected values outside transformation assumptions
Verify transformation code has not been recently deployed with breaking changes
Check memory and CPU usage during transformation — large datasets may cause OOM failures


Check load layer

Verify data warehouse target table schema matches expected load schema
Check data warehouse connection pool and availability
Check for unique constraint violations or foreign key failures during load
Verify target table has sufficient storage allocation


Check orchestration system

Verify orchestration scheduler is running correctly
Check for dependency job failures that blocked this job from starting
Check if job was killed by timeout policy before completion
Verify environment variables and credentials used by job are current


Assess downstream impact

Identify all downstream consumers of this ETL job's output
Check data freshness requirements for each consumer
Determine how long cached or stale data remains acceptable for each consumer
Flag any consumers with imminent freshness SLA breach



Resolution Steps

If source system unavailable:

Do not retry ETL job until source system is restored
Follow relevant source system runbook
Once source restored, trigger manual ETL backfill for missed window


If schema change in source:

Do not attempt transformation on mismatched schema
Identify what changed in source schema
Update transformation logic to handle new schema
Test transformation in staging before production retry
Coordinate with source system team on schema change communication process


If transformation failure due to data quality:

Isolate bad records using transformation error logs
Quarantine bad records to dead letter table for manual review
Reprocess clean records if partial load is acceptable for downstream consumers
Alert data quality team with sample of bad records


If load failure due to schema mismatch:

Check if target schema migration was missed
Apply missing migration if safe to do so
Verify migration with data engineering lead before applying in production
Retry load after schema reconciliation


If orchestration failure:

Restart orchestration scheduler if confirmed down
Manually trigger failed job after confirming dependencies are met
Check and reset any stuck dependency locks


Backfill procedure after restoration:

Identify full time window of missed data
Trigger backfill job with explicit start and end timestamps
Verify row counts match expected volume for backfill window
Notify downstream consumers that backfill is complete and data is current



Escalation Criteria

Escalate to Platform Engineering lead if not resolved within 1 hour for high severity
Escalate to Data Engineering lead if schema change is root cause — requires cross-team coordination
Escalate to VP Engineering if multiple critical ETL jobs failing simultaneously
Notify downstream team leads (Demand Forecast, Commodity, Finance) proactively if their data feed is affected
SLA: Critical ETL jobs must be restored or backfill initiated within 2 hours. High within 4 hours.

Related Systems

Upstream: POS systems, WMS, supplier APIs, commodity price feed, ML forecasting pipeline
Downstream: Data warehouse, executive dashboard, demand forecasting model, replenishment system, finance reporting
Related runbooks: RUNBOOK-001 (Inventory Sync), RUNBOOK-007 (POS Data Feed), RUNBOOK-008 (Data Warehouse Ingestion), RUNBOOK-009 (Schema Migration)

Historical Notes

Most common failure cause: source system schema changes deployed without notifying data engineering team — implement schema change notification process
Second most common: memory exhaustion during transformation of large holiday week datasets — increase memory allocation for jobs running during peak retail periods (Black Friday, Diwali, Christmas week)
Orchestration dependency deadlocks have occurred twice — job A waiting for job B, job B waiting for job A — implement deadlock detection in orchestration config
Dead letter queue buildup is an early warning signal — monitor queue depth, not just job success/failure
Backfill jobs for large windows (>24 hours) should run with reduced parallelism to avoid overwhelming source systems
