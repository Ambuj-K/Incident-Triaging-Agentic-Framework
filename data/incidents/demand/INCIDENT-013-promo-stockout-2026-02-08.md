yaml---
doc_id: INCIDENT-013
doc_type: incident_report
team: demand_forecast_team
incident_family: demand_side
related_runbook: RUNBOOK-013
severity: high
complexity: complex
resolution_outcome: partial
duration_minutes: 384
date: 2026-02-08
status: closed
tags: [promotional-demand, stockout, advertised-item, forecast-not-updated, customer-impact, marketing]
---
INCIDENT-013: Promotional Demand Spike — Stockout on Advertised Item

Incident Summary
A weekend flash sale promotion for organic produce was announced via email and social media on Friday 2026-02-06 evening. The promotional planning system was updated with the campaign details but the forecast system ingests promotional calendar data only at the weekly Sunday run — the Friday update was not reflected in the active forecast. Saturday replenishment orders were generated on baseline forecast. By 11:00 EST Saturday 2026-02-08 organic produce SKUs were selling at 2.8x forecast velocity. Stockouts began at 14:30 EST across 23 stores. Emergency replenishment was ordered but lead time meant stores could not be restocked until Sunday morning. 6 hours of stockout on advertised promotional items resulted in customer complaints and social media criticism.
Timeline

2026-02-06 18:00 EST — Flash sale promotion announced via email and social media
2026-02-06 18:30 EST — Promotional planning system updated with campaign SKUs and expected lift
2026-02-06 19:00 EST — Forecast system did not ingest update — next ingest scheduled for Sunday 01:00 EST
2026-02-07 06:00 EST — Saturday replenishment orders generated on baseline forecast — no promotional uplift
2026-02-08 09:00 EST — Stores opened — organic produce promotion driving above-baseline demand
2026-02-08 11:00 EST — Sales velocity for organic produce at 2.8x forecast
2026-02-08 11:15 EST — Store operations reported unusually high demand on organic produce
2026-02-08 11:30 EST — Demand forecast team notified
2026-02-08 11:45 EST — Confirmed promotional forecast not updated — baseline orders insufficient
2026-02-08 12:00 EST — Emergency replenishment orders placed with primary produce supplier
2026-02-08 12:30 EST — Supplier confirmed earliest delivery: Sunday 07:00 EST
2026-02-08 13:00 EST — Inter-store transfer initiated from stores with surplus stock
2026-02-08 14:30 EST — First stockouts reported — 8 stores
2026-02-08 15:30 EST — 23 stores confirmed at stockout on organic produce promotional SKUs
2026-02-08 16:00 EST — Marketing team notified — promotional messaging adjustment requested
2026-02-08 16:30 EST — Marketing updated email and social media — acknowledged availability issues
2026-02-08 17:00 EST — Customer service team briefed — compensation policy for affected customers
2026-02-08 18:00 EST — 384 minutes from detection to operational close — stockout continued overnight
2026-02-09 07:00 EST — Emergency replenishment arrived — stores restocked
2026-02-09 09:00 EST — Incident fully closed

Root Cause
Promotional calendar data ingested into forecast system only at weekly Sunday run. A promotion announced Friday evening was invisible to the forecast system until Sunday — 36 hours after announcement. Saturday replenishment orders were generated with no knowledge of the weekend promotion.
Contributing Factors

Forecast system promotional calendar ingest is weekly not real-time
No alert or process for promotions announced within 48 hours of go-live
Marketing team did not notify demand forecast team directly — relied on system integration
Saturday replenishment order generation had no promotional calendar cross-check
Inter-store transfer lead time too long for same-day stockout response

Resolution
Emergency replenishment ordered. Inter-store transfers partially mitigated stockouts. Marketing updated promotional messaging. Customer compensation policy applied.
Impact

23 stores at stockout on advertised promotional organic produce SKUs
6 hours of stockout duration across affected stores
Estimated lost revenue: $84,000
Customer complaints: 340 contacts to customer service
Social media criticism: 2 posts with >500 engagements each
Marketing cost of promotional messaging adjustment

Follow-up Actions

 Implement real-time promotional calendar sync to forecast system — ingest within 1 hour of promotional planning update — Owner: Demand Forecast Engineering — Due: 2026-04-30
 Implement 48-hour promotion notification process — any promotion announced within 48 hours of go-live requires direct demand forecast team notification — Owner: Marketing Operations — Due: 2026-03-15
 Add promotional calendar cross-check to replenishment order generation — block baseline orders for active promotional SKUs — Owner: Platform Engineering — Due: 2026-03-31
 Customer compensation review — ensure policy is adequate for advertised item stockouts — Owner: Customer Service — Due: 2026-02-28
 Post-incident review with marketing team — establish joint process for flash sale announcements — Owner: Demand Forecast Team Lead — Due: 2026-02-28

Related Runbook
RUNBOOK-013
Lessons Learned
A system integration that syncs weekly is not an integration — it is a batch job with a 7-day lag. Flash sales and short-notice promotions are an inherent part of retail operations. The forecast system must be able to respond to promotional calendar changes within hours not days. Until real-time sync is implemented, a human notification process is a necessary compensating control. Stockouts on advertised promotional items cause disproportionate customer damage compared to stockouts on non-promoted items — the customer came specifically for that item.