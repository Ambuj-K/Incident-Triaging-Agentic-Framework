---
doc_id: INCIDENT-005
doc_type: incident_report
team: platform_engineering
incident_family: data_pipeline
related_runbook: RUNBOOK-009
severity: critical
complexity: complex
resolution_outcome: escalated
duration_minutes: 267
date: 2026-01-15
status: closed
tags: [schema-migration, split-brain, transactions-table, etl-failure, data-integrity]
---

INCIDENT-005: Schema Migration Failure — Split-Brain State

Incident Summary
A schema migration adding two new columns to the transactions table was deployed as part of a rolling application deployment. The migration completed on the primary database node but failed on replica node 2 of 3 due to a disk space constraint. The result was a split-brain schema state where the primary and replica 1 had the new schema while replica 2 had the old schema. ETL jobs reading from replica 2 began failing with column not found errors 12 minutes after deployment. Application traffic routed to replica 2 returned inconsistent query results. Resolution required emergency disk expansion on replica 2, manual migration application, and schema validation across all nodes. Total duration 267 minutes including a 90-minute window of degraded ETL operations and inconsistent reporting data.
Timeline

2026-01-15 09:00 IST — Schema migration deployed as part of v4.2.1 rolling deployment
2026-01-15 09:03 IST — Migration completed on primary node and replica 1
2026-01-15 09:04 IST — Migration failed on replica 2 — disk space error (disk at 97% utilization)
2026-01-15 09:05 IST — Deployment pipeline marked migration as successful (2 of 3 nodes succeeded — threshold was >50%)
2026-01-15 09:12 IST — First ETL job failure reported — column transaction_channel not found
2026-01-15 09:15 IST — Second ETL job failure — same error
2026-01-15 09:18 IST — Platform engineering on-call paged
2026-01-15 09:25 IST — ETL jobs halted to prevent failure accumulation
2026-01-15 09:35 IST — Schema version checked across all nodes — split-brain confirmed
2026-01-15 09:40 IST — DBA engaged — disk space issue on replica 2 identified
2026-01-15 09:45 IST — Data engineering lead notified — escalation decision made
2026-01-15 10:00 IST — Emergency disk expansion initiated on replica 2
2026-01-15 10:45 IST — Disk expansion completed — 50GB freed
2026-01-15 11:00 IST — Migration applied manually to replica 2
2026-01-15 11:15 IST — Schema validation run across all three nodes — consistent
2026-01-15 11:20 IST — ETL jobs re-enabled — first successful run confirmed
2026-01-15 11:30 IST — Application traffic to replica 2 restored
2026-01-15 13:27 IST — Backfill ETL jobs completed for 90-minute gap
2026-01-15 13:27 IST — Incident closed

Root Cause
Schema migration applied during rolling deployment with an insufficiently strict success threshold (>50% of nodes). Replica 2 had disk utilization at 97% — insufficient space to apply the migration. Disk space monitoring had an alert threshold of 95% but the alert was in a suppressed state from a previous incident and had not been re-enabled.
Contributing Factors

Migration success threshold of >50% allowed partial application — should require 100%
Disk monitoring alert suppressed and not re-enabled after previous incident
No pre-deployment disk space check in migration runbook
Replica 2 disk utilization had been growing for 3 weeks without remediation

Resolution
Emergency disk expansion on replica 2. Manual migration application. Schema validation. ETL backfill for 90-minute gap.
Impact

267 minutes total incident duration
90 minutes of ETL failures and degraded reporting
Inconsistent query results for traffic routed to replica 2 during split-brain window
Finance reporting showed incorrect transaction counts for 90-minute window — required manual reconciliation
No data loss — backfill recovered all missed ETL runs

Follow-up Actions

 Change migration success threshold to 100% — no partial application permitted — completed 2026-01-18
 Re-enable disk monitoring alert on replica 2 — completed 2026-01-15 during incident
 Lower disk alert threshold from 95% to 80% — completed 2026-01-18
 Add pre-migration disk space check to deployment pipeline — fail deployment if any node <20% free — Owner: Platform Engineering — Due: 2026-02-28
 Implement schema consistency check as post-deployment gate — Owner: Platform Engineering — Due: 2026-02-28
 Review all suppressed monitoring alerts monthly — Owner: Platform Engineering lead — Due: recurring

Related Runbook
RUNBOOK-009
Lessons Learned
Majority-success thresholds are inappropriate for schema migrations. Unlike application deployments where a rolling update with partial success is recoverable, a schema migration with partial success creates a split-brain state that is harder to recover from than a clean failure. Schema migrations must succeed on all nodes or fail completely — there is no acceptable middle ground. Suppressed monitoring alerts must have mandatory re-enable dates — an alert that is suppressed indefinitely is not an alert.
