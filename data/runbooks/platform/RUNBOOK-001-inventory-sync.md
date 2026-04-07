RUNBOOK-001: Inventory Sync Job Failure
Overview
The inventory sync job reconciles stock levels between the Warehouse Management System and the central Inventory Database. It runs every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 IST). Failure causes stock level discrepancies across DCs which propagate to replenishment decisions, procurement models, and store-facing availability data. This is one of the highest frequency incidents in retail operations.
Trigger Conditions

Inventory sync job exits with non-zero code
Job runtime exceeds 45 minutes (normal runtime 8-12 minutes)
Stock level discrepancy count exceeds 500 SKUs post-sync
Replenishment system reports blocked orders citing stale inventory data
Monitoring alert: inventory_sync_last_success_age > 4.5 hours

Severity Classification

Critical if: discrepancy affects >5000 SKUs AND replenishment orders for perishables are blocked
High if: discrepancy affects 500-5000 SKUs OR replenishment orders blocked for any category
Medium if: discrepancy affects <500 SKUs AND no downstream order blocking
Low if: single DC affected, non-critical SKUs, sync retry already in progress

Diagnostic Steps

Check job execution logs

Location: /var/log/inventory-sync/sync-YYYY-MM-DD.log
Look for: connection timeout, lock timeout, memory error, upstream API failure
Normal completion marker: [INFO] Sync completed. X records processed. 0 errors.


Check database connectivity

Verify Inventory DB primary node is responsive
Check connection pool utilization — alert if >80%
Check for long-running queries blocking the sync transaction


Check Warehouse Management System API

Verify WMS API health endpoint: GET /api/health
Check WMS API rate limit headers on recent calls
Verify WMS credentials have not expired (rotate every 90 days)


Check upstream data feed freshness

Verify POS transaction feed last update timestamp
Verify DC receiving data feed last update timestamp
If either feed is stale, inventory sync will produce incorrect deltas


Assess downstream impact

Query replenishment system for blocked orders: SELECT count(*) FROM orders WHERE status = 'blocked_stale_inventory'
Identify affected DC locations
Check if perishable category SKUs are in the blocked set



Resolution Steps

If database connection issue:

Restart connection pool manager (non-disruptive)
If primary DB unresponsive, initiate manual failover per RUNBOOK-008
Re-trigger sync job after connectivity confirmed


If WMS API failure:

Check WMS vendor status page
Switch to cached WMS snapshot if available (introduces up to 4 hour data lag)
Contact WMS vendor support if outage exceeds 30 minutes


If job timeout:

Kill stuck job process
Check for database locks and release if safe
Re-trigger with reduced batch size: --batch-size 500 (default 2000)


If data feed stale:

Do not re-trigger sync — will produce incorrect deltas
Resolve upstream feed issue first per RUNBOOK-012 (POS feed) or RUNBOOK-013 (DC receiving feed)
Re-trigger sync only after feed freshness confirmed


Manual stock correction (if sync cannot be completed within 2 hours):

Export last known good snapshot from data warehouse
Apply manual correction script with approval from Supply Chain lead
Document all manual corrections in incident report



Escalation Criteria

Escalate to Supply Chain Engineering lead if not resolved within 45 minutes
Escalate to VP Supply Chain if perishable replenishment blocked >2 hours
Escalate to CTO if affecting >3 DCs simultaneously with no ETA
SLA: High severity must be resolved within 2 hours. Critical within 45 minutes.

Related Systems

Upstream: WMS API, POS transaction feed, DC receiving feed
Downstream: Replenishment System, Procurement Model, Store Availability API, Executive Dashboard
Related runbooks: RUNBOOK-002 (Replenishment System), RUNBOOK-008 (Database Failover), RUNBOOK-012 (POS Feed), RUNBOOK-013 (DC Receiving Feed)

Historical Notes

Most common root cause (60% of occurrences): database connection pool exhaustion during peak batch window
Second most common (25%): WMS API credential expiry — set calendar reminder 1 week before rotation date
Known issue: sync job does not handle partial WMS responses gracefully — if WMS returns 206 Partial Content, job marks as success but data is incomplete. Check record count in completion log matches expected range
Peak risk window: Sunday 00:00 when weekly model retrain also runs — resource contention common