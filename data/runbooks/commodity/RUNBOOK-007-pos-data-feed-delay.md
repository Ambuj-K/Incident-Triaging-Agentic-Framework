yaml---
doc_id: RUNBOOK-007
doc_type: runbook
team: platform_engineering
incident_family: data_pipeline
severity_range: [medium, high]
systems:
  - pos_systems
  - pos_integration_layer
  - data_pipeline
  - data_warehouse
  - ml_forecasting_system
last_verified: 2026-02-15
last_incident: 2026-01-29
status: active
---
RUNBOOK-007: POS Data Feed Delay
Team: Platform Engineering
Last verified: 2026-02-15
Last incident: 2026-01-29
Status: Active
Overview
POS systems generate transaction data for every sale across all store locations. This data feeds the central data pipeline every 15 minutes and is the primary input for demand forecasting, inventory reconciliation, sales reporting, and executive dashboards. POS feed delays degrade forecast accuracy, delay inventory reconciliation, and produce stale sales reporting. Delays exceeding 4 hours begin to affect next-day replenishment calculations. Delays exceeding 24 hours affect weekly model retraining.
Trigger Conditions

POS feed last ingestion timestamp age >20 minutes (normal <15 minutes)
Transaction record count for current hour >30% below expected baseline for that hour and day type
POS integration layer reporting connection failures to store systems
Store count with active POS feed drops below 90% of total stores
Monitoring alert: pos_feed_last_record_age > 20 minutes
Data warehouse transaction table showing gap in record timestamps

Severity Classification

High if: POS feed delayed >2 hours AND demand forecast model retrain window approaching within 6 hours
High if: >20% of stores not sending data (suggests systemic not store-specific issue)
High if: Delay occurring during peak trading hours (loss of real-time inventory visibility)
Medium if: Delay <2 hours AND no immediate downstream model dependency
Medium if: <10% of stores affected (store-specific issue not systemic)
Low if: Delay <30 minutes, within historical variance, auto-recovery likely

Diagnostic Steps

Determine scope — systemic vs store-specific

Check POS integration layer dashboard for per-store feed status
Count stores with active feed vs delayed vs no feed
If >20% of stores affected: treat as systemic, investigate integration layer
If <10% of stores affected: treat as store-specific, investigate those stores individually


For systemic failures — check POS integration layer

Verify integration layer service health and process status
Check integration layer connection pool to store systems
Check network connectivity between integration layer and store network
Review integration layer logs for error patterns
Check if recent deployment to integration layer correlates with feed start time


For store-specific failures — check individual store connectivity

Verify store network connectivity via network monitoring
Check store POS terminal status via store operations dashboard
Contact store manager if network tools show store as unreachable
Check if store is in a known maintenance window


Check data pipeline downstream of integration layer

Verify pipeline is consuming records from integration layer queue
Check consumer lag on POS data topic in message queue
Verify pipeline processing is not backlogged from earlier delay


Assess downstream impact

Check demand forecast model — is it currently running or about to run
Check inventory reconciliation job schedule — when is next run
Check executive dashboard data freshness indicator
Notify stakeholders proactively if delay will affect scheduled reports



Resolution Steps

If integration layer service down:

Restart integration layer service
Verify stores begin reconnecting within 5 minutes of restart
Monitor reconnection rate — should reach 90% of stores within 15 minutes
If stores not reconnecting after restart: escalate to network team


If store-specific network issue:

Contact store operations for affected stores
Store IT to investigate local network and POS terminal connectivity
POS data for affected stores will backfill automatically once connectivity restored if buffer not exceeded
Check buffer capacity — if store was offline >4 hours local buffer may have overflowed, data loss possible


If message queue consumer lag:

Check consumer group health and restart stalled consumers
Scale up consumer instances if lag is due to volume spike
Monitor lag reduction after scaling


Backfill after restoration:

Verify all stores reconnected and sending current data
Check for gaps in transaction timestamps during delay window
Trigger manual reconciliation job for delay window
Notify demand forecast team if delay affected model input completeness


If data loss from store buffer overflow:

Identify affected stores and time window
Check if store has local transaction backup (most POS systems have local log)
Work with store IT to extract and manually ingest missing transaction records
Flag affected period in data warehouse with data completeness indicator



Escalation Criteria

Escalate to Platform Engineering lead if systemic failure not resolved within 30 minutes
Escalate to Network team if store connectivity issue is widespread
Notify Demand Forecast team lead if delay will affect model retrain input completeness
Notify Finance team if sales reporting gap exceeds 4 hours
SLA: Systemic POS feed failures must be restored within 1 hour. Store-specific within 4 hours.

Related Systems

Upstream: Store POS terminals, store network infrastructure, POS integration layer
Downstream: Data pipeline, data warehouse, ML demand forecasting, inventory reconciliation, executive dashboard, finance reporting
Related runbooks: RUNBOOK-006 (ETL Job Failure), RUNBOOK-008 (Data Warehouse Ingestion), RUNBOOK-003 (ML Forecast)

Historical Notes

Most common cause of systemic failure: integration layer memory leak causing gradual degradation — service requires weekly restart during low traffic window as interim mitigation until fix deployed
Store-specific failures peak during store renovation periods when network infrastructure is temporarily modified
POS local buffer holds 4 hours of transactions — stores offline longer than 4 hours will have data gaps that require manual recovery from local logs
Demand forecast team has a data completeness check that flags model inputs — if POS data completeness for training window drops below 95% model retrain should be postponed
Holiday trading periods see 3-4x normal transaction volume — integration layer and pipeline scaling should be pre-provisioned before major retail events
