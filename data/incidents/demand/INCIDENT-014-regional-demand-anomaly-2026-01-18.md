yaml---
doc_id: INCIDENT-014
doc_type: incident_report
team: demand_forecast_team
incident_family: demand_side
related_runbook: RUNBOOK-015
severity: high
complexity: medium
resolution_outcome: clean
duration_minutes: 156
date: 2026-01-18
status: closed
tags: [regional-demand-anomaly, weather-event, flour-rice, northeast-stores, genuine-demand, pantry-loading]
---
INCIDENT-014: Regional Demand Anomaly — Confirmed Genuine Demand

Incident Summary
Flour and rice sales velocity in northeast region stores reached 340% above forecast baseline on 2026-01-18 starting at 09:00 EST. Anomaly detected by automated monitoring at 09:45 EST. Initial investigation ruled out data quality issues within 35 minutes. Root cause identified as a major snowstorm forecast for the following 48 hours driving pantry-loading behavior. Emergency replenishment orders placed for flour and rice across 34 northeast stores. All stores maintained adequate stock throughout the storm period. Demand anomaly resolved naturally as storm passed and customers reduced pantry-loading behavior.
Timeline

2026-01-18 07:00 EST — National Weather Service issued blizzard warning for northeast — up to 24 inches forecast
2026-01-18 09:00 EST — Flour and rice sales velocity began accelerating in northeast stores
2026-01-18 09:45 EST — Automated anomaly alert fired: northeast region flour and rice >50% above forecast
2026-01-18 09:48 EST — Demand forecast on-call engineer paged
2026-01-18 09:55 EST — POS data feed integrity check — confirmed clean, no duplicates
2026-01-18 10:05 EST — Sales velocity now at 2.1x forecast and accelerating
2026-01-18 10:20 EST — Data quality ruled out — genuine demand confirmed
2026-01-18 10:25 EST — Weather alert cross-referenced — blizzard warning identified as trigger
2026-01-18 10:30 EST — Demand forecast team lead notified — emergency response activated
2026-01-18 10:35 EST — Forecast updated for northeast flour and rice — 3.4x baseline uplift applied
2026-01-18 10:45 EST — Emergency replenishment orders generated for 34 northeast stores
2026-01-18 11:00 EST — Primary supplier contacted — confirmed same-day delivery capacity for 28 stores
2026-01-18 11:15 EST — Secondary supplier activated for remaining 6 stores
2026-01-18 11:30 EST — All 34 stores confirmed with inbound emergency replenishment
2026-01-18 12:00 EST — Sales velocity peaked at 3.4x forecast — consistent with updated forecast
2026-01-18 13:00 EST — Demand stabilizing — still elevated but no longer accelerating
2026-01-18 14:00 EST — All emergency deliveries confirmed en route
2026-01-18 15:45 EST — Incident operationally closed — monitoring continued through storm period
2026-01-20 09:00 EST — Demand returned to normal baseline — incident fully closed

Root Cause
Severe weather forecast driving consumer pantry-loading behavior. This is a known demand pattern for staple categories ahead of significant weather events. The forecast model did not have weather event signals as input features and therefore could not anticipate the demand surge.
Contributing Factors

Weather data not integrated as demand signal in forecasting model — known gap
Automated anomaly detection worked correctly and fired within 45 minutes of anomaly start
Data quality validation process worked correctly — ruled out false signal within 35 minutes
Response was faster than previous similar incidents due to improved runbook and team familiarity

Resolution
Data quality validated. Genuine demand confirmed. Forecast updated. Emergency replenishment ordered. All stores maintained stock throughout storm period.
Impact

34 northeast stores at elevated demand risk for flour and rice
No stockouts — emergency replenishment covered all stores
$180,000 in emergency replenishment orders at standard contract rates (primary supplier)
$45,000 in secondary supplier orders at slight premium
Positive customer outcome — stores maintained stock during storm

Follow-up Actions

 Integrate weather forecast data as demand model feature — severe weather warnings should automatically trigger demand review for staple categories in affected regions — Owner: ML Engineering — Due: 2026-06-30
 Document pantry-loading demand multipliers by storm severity for flour, rice, bread, water, canned goods — completed 2026-01-25
 Implement automatic emergency replenishment trigger for weather-confirmed demand anomalies — reduce manual intervention required — Owner: Platform Engineering — Due: 2026-04-30

Related Runbook
RUNBOOK-015
Lessons Learned
The data quality validation step before acting on anomalies is essential and worked correctly here. Acting on a false signal would have generated unnecessary emergency replenishment costs. The 35-minute validation window before confirming genuine demand is the right balance — fast enough to respond before stockout risk materializes, thorough enough to avoid false positives. Weather integration with the forecasting model remains the highest value improvement for this incident type — two of three historical regional anomalies were weather-driven and both required manual detection.