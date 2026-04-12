yaml---
doc_id: INCIDENT-001
doc_type: incident_report
team: platform_engineering
incident_family: data_pipeline
related_runbook: RUNBOOK-001
severity: high
complexity: medium
resolution_outcome: clean
duration_minutes: 38
date: 2026-01-14
status: closed
tags: [inventory-sync, database, connection-pool, replenishment]
---
INCIDENT-001: Inventory Sync Failure — Clean Resolution

Incident Summary
Inventory sync job failed at 04:00 IST batch run due to database connection pool exhaustion. 1,847 SKUs showed incorrect stock levels across 2 regional DCs. Replenishment orders for ambient grocery category blocked for 38 minutes. Resolved by restarting connection pool manager and re-triggering sync job. No manual stock corrections required.
Timeline

04:08 IST — Monitoring alert fired: inventory_sync_last_success_age > 4.5 hours
04:09 IST — PagerDuty paged platform engineering on-call
04:12 IST — On-call engineer acknowledged and began investigation
04:15 IST — Job execution logs reviewed — connection timeout errors identified
04:18 IST — Database connection pool utilization confirmed at 94% — root cause identified
04:22 IST — Connection pool manager restarted — non-disruptive
04:24 IST — Inventory sync job manually re-triggered
04:31 IST — Sync job completed successfully — 1,847 SKUs reconciled
04:33 IST — Replenishment system unblocked — orders resumed
04:46 IST — Incident closed after 15 minute monitoring period confirmed stability

Root Cause
Database connection pool exhaustion. A long-running analytical query initiated by the executive dashboard at 03:45 IST consumed 40 of the 50 available connections in the inventory database connection pool. When the inventory sync job attempted to start at 04:00 IST, insufficient connections were available, causing the job to fail after retry attempts.
Contributing Factors

Connection pool size (50) was set 18 months ago when analytical query load was lower
No connection pool monitoring alert configured — alert only fires on job failure not on pool utilization
Executive dashboard queries not subject to connection limit or timeout policy

Resolution
Restarted connection pool manager which cleared stale connections held by the completed analytical query. Re-triggered inventory sync job which completed successfully.
Impact

1,847 SKUs with incorrect stock levels for 38 minutes
Replenishment orders for ambient grocery blocked for 38 minutes
No orders missed — replenishment window was still open when sync recovered
Zero customer-facing impact

Follow-up Actions

 Add connection pool utilization monitoring alert at 80% threshold — completed 2026-01-16
 Implement connection limit for executive dashboard queries — Owner: Platform Engineering — Due: 2026-02-28
 Increase connection pool size from 50 to 100 — Owner: DBA — Due: 2026-02-15
 Add query timeout policy of 30 minutes for analytical queries — Owner: Platform Engineering — Due: 2026-02-28

Related Runbook
RUNBOOK-001
Lessons Learned
Connection pool monitoring should be a leading indicator not a lagging one. Job failure alerts tell you the problem has already happened. Pool utilization alerts give you time to act before the job fails.