yaml---
doc_id: INCIDENT-003
doc_type: incident_report
team: demand_forecast_team
incident_family: demand_side
related_runbook: RUNBOOK-014
severity: high
complexity: complex
resolution_outcome: escalated
duration_minutes: 312
date: 2025-11-23
status: closed
tags: [ml-forecast, model-regression, retrain, over-ordering, perishables, replenishment]
---
INCIDENT-003: ML Demand Forecasting — Retrain Regression Causing Systematic Over-ordering

Incident Summary
Weekly model retrain completed on Sunday 2025-11-23 and was promoted to production at 05:30 IST. The retrained model had been trained on data including the previous year's pre-Diwali demand surge which inflated baseline assumptions for produce and dairy categories. By 09:00 IST the replenishment system had generated orders 60-80% above normal volume for perishable categories based on the inflated forecasts. Regression was identified at 11:15 IST by a demand analyst reviewing morning replenishment reports. Model rolled back at 14:20 IST. Orders already submitted to suppliers were reviewed — 34% were cancelled or reduced, 66% were accepted and contingency plans made for excess perishable inventory.
Timeline

2025-11-23 01:00 IST — Weekly model retrain job started
2025-11-23 05:15 IST — Retrain completed — validation MAPE 11.2% (within 15% threshold)
2025-11-23 05:30 IST — New model promoted to production
2025-11-23 06:00 IST — Replenishment system began consuming new model forecasts
2025-11-23 07:30 IST — Automated replenishment orders began generating
2025-11-23 09:00 IST — 847 replenishment orders generated for produce and dairy
2025-11-23 11:15 IST — Demand analyst flagged unusually high order volumes in morning report
2025-11-23 11:22 IST — Replenishment system switched to manual approval mode
2025-11-23 11:35 IST — Model comparison run — new model vs previous on last 14 days actual data
2025-11-23 12:10 IST — Regression confirmed — new model MAPE 22.4% vs previous model 9.8% on same period
2025-11-23 12:15 IST — Demand Forecast Team lead notified — rollback decision initiated
2025-11-23 13:00 IST — Commodity team notified — procurement model paused
2025-11-23 14:20 IST — Model rolled back to previous version
2025-11-23 14:35 IST — Replenishment system re-enabled with rollback model
2025-11-23 15:00 IST — Order review completed — 34% of 847 orders cancelled or reduced
2025-11-23 17:30 IST — Incident closed

Root Cause
Training data for the retrain included November 2024 data which contained an unusually large Diwali demand surge (Diwali fell in late October-early November 2024). The model learned inflated seasonal coefficients for produce and dairy in November. The validation MAPE of 11.2% passed the threshold because the holdout set also included the Diwali period — the model performed well on the holdout but both training and holdout reflected the anomalous demand event.
Contributing Factors

Validation set was not temporally separated from the Diwali event — both training and holdout reflected the same anomalous period
No automated check for anomalous training windows before retrain
No shadow mode deployment — model went directly to production without side-by-side comparison
Detection relied on human analyst noticing order volumes — no automated order volume anomaly alert

Resolution
Rolled back to previous model version. Reviewed and partially cancelled inflated replenishment orders. Root cause identified and documented for next retrain cycle. Data science team implemented anomalous period flagging before next retrain.
Impact

847 inflated replenishment orders generated for produce and dairy
288 orders cancelled or reduced after review
Excess perishable inventory risk for 559 accepted orders — contingency plans activated for markdown and donation
Estimated waste cost: $34,000 in perishables that could not be redirected
312 minutes from model deploy to incident close

Follow-up Actions

 Implement anomalous period detection before retrain — flag training windows containing known demand events — completed 2025-12-15
 Separate holdout set temporally — holdout period must not overlap with training anomalies — completed 2025-12-15
 Implement shadow mode deployment for all model retrains — 48 hour parallel run before promotion — Owner: ML Engineering — Due: 2026-02-28
 Add replenishment order volume anomaly alert — fire if daily order volume >40% above 4-week rolling average — Owner: Platform Engineering — Due: 2026-01-31
 Add model performance monitoring — automated MAPE check 6 hours post-deploy against rolling actuals — Owner: ML Engineering — Due: 2026-02-28

Related Runbook
RUNBOOK-014
Lessons Learned
Validation MAPE passing threshold is a necessary but not sufficient condition for model promotion. If the validation set contains the same anomaly as the training set, a badly overfit model will pass validation. Holdout data must be constructed to test generalization, not to test performance on the same anomalous events the model was trained on. Shadow mode would have caught this within hours of deployment.