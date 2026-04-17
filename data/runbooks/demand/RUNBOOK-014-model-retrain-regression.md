---
doc_id: RUNBOOK-014
doc_type: runbook
team: demand_forecast_team
incident_family: demand_side
severity_range: [high, critical]
systems:
  - ml_forecasting_system
  - model_registry
  - replenishment_system
  - procurement_model
last_verified: 2026-03-03
last_incident: 2025-11-23
status: active
---
RUNBOOK-014: Model Retrain Regression Detected Post-Deploy

Team: Demand & Sales Forecast Team
Last verified: 2026-03-03
Last incident: 2025-11-23
Status: Active

Overview
Model retrain regression occurs when a newly retrained demand forecasting model, after deployment to production, produces systematically worse forecasts than the previous model version. Regression is distinct from a model failure (RUNBOOK-003) — the model is running and producing outputs, but the quality of those outputs has degraded. Regression may not be immediately obvious because forecasts look plausible but are directionally wrong, leading to systematic over or under-ordering before the problem is detected. Detection lag is the primary risk — the longer regression goes undetected, the more replenishment decisions are made on degraded forecasts.
Trigger Conditions

Model performance monitoring alert: MAPE on holdout set >15% (threshold for production model)
Forecast accuracy report showing >20% degradation vs previous model version on same period
Replenishment system generating orders significantly different from historical patterns without known demand trigger
Actual vs forecast variance report showing systematic bias (consistently over or under forecasting)
Data science team raises concern about model validation metrics post-retrain
Unusual distribution of forecast values (more extreme values than historical model)

Severity Classification

Critical if: Regression affects all SKU categories AND replenishment orders already generated on degraded forecast
Critical if: Negative forecast values produced (see RUNBOOK-003 for this specific case)
High if: Regression affects major categories (produce, grain, dairy) with high replenishment volume
High if: Systematic over-forecasting detected — will cause overstock and waste for perishables
High if: Systematic under-forecasting detected — will cause stockouts as replenishment is insufficient
Medium if: Regression confined to minor categories, impact on total replenishment volume <10%
Low if: Regression detected before any replenishment orders generated on new model

Diagnostic Steps

Confirm and quantify regression

Run model comparison: generate forecasts from new and previous model on same input data
Calculate MAPE for both models on last 2 weeks of actual sales data (out-of-sample)
If new model MAPE >15% or >5 percentage points worse than previous model: regression confirmed
Identify which categories and SKUs are most affected


Identify regression root cause

Check training data for the retrain window — was it representative
Check if training data pipeline produced complete and clean feature set
Check for data leakage in training: were any features using future information
Check if hyperparameters changed from previous retrain
Check if input feature distribution shifted significantly from training distribution to production


Assess replenishment impact

Identify all replenishment orders generated since new model was deployed
Compare order volumes to equivalent period with previous model
Flag orders with >30% variance from historical patterns for manual review
Check if any orders have already been submitted to suppliers


Check model registry

Verify previous model version is still available in registry
Confirm previous model version produced acceptable metrics at time of deployment
Verify rollback procedure is available and tested


Determine rollback safety

Is previous model version still valid for current demand patterns
Has significant time passed since previous model was trained (>4 weeks: may not reflect current patterns)
Are there known issues with previous model that led to this retrain



Resolution Steps

Immediate containment:

Switch replenishment system to manual approval mode — halt automated order generation
Notify procurement model team to pause commodity sourcing decisions dependent on demand forecast
This prevents additional bad orders from being generated while investigation proceeds


Model rollback (if previous model is valid):

Roll back to previous model version: mlflow models serve --model-uri models:/demand_forecast/[previous_version]
Verify rollback model producing acceptable forecasts on recent data
Re-enable replenishment system automated ordering after rollback verified
Document rollback decision and rationale in model registry


Review orders generated on degraded model:

Pull all orders generated since new model deployed
For orders not yet submitted to suppliers: cancel and regenerate with rollback model
For orders already submitted: assess whether to cancel, modify, or accept
Requires commodity team lead review for orders already with suppliers


Root cause investigation and model fix:

Data science team to identify and fix root cause of regression
Fix must be validated on holdout data before next retrain
Implement additional pre-deployment validation checks to prevent recurrence
Do not retrain until root cause is understood and addressed


Enhanced monitoring for next deploy:

After next retrain: run 48-hour shadow mode (new model runs alongside old model, outputs compared but not used)
Only promote new model to production if shadow mode shows acceptable performance
Implement automated regression detection that fires within 6 hours of new model deploy



Escalation Criteria

Escalate to Demand Forecast Team lead immediately upon regression confirmation
Escalate to VP Supply Chain if high severity regression with significant replenishment impact
Notify Commodity Team lead — their procurement decisions depend on demand forecast quality
Notify Finance if over-ordering has occurred for perishables (waste and write-off risk)
SLA: Replenishment manual approval mode must be activated within 1 hour of regression confirmation. Rollback decision within 3 hours.

Related Systems

Upstream: Training data pipeline, feature engineering pipeline, model registry
Downstream: Replenishment system, procurement model, promotional planning
Related runbooks: RUNBOOK-003 (ML Forecast Model Failure), RUNBOOK-012 (Forecast Pipeline), RUNBOOK-006 (ETL Job)

Historical Notes

Historical regression root cause: training data window included anomalous period (COVID lockdown sales patterns in 2020-2021 data) that skewed model weights — implement automatic detection of anomalous training windows before retrain
Shadow mode was proposed after the November 2025 incident but not yet implemented — this is the highest priority engineering improvement for this runbook
Systematic over-forecasting is more costly than under-forecasting for perishables due to waste — err on side of conservative forecast when uncertainty is high
Model registry maintains last 5 versions — do not allow registry to drop below 3 versions as this limits rollback options
Data science team typically needs 2-3 days to diagnose and fix regression root cause — plan for extended manual approval mode duration
