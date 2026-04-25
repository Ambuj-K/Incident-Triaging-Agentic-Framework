---
doc_id: INCIDENT-008
doc_type: incident_report
team: platform_engineering
incident_family: data_pipeline
related_runbook: RUNBOOK-008
severity: critical
complexity: complex
resolution_outcome: escalated
duration_minutes: 89
date: 2026-02-09
status: closed
tags: [data-warehouse, storage-exhaustion, ingestion-failure, backfill, finance-reporting, critical]
---

INCIDENT-008: Data Warehouse Storage Exhaustion

Incident Summary
Data warehouse storage reached 100% utilization at 03:14 EST causing all ingestion jobs to halt. The storage exhaustion was caused by a combination of three factors: post-holiday backfill jobs running concurrently with normal ingestion, a new analytics table created by the finance team without storage capacity approval, and a log retention policy that had not been enforced for 6 months. All ETL ingestion halted for 89 minutes. Finance month-end close reporting was directly impacted — the finance team was mid-close when the warehouse became read-only for writes. Emergency archival of oldest partitions restored write capacity. No data loss occurred but a 4-hour backfill was required after restoration.

Timeline
2026-02-09 01:00 EST — Post-holiday backfill jobs started (3 concurrent large backfill jobs)
2026-02-09 02:30 EST — Storage utilization reached 85% — alert fired but acknowledged as expected during backfill
2026-02-09 03:14 EST — Storage reached 100% — all write operations halted
2026-02-09 03:16 EST — All ETL ingestion jobs began failing with storage full errors
2026-02-09 03:18 EST — Monitoring alert fired: warehouse_ingestion_error_rate > 1%
2026-02-09 03:20 EST — Platform engineering on-call paged — critical severity
2026-02-09 03:25 EST — Storage exhaustion confirmed as root cause
2026-02-09 03:30 EST — Data governance team on-call paged for emergency archival approval
2026-02-09 03:45 EST — Finance team notified — month-end close reporting impacted
2026-02-09 03:50 EST — Data governance approval received for emergency archival of partitions older than 18 months
2026-02-09 04:00 EST — Archival job started — moving 2.3TB to cold storage
2026-02-09 04:30 EST — 800GB freed — storage at 78% — write operations resumed
2026-02-09 04:43 EST — ETL ingestion jobs restarted
2026-02-09 05:00 EST — Normal ingestion confirmed healthy
2026-02-09 05:15 EST — Backfill jobs restarted with reduced concurrency (1 at a time not 3)
2026-02-09 07:30 EST — All backfill completed
2026-02-09 09:00 EST — Finance team confirmed month-end close reporting data complete
2026-02-09 09:14 EST — Incident closed

Root Cause
Three contributing sources of storage growth converged simultaneously. Post-holiday backfill jobs added 1.1TB of transaction data. Finance team created a new 400GB analytics table without going through the storage capacity approval process. Log retention policy had not been enforced for 6 months, allowing 800GB of logs to accumulate beyond the 90-day retention policy. Storage exhaustion manifests as errno 28 (ENOSPC - no space left on device) in ETL job logs when warehouse disk is full.

Contributing Factors
No storage capacity gate for new table creation — finance team created large table without approval
Log retention enforcement job had been disabled after a false-positive deletion incident 6 months prior and never re-enabled
85% alert acknowledged as expected during backfill without checking absolute growth rate
Three concurrent backfill jobs ran simultaneously — no concurrency limit on backfill operations
Storage headroom policy (keep 20% free) was documented but not enforced programmatically

Resolution
Emergency archival of partitions older than 18 months to cold storage. Freed 800GB. Restored write capacity. Reduced backfill concurrency. Re-ran all failed ingestion jobs.
Impact

89 minutes of complete data warehouse write halt
All ETL ingestion failed during window — 4-hour backfill required
Finance month-end close delayed by 4.5 hours
No data loss
VP Finance notified — formal escalation to VP Engineering

Follow-up Actions

 Re-enable log retention enforcement job — completed 2026-02-09 during incident
 Implement storage capacity approval gate for new table creation >50GB — completed 2026-02-16
 Programmatically enforce 20% storage headroom policy — alert at 75%, halt non-critical jobs at 85%, page on-call at 90% — Owner: Platform Engineering — Due: 2026-03-15
 Limit concurrent backfill jobs to 1 — implement backfill queue — Owner: Platform Engineering — Due: 2026-03-01
 Monthly storage capacity review — Owner: Platform Engineering lead — Due: recurring
 Expand warehouse storage allocation by 40% — Owner: Infrastructure — Due: 2026-04-30

Related Runbook
RUNBOOK-008
Lessons Learned
Storage exhaustion is always a compound failure. No single factor caused this — it required three simultaneous contributors to push utilization from manageable to critical. The 85% alert being acknowledged without investigating growth rate is a pattern failure — an alert acknowledged without action is not an alert, it is noise. Storage headroom policies that exist only in documentation are not policies. Automated enforcement is the only reliable enforcement.
