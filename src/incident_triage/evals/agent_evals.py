import os
import time
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from google import genai
from incident_triage.agent.graph import build_graph
from incident_triage.agent.state import AgentState
from incident_triage.evals.eval_dataset import AgentEvalCase, AGENT_EVAL_DATASET

graph = build_graph(interrupt_on_human_review=False)


@dataclass
class EvalResult:
    case_name: str
    passed: bool
    routing_correct: bool
    severity_correct: bool
    escalate_correct: bool
    confidence_in_range: bool
    retrieval_correct: bool
    contradiction_correct: bool
    insufficient_context_correct: bool
    judge_score: Optional[float]
    judge_reasoning: str
    actual_routing: str
    actual_severity: Optional[str]
    actual_confidence: Optional[float]
    actual_runbook: Optional[str]
    consistency_flags: list[str]
    notes: str


def run_agent(case: AgentEvalCase) -> dict:
    """Run agent on a single eval case and return result state."""
    config = {
        "configurable": {
            "thread_id": f"eval-{abs(hash(case.name))}"
        }
    }
    initial_state = AgentState(incident_description=case.incident)
    return graph.invoke(initial_state, config=config)


def llm_judge(
    incident: str,
    report: dict,
    criteria: list[str],
    context_used: str = "",
) -> tuple[float, str]:
    """
    Use Gemini to evaluate whether the investigation report
    meets the specified criteria.

    Returns (score 0.0-1.0, reasoning string)
    """
    if not criteria:
        return 1.0, "No criteria specified"

    criteria_text = "\n".join(f"- {c}" for c in criteria)

    prompt = f"""You are evaluating an AI incident triage system.

INCIDENT:
{incident}

INVESTIGATION REPORT:
Severity: {report.get('severity')}
Complexity: {report.get('complexity')}
Affected systems: {report.get('affected_systems')}
Summary: {report.get('summary')}
Immediate actions: {report.get('immediate_actions')}
Confidence: {report.get('system_specific_confidence')}
Escalate: {report.get('escalate')}
Contradiction detected: {report.get('contradiction_detected')}
Insufficient context: {report.get('insufficient_context')}

EVALUATION CRITERIA:
{criteria_text}

For each criterion, state whether it is MET or NOT MET and why.
Then provide an overall score from 0.0 to 1.0 where:
1.0 = all criteria fully met
0.7 = most criteria met with minor gaps
0.5 = some criteria met, significant gaps
0.3 = few criteria met
0.0 = criteria not met

Respond in this exact format:
CRITERIA ASSESSMENT:
[your assessment of each criterion]

OVERALL SCORE: [0.0-1.0]
REASONING: [one sentence summary]"""

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    text = response.text

    # Extract score
    score = 0.5  # default
    for line in text.split("\n"):
        if "OVERALL SCORE:" in line:
            try:
                score = float(line.split("OVERALL SCORE:")[-1].strip())
            except ValueError:
                pass

    # Extract reasoning
    reasoning = ""
    for line in text.split("\n"):
        if "REASONING:" in line:
            reasoning = line.split("REASONING:")[-1].strip()

    return score, reasoning


def evaluate_case(case: AgentEvalCase) -> EvalResult:
    """Run eval for a single case."""
    result = run_agent(case)

    # Determine actual routing
    if result.get("validation_error"):
        actual_routing = "validation_failed"
    elif result.get("auto_resolved"):
        actual_routing = "auto_resolve"
    else:
        actual_routing = "human_review"

    final_report = result.get("final_report")
    actual_severity = final_report.severity.value if final_report else None
    actual_confidence = (
        final_report.system_specific_confidence if final_report else None
    )

    # Check retrieval
    actual_runbook = None
    runbooks = result.get("retrieved_runbooks", [])
    if runbooks:
        actual_runbook = runbooks[0].get("doc_id")

    # Correctness checks
    routing_correct = actual_routing == case.expected_routing

    severity_correct = True
    if case.expected_severity and actual_severity:
        severity_correct = actual_severity == case.expected_severity

    escalate_correct = True
    if case.expected_escalate is not None and final_report:
        escalate_correct = final_report.escalate == case.expected_escalate

    confidence_in_range = True
    if actual_confidence is not None:
        confidence_in_range = (
            case.min_confidence <= actual_confidence <= case.max_confidence
        )

    retrieval_correct = True
    if case.expected_runbook and actual_runbook:
        retrieval_correct = actual_runbook == case.expected_runbook

    contradiction_correct = True
    if case.expect_contradiction and final_report:
        contradiction_correct = final_report.contradiction_detected

    insufficient_context_correct = True
    if case.expect_insufficient_context and final_report:
        insufficient_context_correct = final_report.insufficient_context

    # LLM judge
    judge_score = None
    judge_reasoning = "No report to evaluate"

    if final_report and case.judge_criteria:
        report_dict = {
            "severity": actual_severity,
            "complexity": final_report.complexity.value if final_report else None,
            "affected_systems": final_report.affected_systems if final_report else [],
            "summary": final_report.summary if final_report else "",
            "immediate_actions": final_report.immediate_actions if final_report else [],
            "system_specific_confidence": actual_confidence,
            "escalate": final_report.escalate if final_report else None,
            "contradiction_detected": final_report.contradiction_detected if final_report else None,
            "insufficient_context": final_report.insufficient_context if final_report else None,
        }
        judge_score, judge_reasoning = llm_judge(
            incident=case.incident,
            report=report_dict,
            criteria=case.judge_criteria,
        )

    # Overall pass/fail
    structural_pass = all([
        routing_correct,
        severity_correct,
        escalate_correct,
        confidence_in_range,
        retrieval_correct,
        contradiction_correct,
        insufficient_context_correct,
    ])

    judge_pass = judge_score is None or judge_score >= 0.7

    passed = structural_pass and judge_pass

    return EvalResult(
        case_name=case.name,
        passed=passed,
        routing_correct=routing_correct,
        severity_correct=severity_correct,
        escalate_correct=escalate_correct,
        confidence_in_range=confidence_in_range,
        retrieval_correct=retrieval_correct,
        contradiction_correct=contradiction_correct,
        insufficient_context_correct=insufficient_context_correct,
        judge_score=judge_score,
        judge_reasoning=judge_reasoning,
        actual_routing=actual_routing,
        actual_severity=actual_severity,
        actual_confidence=actual_confidence,
        actual_runbook=actual_runbook,
        consistency_flags=result.get("consistency_flags", []),
        notes=case.notes,
    )


def run_evals(
    dataset: list[AgentEvalCase] = None,
    sleep_between: int = 20,
) -> list[EvalResult]:
    """Run full eval suite."""
    if dataset is None:
        dataset = AGENT_EVAL_DATASET

    results = []

    for i, case in enumerate(dataset):
        print(f"\n[{i+1}/{len(dataset)}] {case.name}")
        try:
            result = evaluate_case(case)
            results.append(result)

            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {status}")
            print(f"  Routing: {result.actual_routing} "
                  f"(expected: {case.expected_routing})")
            if result.actual_severity:
                print(f"  Severity: {result.actual_severity}")
            if result.actual_confidence is not None:
                print(f"  Confidence: {result.actual_confidence:.2f} "
                      f"(range: {case.min_confidence}-{case.max_confidence})")
            if result.actual_runbook:
                print(f"  Top runbook: {result.actual_runbook} "
                      f"(expected: {case.expected_runbook})")
            if result.judge_score is not None:
                print(f"  Judge score: {result.judge_score:.2f}")
                print(f"  Judge: {result.judge_reasoning}")
            if result.consistency_flags:
                print(f"  Consistency flags: {result.consistency_flags}")

        except Exception as e:
            print(f"  ✗ ERROR: {str(e)[:100]}")
            results.append(EvalResult(
                case_name=case.name,
                passed=False,
                routing_correct=False,
                severity_correct=False,
                escalate_correct=False,
                confidence_in_range=False,
                retrieval_correct=False,
                contradiction_correct=False,
                insufficient_context_correct=False,
                judge_score=None,
                judge_reasoning=f"Error: {str(e)[:100]}",
                actual_routing="error",
                actual_severity=None,
                actual_confidence=None,
                actual_runbook=None,
                consistency_flags=[],
                notes=case.notes,
            ))

        time.sleep(sleep_between)

    return results


def print_eval_summary(results: list[EvalResult]):
    """Print formatted eval summary."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    judge_scores = [r.judge_score for r in results if r.judge_score is not None]
    avg_judge = sum(judge_scores) / len(judge_scores) if judge_scores else 0

    print(f"\n{'='*70}")
    print("AGENT EVAL SUMMARY")
    print(f"{'='*70}")
    print(f"Total:          {total}")
    print(f"Passed:         {passed} ({passed/total:.0%})")
    print(f"Failed:         {total-passed} ({(total-passed)/total:.0%})")
    print(f"Avg judge score: {avg_judge:.2f}")

    print(f"\n{'='*70}")
    print("PER-CASE RESULTS")
    print(f"{'='*70}")
    print(f"{'Case':<35} {'Route':<6} {'Sev':<5} {'Conf':<6} "
          f"{'Ret':<6} {'Judge':<6}")
    print("-"*70)

    for r in results:
        status = "✓" if r.passed else "✗"
        route = "✓" if r.routing_correct else "✗"
        sev = "✓" if r.severity_correct else "✗"
        conf = "✓" if r.confidence_in_range else "✗"
        ret = "✓" if r.retrieval_correct else "✗"
        judge = f"{r.judge_score:.2f}" if r.judge_score else "n/a"
        print(f"{status} {r.case_name:<33} {route:<6} {sev:<5} "
              f"{conf:<6} {ret:<6} {judge:<6}")

    print(f"\n{'='*70}")
    print("FAILURES")
    print(f"{'='*70}")
    for r in results:
        if not r.passed:
            print(f"\n  {r.case_name}")
            if not r.routing_correct:
                print(f"    Routing: actual={r.actual_routing}")
            if not r.severity_correct:
                print(f"    Severity: actual={r.actual_severity}")
            if not r.confidence_in_range:
                print(f"    Confidence: {r.actual_confidence}")
            if not r.retrieval_correct:
                print(f"    Retrieval: got={r.actual_runbook}")
            if r.judge_score and r.judge_score < 0.7:
                print(f"    Judge: {r.judge_score:.2f} — {r.judge_reasoning}")
