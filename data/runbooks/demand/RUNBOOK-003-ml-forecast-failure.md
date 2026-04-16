---
doc_id: RUNBOOK-003
doc_type: runbook
team: demand_forecast_team
incident_family: demand_side
severity_range: [medium, high, critical]
systems:
  - ml_forecasting_system
  - replenishment_system
  - procurement_model
  - pos_systems
last_verified: 2026-03-01
last_incident: 2026-02-14
status: active
---

RUNBOOK-003: ML Demand Forecasting Model Failure
Overview
The ML demand forecasting model produces weekly and daily demand forecasts for all SKUs across all store and DC locations. It is retrained every Sunday between 01:00-05:00 IST on the previous week's sales data. Forecast outputs feed the replenishment system, promotional planning, and procurement model. Model failures fall into three categories: retrain failures (model does not update), output anomalies (model updates but produces invalid forecasts), and pipeline failures (model runs but outputs do not reach downstream systems).
Trigger Conditions

Retrain job fails to complete within 6 hour window
Forecast values outside acceptable range: negative values, values >500% of historical baseline
Downstream replenishment system reports missing forecast data
Forecast pipeline last successful run age >25 hours
Model performance metrics below threshold: MAPE >15% on validation set

Severity Classification

Critical if: forecast pipeline completely down AND replenishment orders due within 6 hours
High if: model producing invalid values (negative, extreme outliers) for any category
High if: retrain failed AND current model >2 weeks old
Medium if: retrain failed but current model <1 week old and producing valid forecasts
Low if: single SKU or small category affected, manual override available

Diagnostic Steps

Identify failure category

Check retrain job status and completion logs
Check forecast output pipeline status
Query for invalid forecast values: SELECT count(*) FROM forecasts WHERE forecast_value < 0 OR forecast_value > (historical_baseline * 5)


For retrain failures:

Check training data availability and completeness
Check GPU/compute resource availability for training job
Review training logs for convergence errors, memory errors, or data pipeline failures
Check if input feature pipeline produced valid features for the retrain window


For output anomalies:

Identify affected categories and SKU count
Check if anomaly correlates with specific retrain (rollback candidate)
Check input data for affected categories — corrupted input produces corrupted output
Compare current model version output against previous version on same input


For pipeline failures:

Check forecast export job status
Verify downstream system ingestion endpoints are accepting data
Check for schema changes in forecast output format


Assess downstream impact:

Identify replenishment orders due in next 24 hours that rely on affected forecasts
Check if procurement model is consuming affected forecast data
Identify promotional SKUs with upcoming campaigns that need valid forecasts



Resolution Steps

If retrain failed, current model still valid:

Keep current model in production
Investigate and fix retrain pipeline
Schedule retrain retry for next available window
Monitor model performance metrics daily until retrain succeeds


If output anomalies detected:

Immediately halt downstream consumption of affected forecasts
Rollback to previous model version: mlflow models serve --model-uri models:/demand_forecast/[previous_version]
Verify rollback model producing valid outputs before re-enabling downstream
Investigate root cause before scheduling new retrain


If pipeline failure (model fine, outputs not reaching downstream):

Restart forecast export job
If schema mismatch: coordinate with downstream teams for emergency schema fix
Manually trigger downstream system refresh after pipeline restored


Manual forecast override (if model cannot be restored quickly):

Use last valid forecast with staleness flag
Apply conservative safety stock multiplier: 1.2x on all affected SKUs
Notify replenishment and procurement teams of manual override status
Require human approval on all replenishment orders until model restored



Escalation Criteria

Escalate to ML Engineering lead if retrain failure not resolved within 4 hours
Escalate to Supply Chain lead if replenishment orders need manual review
Escalate to VP Supply Chain if model outage exceeds 24 hours
SLA: Output anomalies must be contained (rollback or halt) within 1 hour of detection

Related Systems

Upstream: Sales transaction pipeline, POS data feed, promotional calendar, weather data feed
Downstream: Replenishment System, Procurement Model, Promotional Planning, Store Operations Dashboard
Related runbooks: RUNBOOK-001 (Inventory Sync), RUNBOOK-002 (Commodity Price Feed), RUNBOOK-004 (Procurement Model), RUNBOOK-012 (POS Feed)

Historical Notes

Most common retrain failure cause: training data pipeline producing incomplete feature set when POS feed is delayed — RUNBOOK-001 and RUNBOOK-003 failures often co-occur
Negative forecast values almost always caused by corrupted input data in produce category — check seasonal adjustment factors if produce is affected
Model rollback is safe and fast — keep previous 3 versions available in MLflow registry at all times
Retrain on holiday weeks produces unreliable models due to atypical sales patterns — manually flag holiday weeks and use ensemble of holiday-week-aware model variant