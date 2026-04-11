yaml---
doc_id: RUNBOOK-008
doc_type: runbook
team: platform_engineering
incident_family: data_pipeline
severity_range: [medium, high, critical]
systems:
  - data_warehouse
  - etl_pipeline
  - executive_dashboard
  - ml_forecasting_system
  - finance_reporting
last_verified: 2026-03-05
last_incident: 2026-02-09
status: active
---
RUNBOOK-008: Data Warehouse Ingestion Failure
Team: Platform Engineering
Last verified: 2026-03-05
Last incident: 2026-02-09
Status: Active
Overview
The data warehouse is the central repository for all operational and analytical data. Ingestion failures prevent new data from reaching the warehouse, causing downstream consumers to operate on stale data. Ingestion failures differ from ETL failures in that the ETL pipeline may be functioning correctly but the warehouse itself is rejecting or failing to persist incoming data. Root causes include warehouse cluster health issues, storage capacity exhaustion, schema conflicts, network partitions, and access control changes.
Trigger Conditions

Data warehouse ingestion job reporting load failures with non-zero error count
Table row counts not increasing despite ETL jobs completing successfully
Data warehouse cluster health check degraded or failing
Storage utilization alert: warehouse storage >85% capacity
Ingestion latency spike: load time exceeding 3x historical average for equivalent data volume
Access denied errors appearing in ETL load logs
Monitoring alert: warehouse_ingestion_error_rate > 1%

Severity Classification

Critical if: Complete warehouse ingestion failure AND executive reporting unavailable AND duration >2 hours
Critical if: Warehouse storage exhausted — all ingestion halted
High if: Ingestion failure affecting forecasting model input tables
High if: Ingestion failure affecting finance reporting tables during month-end close
Medium if: Partial ingestion failure affecting non-critical reporting tables
Medium if: Ingestion degraded (higher latency, higher error rate) but not fully failed
Low if: Single table ingestion failing, no operational downstream impact

Diagnostic Steps

Determine failure scope

Check which tables are failing to ingest
Determine if failure is warehouse-wide or table-specific
Check if ETL jobs are completing successfully and handing off to warehouse correctly
Distinguish between ETL failure (upstream) and warehouse ingestion failure (at load layer)


Check warehouse cluster health

Verify warehouse cluster node status — all nodes healthy and reachable
Check cluster resource utilization: CPU, memory, I/O
Check active query count — high concurrent query load can block ingestion
Check for long-running queries blocking table locks needed for ingestion


Check storage capacity

Query: SELECT schema_name, sum(data_length_bytes) FROM warehouse_storage_stats GROUP BY schema_name ORDER BY sum DESC
Check total storage utilization vs allocated capacity
If >85%: identify largest tables and oldest partitions for archival
If >95%: emergency — warehouse will halt all writes, escalate immediately


Check schema conflicts

Verify target table schema matches incoming data schema
Check recent DDL changes to target tables
Look for column type mismatches or missing required columns in incoming data


Check access controls

Verify ETL service account permissions on target tables
Check if IAM or database role changes were recently applied
Verify network access rules between ETL layer and warehouse cluster


Assess downstream impact

Check all downstream consumers for data freshness
Identify which consumers have the shortest acceptable staleness window
Notify affected teams proactively with estimated resolution time



Resolution Steps

If warehouse cluster health issue:

Identify and terminate long-running blocking queries with DBA approval
If node failure: initiate node recovery per infrastructure runbook
If cluster overloaded: throttle incoming ingestion rate, prioritize critical tables
Restart warehouse services only if cluster is completely unresponsive and DBA approves


If storage exhaustion:

Immediately identify largest tables and oldest partitions
Archive oldest partitions to cold storage: coordinate with data governance team
Do not delete data without data governance approval
After freeing space: verify ingestion resumes automatically
Raise storage capacity ticket immediately — this is a recurring risk if not addressed


If schema conflict:

Do not force load mismatched schema — data corruption risk
Identify exact schema difference between incoming data and target table
Apply schema migration if additive (new nullable column): coordinate with downstream teams first
If breaking change: halt ingestion, escalate to data engineering lead for resolution plan


If access control issue:

Restore previous access configuration if change was unintended
If intentional change: update ETL service account permissions to match new requirements
Verify fix with a test ingestion before resuming full pipeline


Backfill after restoration:

Identify full time window of failed ingestion
Re-run ETL jobs for missed window in chronological order
Verify row counts and data completeness after backfill
Notify downstream consumers that data is current



Escalation Criteria

Escalate to Platform Engineering lead immediately for storage exhaustion
Escalate to DBA for cluster health issues requiring query termination
Escalate to Data Governance for storage archival decisions
Notify Finance team lead immediately if month-end close reporting is affected
Notify Demand Forecast team if ingestion failure exceeds 4 hours
SLA: Storage exhaustion must be resolved within 1 hour. Other critical ingestion failures within 2 hours.

Related Systems

Upstream: ETL pipeline, POS integration layer, ML forecasting pipeline, commodity price feed
Downstream: Executive dashboard, finance reporting, demand forecasting model, replenishment system
Related runbooks: RUNBOOK-006 (ETL Job Failure), RUNBOOK-007 (POS Feed), RUNBOOK-009 (Schema Migration)

Historical Notes

Storage exhaustion has occurred twice — both times during post-holiday data catch-up when backfill jobs ran concurrently with normal ingestion — implement storage headroom policy: never allow utilization to exceed 80% in normal operations
Month-end close is the highest risk window for ingestion failures — Finance team runs heavy analytical queries that compete with ingestion for warehouse resources — pre-schedule ingestion priority elevation during close window
Long-running analytical queries from executive dashboard are the most common cause of ingestion blocking — implement query timeout policy of 30 minutes for dashboard queries
Schema conflicts most commonly introduced by upstream teams deploying changes without notifying data engineering — implement schema change registry and automated compatibility check in CI pipeline
