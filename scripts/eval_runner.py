from incident_triage.evals.retrieval_evals import (
    RETRIEVAL_TEST_CASES,
    evaluate_retrieval,
    print_eval_report,
)

if __name__ == "__main__":
    print("Running retrieval evals...")
    results = evaluate_retrieval(RETRIEVAL_TEST_CASES, top_k=5)
    print_eval_report(results)
