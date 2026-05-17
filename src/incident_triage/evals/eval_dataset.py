from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentEvalCase:
    """
    Ground truth case for agent evaluation.
    Defines what a correct investigation report looks like.
    """
    name: str
    incident: str
    corpus_domain: str

    # Expected routing
    expected_routing: str  # "auto_resolve", "human_review", "validation_failed"

    # Expected report fields
    expected_severity: Optional[str] = None
    expected_escalate: Optional[bool] = None

    # Expected retrieval
    expected_runbook: Optional[str] = None
    expected_incident: Optional[str] = None

    # Expected confidence range
    min_confidence: float = 0.0
    max_confidence: float = 1.0

    # Expected flags
    expect_contradiction: bool = False
    expect_insufficient_context: bool = False

    # LLM judge criteria
    judge_criteria: list[str] = field(default_factory=list)

    notes: str = ""


AGENT_EVAL_DATASET = [

    # --- IN-CORPUS: PLATFORM DOMAIN ---
    AgentEvalCase(
        name="inventory_sync_failure",
        incident="Inventory sync job failed at 3am. 2400 SKUs showing incorrect stock levels across 3 regional DCs. Downstream replenishment orders blocked.",
        corpus_domain="platform",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        expected_runbook="RUNBOOK-001",
        expected_incident="INCIDENT-001",
        min_confidence=0.7,
        max_confidence=1.0,
        judge_criteria=[
            "Immediate actions reference database connectivity or connection pool",
            "Report identifies inventory sync job as the primary affected system",
            "Report recommends checking sync job logs",
            "Severity is high not critical — potential impact not yet realized",
        ],
        notes="Core platform incident — should retrieve RUNBOOK-001 and produce specific actions",
    ),

    AgentEvalCase(
        name="etl_silent_failure",
        incident="ETL job ingesting POS transaction data completed with exit code 0 but downstream systems reporting stale data. No records appear to have been written.",
        corpus_domain="platform",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        expected_runbook="RUNBOOK-006",
        expected_incident="INCIDENT-006",
        min_confidence=0.6,
        max_confidence=1.0,
        judge_criteria=[
            "Report identifies silent failure pattern — exit code 0 with zero records",
            "Immediate actions include checking upstream ETL job not just downstream systems",
            "Report mentions schema change or data pipeline as likely cause",
        ],
        notes="Silent failure pattern — diagnosis should start upstream not downstream",
    ),

    # --- IN-CORPUS: COMMODITY DOMAIN ---
    AgentEvalCase(
        name="commodity_price_feed_stale",
        incident="Wheat commodity price feed not updating since 6am. Procurement model making sourcing decisions on stale price data. Purchase orders may be based on incorrect prices.",
        corpus_domain="commodity",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        expected_runbook="RUNBOOK-002",
        expected_incident="INCIDENT-002",
        min_confidence=0.7,
        max_confidence=1.0,
        # Commodity price feed — revised criteria
        judge_criteria=[
            "Report identifies procurement model as affected system",
            "Immediate actions include reviewing or pausing pending purchase orders",
            "Severity is high not critical — orders may be affected but not confirmed",
        ],
        # Remove: "Report mentions stale data guard or manual approval mode"
        notes="Commodity domain — should retrieve RUNBOOK-002",
    ),

    AgentEvalCase(
        name="duplicate_purchase_orders",
        incident="Automated purchase order system submitted duplicate orders for produce category. Same order sent twice to 6 suppliers. Combined duplicate value approximately $800,000.",
        corpus_domain="commodity",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        expected_runbook="RUNBOOK-005",
        expected_incident="INCIDENT-009",
        min_confidence=0.7,
        max_confidence=1.0,
        # Duplicate PO — revised criteria
        judge_criteria=[
            "Report identifies $800,000 duplicate value as primary risk",
            "Immediate actions include contacting suppliers to cancel duplicates",
            "Report recommends halting further automated orders",
        ],
        # Remove: perishable and idempotency criteria
        notes="Financial impact incident — actions should be time-sensitive",
    ),

    # --- IN-CORPUS: DEMAND DOMAIN ---
    AgentEvalCase(
        name="ml_forecast_negative_values",
        incident="ML demand forecasting model producing negative values for produce categories since yesterday retrain. Downstream procurement orders look wrong but have not been sent yet.",
        corpus_domain="demand",
        expected_routing="human_review",
        expected_severity="high",
        expected_escalate=True,
        expected_runbook="RUNBOOK-003",
        expected_incident="INCIDENT-003",
        min_confidence=0.7,
        max_confidence=1.0,
        judge_criteria=[
            "Report recommends halting pending procurement orders",
            "Report mentions model rollback as immediate action",
            "Severity is high not critical — orders not yet sent",
            "Report identifies retrain as the trigger event",
        ],
        notes="Potential impact rule — orders not sent so severity caps at high",
    ),

    # --- OUT-OF-CORPUS ---
    AgentEvalCase(
        name="payment_gateway_outage",
        incident="Payment gateway completely down. Zero transactions processing across all channels for the last 10 minutes. All checkout attempts returning 503. Revenue loss $12,000 per minute.",
        corpus_domain="none",
        expected_routing="human_review",
        expected_severity="critical",
        expected_escalate=True,
        min_confidence=0.0,
        max_confidence=0.5,
        judge_criteria=[
            "system_specific_confidence is low — payment systems not in corpus",
            "Report correctly identifies critical severity",
            "Immediate actions are generic not system-specific",
        ],
        notes="Out of corpus — confidence should be low, routing via severity not confidence",
    ),

    # --- EDGE CASES ---
    AgentEvalCase(
    name="vague_input",
    incident="something seems wrong with the backend systems today",
    corpus_domain="none",
    expected_routing="human_review",
    expected_severity=None,  # remove severity constraint — low or medium both valid
    expected_escalate=False,
    expect_insufficient_context=True,
    min_confidence=0.0,
    max_confidence=0.3,
    judge_criteria=[
        "insufficient_context flag is True",
        "system_specific_confidence is very low",
        "affected_systems is unknown or generic",
    ],
    notes="Vague input — model should flag insufficient context. Severity low or medium both acceptable.",
    ),

    AgentEvalCase(
        name="contradictory_input",
        incident="System is fully operational and all services healthy. System is completely down and no services responding.",
        corpus_domain="none",
        expected_routing="human_review",
        expect_contradiction=True,
        judge_criteria=[
            "contradiction_detected flag is True",
            "Report acknowledges conflicting information",
        ],
        notes="Contradictory input — model should detect contradiction",
    ),
]
