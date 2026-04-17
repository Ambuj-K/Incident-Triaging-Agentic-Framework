---
doc_id: RUNBOOK-012
doc_type: runbook
team: demand_forecast_team
incident_family: demand_side
severity_range: [medium, high]
systems:
  - ml_forecasting_system
  - forecast_pipeline
  - replenishment_system
  - procurement_model
last_verified: 2026-03-02
last_incident: 2026-02-14
status: active
---
RUNBOOK-012: Forecast Pipeline Delay

Team: Demand & Sales Forecast Team
Last verified: 2026-03-02
Last incident: 2026-02-14
Status: Active

Overview
The forecast pipeline processes raw demand signals, applies feature engineering, runs inference against the current demand model, and distributes forecast outputs to downstream consumers including the replenishment system, procurement model, and promotional planning tools. Pipeline delays are distinct from model failures (RUNBOOK-003) — the model itself is healthy but outputs are not reaching consumers on schedule. Delays accumulate risk as downstream systems operate on progressively stale forecasts and replenishment decisions drift from actual demand.
Trigger Conditions

Forecast pipeline last successful completion age >26 hours (normal cycle: every 24 hours)
Replenishment system reporting forecast data age >28 hours
Forecast output record count lower than expected by >15% vs previous equivalent run
Pipeline stage stuck in running state >3x historical duration for that stage
Downstream consumer alert: forecast_data_staleness_warning
Feature engineering job producing incomplete feature set

Severity Classification

High if: Pipeline delay >6 hours AND daily replenishment order generation window approaching
High if: Pipeline delay coincides with promotional campaign launch requiring updated forecasts
High if: Delay caused by upstream data quality issue affecting forecast accuracy not just timing
Medium if: Pipeline delayed 2-6 hours with no immediate replenishment dependency
Medium if: Pipeline delayed due to infrastructure resource contention (will self-resolve)
Low if: Delay <2 hours within expected variance, auto-recovery in progress

Diagnostic Steps

Identify which pipeline stage is delayed

Check pipeline orchestration dashboard for stage-level status
Stages in order: data ingestion → feature engineering → model inference → output formatting → distribution
Identify the first stage that is not completing on schedule
Check if delay is accumulating (getting worse) or stable (stuck at same point)


Check upstream data availability

Verify POS transaction data is available and complete for forecast window
Check promotional calendar data feed is current
Verify weather data feed is available (used as demand signal for seasonal categories)
If upstream data incomplete: forecast will be delayed until data is available or pipeline runs with partial data


Check infrastructure resources

Check compute resource availability for inference stage (CPU and memory)
Verify no other large jobs competing for same resources (model retrain, batch ETL)
Check if pipeline was pre-scaled for expected data volume (post-holiday catch-up periods need more resources)


Check model serving layer

Verify model serving endpoint is healthy and responding
Check inference latency — if model serving is slow, pipeline will take longer
Check model serving resource utilization


Check output distribution layer

Verify downstream consumer endpoints are accepting forecast data
Check if any schema changes have been made to forecast output format
Check distribution job queue depth



Resolution Steps

If upstream data incomplete:

Determine if partial data is sufficient for acceptable forecast quality
If yes: trigger pipeline with partial data flag and notify downstream consumers of reduced accuracy
If no: wait for upstream data with ETA from relevant team, notify downstream consumers of delay


If infrastructure resource contention:

Identify competing jobs and their priority
If lower priority than forecast pipeline: pause competing jobs temporarily
Scale up compute resources if budget allows for time-critical situations
Restart pipeline after resources freed


If specific pipeline stage stuck:

Kill stuck stage process after confirming it has not made partial progress that would cause issues on restart
Restart from last successful checkpoint if available
If no checkpoint: restart full pipeline (data ingestion through distribution)


If model serving layer unhealthy:

Follow RUNBOOK-003 (ML Demand Forecasting Model Failure) for model serving issues
Pipeline delay may be symptom of underlying model issue


If distribution layer failing:

Check and fix connectivity to downstream consumer endpoints
If schema mismatch: coordinate emergency schema fix with downstream teams
Manually push latest available forecast to replenishment system if automated distribution cannot be restored quickly


Downstream notification:

Notify replenishment team immediately if delay will affect order generation window
Notify procurement model team if delay will affect sourcing decisions
Provide ETA for pipeline completion — update every 30 minutes if resolution is taking longer than expected



Escalation Criteria

Escalate to Demand Forecast Team lead if pipeline not restored within 3 hours
Escalate to Platform Engineering if root cause is infrastructure-related
Notify Replenishment team lead if delay will affect daily order window
Notify Commodity Team if delay will affect procurement model inputs
SLA: Pipeline must be restored or downstream consumers notified of manual workaround within 4 hours

Related Systems

Upstream: POS data feed, promotional calendar, weather data feed, ML model serving
Downstream: Replenishment system, procurement model, promotional planning, store operations
Related runbooks: RUNBOOK-003 (ML Forecast Model), RUNBOOK-006 (ETL Job), RUNBOOK-007 (POS Feed)

Historical Notes

Most common delay cause: upstream POS data feed running late (RUNBOOK-007) causing feature engineering to wait — RUNBOOK-007 and RUNBOOK-012 incidents frequently co-occur
Pipeline has no checkpoint/resume capability for the inference stage — a failure mid-inference requires full restart, adding 2-3 hours to recovery time — checkpoint capability is on the engineering backlog
Post-holiday periods (day after major sale events) have 3-4x normal data volume — pipeline needs pre-provisioned compute scaling or will run significantly over schedule
Promotional campaign launches are the highest risk scenario — forecast data must be current before campaign goes live or promotional inventory planning is based on baseline not promotional demand
