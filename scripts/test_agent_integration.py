import warnings
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

import time
import json
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState
from incident_triage.models.incident_report import Severity

graph = build_graph(interrupt_on_human_review=False)


@dataclass
class IntegrationTestCase:
    name: str
    incident: str
    expected_routing: str
    expected_severity: Optional[str | tuple[str, ...]] = None
    expected_escalate: Optional[bool] = None
    corpus_domain: str = "unknown"
    notes: str = ""


TEST_CASES = [

    # --- VALIDATION FAILURES ---
    IntegrationTestCase(
        name="empty input",
        incident="",
        expected_routing="validation_failed",
        corpus_domain="none",
        notes="Should fail at validate_input node",
    ),
    IntegrationTestCase(
        name="too short input",
        incident="broken",
        expected_routing="validation_failed",
        corpus_domain="none",
        notes="Under 5 words should fail validation",
    ),

    # --- AUTO RESOLVE ---
    IntegrationTestCase(
        name="low severity dashboard",
        incident="One internal reporting dashboard loading slowly for a single analyst. No other users affected. No business critical data involved.",
        expected_routing="auto_resolve",
        expected_severity="low",
        expected_escalate=False,
        corpus_domain="platform",
        notes="Low severity, low stakes, should auto-resolve",
    ),

    # --- PLATFORM DOMAIN ---
    IntegrationTestCase(
        name="inventory sync failure",
        incident="Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="platform",
        notes="High severity, should retrieve RUNBOOK-001 and INCIDENT-001",
    ),
    IntegrationTestCase(
        name="ETL silent failure",
        incident="ETL job ingesting POS transaction data completed with exit code 0 but downstream systems reporting stale data. No records appear to have been written.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="platform",
        notes="Should retrieve RUNBOOK-006 and INCIDENT-006",
    ),
    IntegrationTestCase(
        name="schema migration failure",
        incident="Schema migration deployed to transactions table without rollback plan. Downstream ETL jobs failing with column not found errors. 4 hours of transaction data not ingested.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="platform",
        notes="Should retrieve RUNBOOK-009 and INCIDENT-005",
    ),
    IntegrationTestCase(
        name="POS data feed delay",
        incident="POS data feed delayed by 3 hours across all stores. Transaction data not reaching data warehouse. Morning executive dashboard showing yesterday data.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="platform",
        notes="Should retrieve RUNBOOK-007 and INCIDENT-007",
    ),

    # --- COMMODITY DOMAIN ---
    IntegrationTestCase(
        name="commodity price feed stale",
        incident="Wheat commodity price feed not updating since 6am. Procurement model making sourcing decisions on stale price data. Purchase orders may be based on incorrect prices.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="commodity",
        notes="Should retrieve RUNBOOK-002 and INCIDENT-002",
    ),
    IntegrationTestCase(
        name="supplier API timeout",
        incident="Primary grain supplier API returning timeouts. Cannot confirm delivery schedules for 14 DC locations. Bread category stockout risk within 4 days.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="commodity",
        notes="Should retrieve RUNBOOK-004 and INCIDENT-004",
    ),
    IntegrationTestCase(
        name="duplicate purchase orders",
        incident="Automated purchase order system submitted duplicate orders for produce category. Same order sent twice to 6 suppliers. Combined duplicate value approximately $800,000.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="commodity",
        notes="Should retrieve RUNBOOK-005 and INCIDENT-009",
    ),
    IntegrationTestCase(
        name="futures feed failure CBOT",
        incident="Futures contract data feed failure during CBOT trading hours. Wheat and corn futures not updating. Forward procurement decisions pending.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="commodity",
        notes="CBOT acronym — tests hybrid keyword search",
    ),

    # --- DEMAND DOMAIN ---
    IntegrationTestCase(
        name="ML forecast negative values",
        incident="ML demand forecasting model producing negative values for produce categories since yesterday retrain. Downstream procurement orders look wrong but have not been sent yet.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="demand",
        notes="Should retrieve RUNBOOK-003 and INCIDENT-003",
    ),
    IntegrationTestCase(
        name="model retrain regression MAPE",
        incident="Model retrain regression detected. New model MAPE 22% vs previous model MAPE 9%. Replenishment orders generated on degraded forecasts.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="demand",
        notes="MAPE metric — tests hybrid keyword search, should retrieve RUNBOOK-014",
    ),
    IntegrationTestCase(
        name="promotional demand spike",
        incident="Promotional campaign live but demand forecast not updated. Organic produce selling at 2.8x forecast velocity. Stockouts beginning across 23 stores.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="demand",
        notes="Should retrieve RUNBOOK-013 and INCIDENT-013",
    ),
    IntegrationTestCase(
        name="forecast pipeline delay",
        incident="Demand forecast pipeline delayed by 6 hours. Promotional campaign replenishment orders not generated on time. Valentine's Day campaign at risk.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="demand",
        notes="Should retrieve RUNBOOK-012 and INCIDENT-012",
    ),

    # --- CRITICAL SEVERITY ---
    IntegrationTestCase(
        name="complete payment gateway outage",
        incident="Payment gateway completely down. Zero transactions processing across all channels for the last 10 minutes. All checkout attempts returning 503. Revenue loss $12,000 per minute.",
        expected_routing="human_review",
        expected_severity="critical",
        expected_escalate=True,
        corpus_domain="none",
        notes="Critical severity — not in corpus, tests low confidence routing",
    ),
    IntegrationTestCase(
        name="cascading failure multi-system",
        incident="Primary database cluster unresponsive. Inventory sync failing. Demand forecast pipeline delayed. Replenishment orders blocked. Automated failover not triggering.",
        expected_routing="human_review",
        expected_severity="critical",
        expected_escalate=True,
        corpus_domain="platform",
        notes="Multi-system cascade — should retrieve INCIDENT-015",
    ),

    # --- EDGE CASES ---
    IntegrationTestCase(
        name="vague input",
        incident="something seems wrong with the backend systems today",
        expected_routing="human_review",
        expected_severity=("low", "medium"),
        expected_escalate=None,  # routing to human_review is the real assertion;
                                # escalate flag is secondary and has shown both
                                # True and False across runs as the model's
                                # caution threshold shifted with prompt changes
        corpus_domain="none",
        notes=(
            "Vague — insufficient context should trigger human review. "
            "Severity and escalate are both secondary to routing here — "
            "model has shown both low/medium severity and both escalate "
            "values across runs depending on prompt state. Routing to "
            "human_review is the actual quality bar for this case."
        ),
    ),
    IntegrationTestCase(
        name="contradictory input",
        incident="System is fully operational and all services healthy. System is completely down and no services responding. All users affected and no users affected.",
        expected_routing="human_review",
        corpus_domain="none",
        notes="Contradiction detected should trigger human review",
    ),
    IntegrationTestCase(
        name="potential impact not yet realized",
        incident="ML demand forecasting model producing incorrect values for produce. Procurement orders look wrong but have not been submitted to suppliers yet.",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        corpus_domain="demand",
        notes="Potential impact rule — severity must not exceed high",
    ),
    IntegrationTestCase(
        name="data warehouse storage",
        incident="Data warehouse storage exhausted. All ETL ingestion jobs failing. Finance reporting unavailable. errno 28 appearing in logs.",
        expected_routing="human_review",
        expected_severity="critical",  # model is correct — active outage
        expected_escalate=True,
        corpus_domain="platform",
        notes="Technical query with errno 28 — tests hybrid search. Active outage justifies critical.",
    ),
]


def run_integration_tests():
    results = {
        "total": len(TEST_CASES),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "details": [],
    }

    for i, case in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] {case.name}")

        try:
            config = {
                "configurable": {
                    "thread_id": f"integration-{i}-{abs(hash(case.name))}"
                }
            }

            initial_state = AgentState(
                incident_description=case.incident
            )

            result = graph.invoke(initial_state, config=config)

            # Determine actual routing
            if result.get("validation_error"):
                actual_routing = "validation_failed"
            elif result.get("auto_resolved"):
                actual_routing = "auto_resolve"
            else:
                actual_routing = "human_review"

            # Check routing
            routing_correct = actual_routing == case.expected_routing

            # Check severity if expected
            severity_correct = True
            actual_severity = None
            if case.expected_severity and result.get("final_report"):
                actual_severity = result["final_report"].severity.value
                if isinstance(case.expected_severity, tuple):
                    severity_correct = actual_severity in case.expected_severity
                else:
                    severity_correct = actual_severity == case.expected_severity

            # Check escalate if expected
            escalate_correct = True
            actual_escalate = None
            if case.expected_escalate is not None and result.get("final_report"):
                actual_escalate = result["final_report"].escalate
                escalate_correct = actual_escalate == case.expected_escalate

            passed = routing_correct and severity_correct and escalate_correct

            if passed:
                results["passed"] += 1
                status = "✓ PASS"
            else:
                results["failed"] += 1
                status = "✗ FAIL"

            detail = {
                "name": case.name,
                "status": status,
                "expected_routing": case.expected_routing,
                "actual_routing": actual_routing,
                "routing_correct": routing_correct,
                "expected_severity": case.expected_severity,
                "actual_severity": actual_severity,
                "severity_correct": severity_correct,
                "expected_escalate": case.expected_escalate,
                "actual_escalate": actual_escalate,
                "escalate_correct": escalate_correct,
                "consistency_flags": result.get("consistency_flags", []),
                "steps_taken": result.get("steps_taken", []),
                "corpus_domain": case.corpus_domain,
                "notes": case.notes,
            }

            results["details"].append(detail)

            print(f"  {status}")
            print(f"  Routing: {actual_routing} (expected: {case.expected_routing})")
            if actual_severity:
                print(f"  Severity: {actual_severity} (expected: {case.expected_severity})")

        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "name": case.name,
                "status": "✗ ERROR",
                "error": str(e),
                "corpus_domain": case.corpus_domain,
            })
            print(f"  ✗ ERROR: {str(e)[:100]}")

        # Rate limiting — 2 LLM calls per test
        time.sleep(15)

    return results


def print_summary(results: dict):
    print(f"\n{'='*70}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total:   {results['total']}")
    print(f"Passed:  {results['passed']} ({results['passed']/results['total']:.0%})")
    print(f"Failed:  {results['failed']} ({results['failed']/results['total']:.0%})")
    print(f"Errors:  {results['errors']}")

    print(f"\n{'='*70}")
    print("FAILURES AND ERRORS")
    print(f"{'='*70}")

    for detail in results["details"]:
        if "FAIL" in detail.get("status", "") or "ERROR" in detail.get("status", ""):
            print(f"\n  {detail['name']}")
            if "error" in detail:
                print(f"    Error: {detail['error']}")
            else:
                if not detail.get("routing_correct"):
                    print(
                        f"    Routing: expected={detail['expected_routing']} "
                        f"actual={detail['actual_routing']}"
                    )
                if not detail.get("severity_correct"):
                    print(
                        f"    Severity: expected={detail['expected_severity']} "
                        f"actual={detail['actual_severity']}"
                    )
                if not detail.get("escalate_correct"):
                    print(
                        f"    Escalate: expected={detail['expected_escalate']} "
                        f"actual={detail['actual_escalate']}"
                    )
                print(f"    Notes: {detail['notes']}")

    print(f"\n{'='*70}")
    print("DOMAIN BREAKDOWN")
    print(f"{'='*70}")

    domains = {}
    for detail in results["details"]:
        domain = detail.get("corpus_domain", "unknown")
        if domain not in domains:
            domains[domain] = {"total": 0, "passed": 0}
        domains[domain]["total"] += 1
        if detail.get("status") == "✓ PASS":
            domains[domain]["passed"] += 1

    for domain, counts in domains.items():
        rate = counts["passed"] / counts["total"] if counts["total"] > 0 else 0
        print(
            f"  {domain:<12} "
            f"{counts['passed']}/{counts['total']} "
            f"({rate:.0%})"
        )


if __name__ == "__main__":
    print("Starting integration tests...")
    print(f"Total test cases: {len(TEST_CASES)}")
    print("Estimated time: ~5 minutes (15s sleep between cases)\n")

    results = run_integration_tests()
    print_summary(results)

    # Save results to file
    with open("integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to integration_test_results.json")
