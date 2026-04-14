yaml---
doc_id: INCIDENT-010
doc_type: incident_report
team: commodity_team
incident_family: supply_side
related_runbook: RUNBOOK-010
severity: high
complexity: medium
resolution_outcome: clean
duration_minutes: 156
date: 2026-01-22
status: closed
tags: [futures-feed, exchange-connectivity, manual-procurement, wheat, corn, procurement-model]
---
INCIDENT-010: Futures Feed Failure — Manual Procurement Activated

Incident Summary
Primary exchange data provider connectivity dropped at 10:15 EST during active CBOT trading hours. Wheat and corn futures data stopped updating. The procurement model detected stale futures data at 10:45 EST and automatically switched to manual approval mode per its stale data guard (implemented after INCIDENT-002). Commodity traders manually sourced wheat and corn forward contracts for the day using Bloomberg terminal as alternative data source. Exchange connectivity was restored at 12:51 EST. All pending procurement decisions that had been held were processed after verification of restored data feed. Total financial decisions made manually: $2.3M across 4 contracts. No financial exposure — manual decisions were made with accurate Bloomberg data.
Timeline

2026-01-22 10:15 EST — Exchange data provider connectivity dropped
2026-01-22 10:15 EST — Futures feed ingestion began failing — no new records
2026-01-22 10:30 EST — Feed staleness reached 15 minutes — approaching alert threshold
2026-01-22 10:45 EST — Procurement model stale data guard triggered — automatic switch to manual approval mode
2026-01-22 10:46 EST — Commodity team alerted by procurement model: futures_data_stale = true
2026-01-22 10:50 EST — Commodity engineer began investigation
2026-01-22 10:55 EST — Exchange status page checked — provider reporting connectivity issues
2026-01-22 11:00 EST — Secondary exchange provider switched to as primary
2026-01-22 11:10 EST — Secondary provider confirmed — wheat and corn data available but 10 minute delayed
2026-01-22 11:15 EST — Commodity traders began manual procurement using Bloomberg as primary reference
2026-01-22 11:30 EST — First manual forward contract decision made — $680,000 wheat 60-day
2026-01-22 12:05 EST — Second and third manual decisions made — corn contracts
2026-01-22 12:30 EST — Fourth manual decision made — wheat 30-day
2026-01-22 12:51 EST — Primary exchange provider connectivity restored
2026-01-22 13:00 EST — Primary provider data verified current and accurate
2026-01-22 13:10 EST — Procurement model switched back to automated mode
2026-01-22 13:15 EST — Held automated decisions processed against restored feed
2026-01-22 13:51 EST — Incident closed

Root Cause
Primary exchange data provider experienced a network connectivity issue on their infrastructure. Issue was external and outside our control. Internal response was correct and timely — stale data guard triggered automatically, manual mode activated, traders used alternative data source.
Contributing Factors

Secondary provider has 10-minute data delay vs real-time primary — acceptable for manual decision support but not for automated model use
Manual procurement decisions required commodity trader availability during trading hours — correct assumption for this time of day but would be an issue outside trading hours

Resolution
Switched to secondary provider for monitoring during outage. Commodity traders used Bloomberg for manual decisions. Restored to automated mode after primary provider recovered.
Impact

156 minutes of manual procurement mode
$2.3M in contracts processed manually — all at accurate market prices
No financial exposure
No missed procurement windows

Follow-up Actions

 Evaluate upgrading secondary provider to real-time feed — current 10-minute delay prevents automated fallback — Owner: Commodity Engineering — Due: 2026-04-30
 Document Bloomberg terminal manual procurement procedure formally — currently undocumented tribal knowledge — Owner: Commodity Team Lead — Due: 2026-02-28
 Add outside-trading-hours manual procurement coverage plan — current process assumes trader availability — Owner: VP Commodity — Due: 2026-03-31

Related Runbook
RUNBOOK-010
Lessons Learned
The stale data guard implemented after INCIDENT-002 worked exactly as designed — it caught the feed failure before any automated decisions were made on stale data. Preventive controls implemented after postmortems have real value. This incident would have had the same financial exposure profile as INCIDENT-002 without that guard. The remaining gap is the secondary provider data delay — a true automated fallover requires a real-time secondary feed not a delayed one.
