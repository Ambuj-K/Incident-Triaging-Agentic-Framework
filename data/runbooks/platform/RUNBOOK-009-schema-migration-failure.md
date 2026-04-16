---
doc_id: RUNBOOK-009
doc_type: runbook
team: platform_engineering
incident_family: data_pipeline
severity_range: [high, critical]
severity_range: [high, critical]
systems:
  - data_warehouse
  - etl_pipeline
  - transactions_database
  - inventory_database
last_verified: 2026-02-28
last_incident: 2026-01-15
status: active
---

RUNBOOK-009: Schema Migration Failure
Team: Platform Engineering
Last verified: 2026-02-28
Last incident: 2026-01-15
Status: Active
Overview
Schema migrations modify the structure of database tables or data warehouse schemas — adding columns, changing types, renaming fields, dropping columns, or modifying constraints. Failed or incorrectly applied migrations cause downstream ETL jobs, application queries, and reporting pipelines to fail with schema mismatch errors. The risk window is highest immediately after deployment and during the first ETL job run post-migration. Unlike most incidents, schema migration failures often require a coordinated rollback across multiple systems simultaneously.
Trigger Conditions

ETL job failing with column not found or type mismatch error immediately after deployment
Application returning database errors referencing missing or renamed columns
Data warehouse ingestion failing with schema validation errors
Downstream reporting showing null values in previously populated columns
Migration job exiting with non-zero code during deployment
Monitoring alert: schema_validation_check_failed post-deployment

Severity Classification

Critical if: Migration failure affecting transactions table or inventory table — core operational data
Critical if: Migration cannot be rolled back cleanly (data already written in new schema)
High if: Multiple ETL jobs failing due to schema mismatch
High if: Migration failure affecting demand forecast or procurement model input tables
Medium if: Single non-critical reporting table affected
Medium if: Migration partially applied — some nodes updated, others not (split-brain schema)
Low if: Migration failed before any data written, clean rollback available

Diagnostic Steps

Determine migration state

Check migration job logs for exact failure point
Determine if migration was applied to zero, some, or all database nodes
Check migration version table to see which migrations are recorded as applied
Determine if any data was written in new schema format before failure


Assess rollback feasibility

Check if rollback script exists for this migration (should be mandatory per deployment process)
Determine if rollback is safe — if data was written in new schema, rollback may cause data loss
Check if downstream systems have already adapted to new schema (if so, rollback breaks them)
If rollback is not safe: do not attempt — escalate immediately to data engineering lead


Identify all affected downstream systems

Check which ETL jobs reference the migrated table
Check which application services query the migrated table
Check which reports or dashboards depend on the migrated table
Halt all writes to affected table until migration state is resolved


Check split-brain schema state

In distributed databases: verify all nodes have same schema version
Query each node for column list and compare
Split-brain schema is a critical state — reads may return inconsistent results


Assess data integrity

If migration was partially applied: check for data written in inconsistent state
Identify any records that may be corrupt or incomplete due to partial migration
Do not attempt data repair without data engineering lead approval



Resolution Steps

If migration failed before any data written (clean state):

Roll back migration using rollback script
Verify all nodes return to previous schema version
Restart affected ETL jobs and application services
Fix migration script, test in staging, re-deploy with fix


If migration partially applied (split-brain):

Halt all writes to affected table immediately
Complete the migration forward on remaining nodes rather than rolling back
This is safer than rolling back when some nodes are already migrated
Verify all nodes at same schema version before re-enabling writes
Requires data engineering lead approval before proceeding


If migration applied but rollback needed due to bugs:

Assess data written in new schema — can it be safely transformed back
If yes: write and test forward-fix migration that returns to previous state
If no: accept new schema, fix application and ETL code to work with it
Never write a rollback that drops data without explicit data governance approval


If downstream ETL jobs failing due to schema mismatch:

Halt ETL jobs — do not accumulate failures
Determine whether to roll forward (fix ETL to match new schema) or roll back (revert schema)
Roll forward is usually faster if migration itself was successful
Update ETL transformation logic for new schema
Test in staging before re-enabling production ETL


Post-resolution verification:

Run schema validation check across all nodes
Verify ETL jobs complete successfully end to end
Check downstream consumers for data completeness
Run data quality checks on affected tables



Escalation Criteria

Escalate to Data Engineering lead immediately for any critical severity migration failure
Escalate to DBA for split-brain schema state
Escalate to VP Engineering if core operational tables (transactions, inventory) are affected
Notify all downstream team leads (Demand Forecast, Commodity, Finance) immediately
SLA: Writes must be halted within 15 minutes of detection. Resolution plan must exist within 1 hour.

Related Systems

Upstream: Deployment pipeline, application services writing to migrated tables
Downstream: ETL pipeline, data warehouse, all downstream consumers of affected tables
Related runbooks: RUNBOOK-006 (ETL Job Failure), RUNBOOK-008 (Data Warehouse Ingestion)

Historical Notes

Root cause of most schema migration incidents: migration deployed to production without staging validation — mandatory staging deployment and validation gate must precede all production schema changes
Split-brain schema has occurred once — caused by rolling deployment where new application version (expecting new schema) deployed alongside old application version (expecting old schema) during migration window — coordinate migration timing with deployment to avoid overlap
Rollback scripts are frequently missing or untested — establish policy that every migration PR must include a tested rollback script before merge
The most dangerous migration pattern: dropping a column that application code still references — implement column usage audit before any DROP COLUMN migration
Forward-fix is almost always faster and safer than rollback once any data has been written in new schema — default to forward-fix unless data engineering lead explicitly approves rollback
