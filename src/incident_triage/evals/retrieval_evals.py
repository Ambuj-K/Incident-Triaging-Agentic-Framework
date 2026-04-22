from dataclasses import dataclass
from incident_triage.retrieval.retriever import retrieve_for_incident


@dataclass
class RetrievalTestCase:
    query: str
    expected_runbook: str
    expected_incident: str
    team: str
    incident_family: str


# Ground truth dataset
# These are the queries we know the correct answers for
RETRIEVAL_TEST_CASES = [
    RetrievalTestCase(
        query="Inventory sync job failed at 3am, 2400 SKUs showing incorrect stock levels across 3 DCs, replenishment orders blocked",
        expected_runbook="RUNBOOK-001",
        expected_incident="INCIDENT-001",
        team="platform_engineering",
        incident_family="data_pipeline",
    ),
    RetrievalTestCase(
        query="Commodity price feed not updating since 6am, procurement model operating on stale data, purchase orders may be affected",
        expected_runbook="RUNBOOK-002",
        expected_incident="INCIDENT-002",
        team="commodity_team",
        incident_family="supply_side",
    ),
    RetrievalTestCase(
        query="ML demand forecasting model producing negative values for produce categories after Sunday retrain",
        expected_runbook="RUNBOOK-003",
        expected_incident="INCIDENT-003",
        team="demand_forecast_team",
        incident_family="demand_side",
    ),
    RetrievalTestCase(
        query="Automated purchase order system submitted duplicate orders to produce suppliers, combined value $800,000",
        expected_runbook="RUNBOOK-005",
        expected_incident="INCIDENT-009",
        team="platform_engineering",
        incident_family="supply_side",
    ),
    RetrievalTestCase(
        query="Data warehouse storage exhausted, all ETL ingestion halted, finance reporting unavailable",
        expected_runbook="RUNBOOK-008",
        expected_incident="INCIDENT-008",
        team="platform_engineering",
        incident_family="data_pipeline",
    ),
    RetrievalTestCase(
        query="ETL job ingesting POS transaction data failed silently, wrote zero records, downstream forecast consumed stale data",
        expected_runbook="RUNBOOK-006",
        expected_incident="INCIDENT-006",
        team="platform_engineering",
        incident_family="data_pipeline",
    ),
    RetrievalTestCase(
        query="Primary grain supplier API returning timeouts, cannot confirm delivery schedules for DC locations",
        expected_runbook="RUNBOOK-004",
        expected_incident="INCIDENT-004",
        team="commodity_team",
        incident_family="supply_side",
    ),
    RetrievalTestCase(
        query="Futures contract data feed failure during active procurement window, forward contracts pending",
        expected_runbook="RUNBOOK-010",
        expected_incident="INCIDENT-010",
        team="commodity_team",
        incident_family="supply_side",
    ),
    RetrievalTestCase(
        query="Demand forecast pipeline delayed, promotional campaign replenishment orders not generated on time",
        expected_runbook="RUNBOOK-012",
        expected_incident="INCIDENT-012",
        team="demand_forecast_team",
        incident_family="demand_side",
    ),
    RetrievalTestCase(
        query="Promotional campaign live but forecast not updated, organic produce stockouts across stores",
        expected_runbook="RUNBOOK-013",
        expected_incident="INCIDENT-013",
        team="demand_forecast_team",
        incident_family="demand_side",
    ),
]


def evaluate_retrieval(
    test_cases: list[RetrievalTestCase],
    top_k: int = 5,
) -> dict:
    """
    Run retrieval evals against ground truth dataset.
    Measures precision@1, precision@3, and recall@5.
    """
    results = {
        "total": len(test_cases),
        "runbook_p1": 0,   # correct runbook in position 1
        "runbook_p3": 0,   # correct runbook in top 3
        "incident_p1": 0,  # correct incident in position 1
        "incident_p3": 0,  # correct incident in top 3
        "both_p1": 0,      # both correct in position 1
        "details": [],
    }

    for case in test_cases:
        retrieved = retrieve_for_incident(case.query, top_k=top_k)

        runbook_ids = [r["doc_id"] for r in retrieved["runbooks"]]
        incident_ids = [r["doc_id"] for r in retrieved["past_incidents"]]

        runbook_p1 = len(runbook_ids) > 0 and runbook_ids[0] == case.expected_runbook
        runbook_p3 = case.expected_runbook in runbook_ids[:3]
        incident_p1 = len(incident_ids) > 0 and incident_ids[0] == case.expected_incident
        incident_p3 = case.expected_incident in incident_ids[:3]
        both_p1 = runbook_p1 and incident_p1

        if runbook_p1:
            results["runbook_p1"] += 1
        if runbook_p3:
            results["runbook_p3"] += 1
        if incident_p1:
            results["incident_p1"] += 1
        if incident_p3:
            results["incident_p3"] += 1
        if both_p1:
            results["both_p1"] += 1

        top_runbook = retrieved["runbooks"][0] if retrieved["runbooks"] else None
        top_incident = retrieved["past_incidents"][0] if retrieved["past_incidents"] else None

        results["details"].append({
            "query": case.query[:60],
            "expected_runbook": case.expected_runbook,
            "got_runbook": runbook_ids[0] if runbook_ids else "none",
            "runbook_p1": runbook_p1,
            "runbook_similarity": top_runbook["similarity"] if top_runbook else 0,
            "expected_incident": case.expected_incident,
            "got_incident": incident_ids[0] if incident_ids else "none",
            "incident_p1": incident_p1,
            "incident_similarity": top_incident["similarity"] if top_incident else 0,
        })

    total = results["total"]
    results["runbook_p1_rate"] = results["runbook_p1"] / total
    results["runbook_p3_rate"] = results["runbook_p3"] / total
    results["incident_p1_rate"] = results["incident_p1"] / total
    results["incident_p3_rate"] = results["incident_p3"] / total
    results["both_p1_rate"] = results["both_p1"] / total

    return results


def print_eval_report(results: dict):
    """Print formatted eval report."""
    print("\n" + "="*60)
    print("RETRIEVAL EVAL REPORT")
    print("="*60)
    print(f"Total test cases: {results['total']}")
    print()
    print("PRECISION METRICS:")
    print(f"  Runbook  P@1: {results['runbook_p1_rate']:.0%} ({results['runbook_p1']}/{results['total']})")
    print(f"  Runbook  P@3: {results['runbook_p3_rate']:.0%} ({results['runbook_p3']}/{results['total']})")
    print(f"  Incident P@1: {results['incident_p1_rate']:.0%} ({results['incident_p1']}/{results['total']})")
    print(f"  Incident P@3: {results['incident_p3_rate']:.0%} ({results['incident_p3']}/{results['total']})")
    print(f"  Both     P@1: {results['both_p1_rate']:.0%} ({results['both_p1']}/{results['total']})")
    print()
    print("PER QUERY BREAKDOWN:")
    print(f"{'Query':<45} {'Runbook':<12} {'Incident':<12} {'R-Sim':<8} {'I-Sim':<8}")
    print("-"*85)
    for d in results["details"]:
        runbook_mark = "✓" if d["runbook_p1"] else "✗"
        incident_mark = "✓" if d["incident_p1"] else "✗"
        print(
            f"{d['query']:<45} "
            f"{runbook_mark} {d['got_runbook']:<10} "
            f"{incident_mark} {d['got_incident']:<10} "
            f"{d['runbook_similarity']:.3f}    "
            f"{d['incident_similarity']:.3f}"
        )
    print("="*60)
