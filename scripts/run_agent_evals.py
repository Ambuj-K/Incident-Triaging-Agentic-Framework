import warnings
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

import json
import time
from dotenv import load_dotenv
load_dotenv()

from incident_triage.evals.agent_evals import run_evals, print_eval_summary
from incident_triage.evals.eval_dataset import AGENT_EVAL_DATASET

if __name__ == "__main__":
    print("Running agent evals...")
    print(f"Total cases: {len(AGENT_EVAL_DATASET)}")
    print("Each case: 2 agent LLM calls + 1 judge call = 3 total")
    print(f"Estimated time: ~{len(AGENT_EVAL_DATASET) * 20 // 60 + 1} minutes\n")

    results = run_evals(AGENT_EVAL_DATASET, sleep_between=20)
    print_eval_summary(results)

    # Save results
    output = [
        {
            "case_name": r.case_name,
            "passed": r.passed,
            "routing_correct": r.routing_correct,
            "severity_correct": r.severity_correct,
            "confidence_in_range": r.confidence_in_range,
            "retrieval_correct": r.retrieval_correct,
            "judge_score": r.judge_score,
            "judge_reasoning": r.judge_reasoning,
            "actual_routing": r.actual_routing,
            "actual_severity": r.actual_severity,
            "actual_confidence": r.actual_confidence,
            "actual_runbook": r.actual_runbook,
            "consistency_flags": r.consistency_flags,
        }
        for r in results
    ]

    with open("agent_eval_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to agent_eval_results.json")
