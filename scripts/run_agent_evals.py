import warnings
warnings.filterwarnings("ignore", message=".*Deserializing unregistered type.*")

import json
import time
from dotenv import load_dotenv
load_dotenv()

from incident_triage.evals.agent_evals import run_evals, print_eval_summary
from incident_triage.evals.eval_dataset import AGENT_EVAL_DATASET


def compare_to_baseline(
    results: list,
    baseline_path: str = "agent_eval_baseline.json",
) -> None:
    try:
        with open(baseline_path) as f:
            baseline = json.load(f)
    except FileNotFoundError:
        print("No baseline found — skipping regression check")
        return

    baseline_by_name = {r["case_name"]: r for r in baseline}

    print(f"\n{'='*70}")
    print("REGRESSION CHECK vs BASELINE")
    print(f"{'='*70}")

    regressions = []
    improvements = []

    for result in results:
        name = result.case_name
        if name not in baseline_by_name:
            continue

        baseline_score = baseline_by_name[name].get("judge_score") or 0
        current_score = result.judge_score or 0
        delta = current_score - baseline_score

        if delta < -0.1:
            regressions.append((name, baseline_score, current_score, delta))
        elif delta > 0.1:
            improvements.append((name, baseline_score, current_score, delta))

    if regressions:
        print("\n⚠  REGRESSIONS DETECTED:")
        for name, base, curr, delta in regressions:
            print(f"  {name}: {base:.2f} → {curr:.2f} ({delta:+.2f})")
    else:
        print("\n✓ No regressions detected")

    if improvements:
        print("\n↑  IMPROVEMENTS:")
        for name, base, curr, delta in improvements:
            print(f"  {name}: {base:.2f} → {curr:.2f} ({delta:+.2f})")


if __name__ == "__main__":
    print("Running agent evals...")
    print(f"Total cases: {len(AGENT_EVAL_DATASET)}")
    print("Each case: 2 agent LLM calls + 1 judge call = 3 total")
    print(
        f"Estimated time: "
        f"~{len(AGENT_EVAL_DATASET) * 20 // 60 + 1} minutes\n"
    )

    results = run_evals(AGENT_EVAL_DATASET, sleep_between=20)
    print_eval_summary(results)
    compare_to_baseline(results)

    output = [
        {
            "case_name": r.case_name,
            "passed": r.passed,
            "routing_correct": r.routing_correct,
            "severity_correct": r.severity_correct,
            "escalate_correct": r.escalate_correct,
            "confidence_in_range": r.confidence_in_range,
            "retrieval_correct": r.retrieval_correct,
            "contradiction_correct": r.contradiction_correct,
            "insufficient_context_correct": r.insufficient_context_correct,
            "judge_score": r.judge_score,
            "judge_reasoning": r.judge_reasoning,
            "actual_routing": r.actual_routing,
            "actual_severity": r.actual_severity,
            "actual_confidence": r.actual_confidence,
            "actual_runbook": r.actual_runbook,
            "consistency_flags": r.consistency_flags,
            "immediate_actions": r.immediate_actions,
            "summary": r.summary,
        }
        for r in results
    ]

    with open("agent_eval_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to agent_eval_results.json")
