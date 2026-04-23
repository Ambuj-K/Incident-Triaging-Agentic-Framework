from incident_triage.evals.retrieval_evals import (
    RETRIEVAL_TEST_CASES,
    evaluate_retrieval,
    evaluate_hybrid_retrieval,
    print_eval_report,
)

if __name__ == "__main__":
    print("=== SEMANTIC SEARCH ===")
    semantic_results = evaluate_retrieval(RETRIEVAL_TEST_CASES, top_k=5)
    print_eval_report(semantic_results)

    print("\n=== HYBRID SEARCH ===")
    hybrid_results = evaluate_hybrid_retrieval(RETRIEVAL_TEST_CASES, top_k=5)
    print_eval_report(hybrid_results)

    print("\n=== COMPARISON ===")
    print(f"Runbook  P@1: {semantic_results['runbook_p1_rate']:.0%} → {hybrid_results['runbook_p1_rate']:.0%}")
    print(f"Incident P@1: {semantic_results['incident_p1_rate']:.0%} → {hybrid_results['incident_p1_rate']:.0%}")
    print(f"Both     P@1: {semantic_results['both_p1_rate']:.0%} → {hybrid_results['both_p1_rate']:.0%}")