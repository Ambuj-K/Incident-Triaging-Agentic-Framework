The end goal is to have a functional agentic pipeline incorporating custom evals for an incident triaging usecase concerned with forecasting avilability of retail goods.

testcases (added evals)

┌─────────────────────────────────────────────────────────────────┐
│                    INCIDENT TRIAGE AGENT                        │
│                                                                 │
│  Natural Language Incident                                      │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │ validate_input  │ ← InputValidator (security layer)          │
│  └────────┬────────┘                                            │
│           │ valid / invalid                                     │
│    ┌──────┴──────┐                                              │
│    │             │                                              │
│    ▼             ▼                                              │
│  request_    classify_incident  ← Pass 1 LLM (Gemini Flash)     │
│  clarification  │               ← @observe span                 │
│    │            │ affected_systems                              │
│    │            ▼                                               │
│    │    retrieve_context       ← Hybrid Search                  │
│    │         │                 ← pgvector + BM25                │
│    │         │                 ← @observe span                  │
│    │         │ runbooks + incidents                             │
│    │         ▼                                                  │
│    │  investigate_with_context ← Pass 2 LLM (Gemini Flash)      │
│    │         │                 ← @observe span                  │
│    │         │ final_report + confidence_delta                  │
│    │    ┌────┴────┐                                             │
│    │    │  route  │ ← multi-signal routing                      │
│    │    └────┬────┘                                             │
│    │    escalate?  confidence<0.4?  consistency_flags?          │
│    │    contradiction?  complexity=complex?                     │
│    │         │                                                  │
│    │   ┌─────┴──────┐                                           │
│    │   │            │                                           │
│    ▼   ▼            ▼                                           │
│  END  human_review  auto_resolve                                │
│       (interrupt)   (low sev +                                  │
│       state update  high conf)                                  │
│       resume                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL LAYER                              │
│                                                                 │
│  Query (incident_description + affected_systems)                │
│           │                                                     │
│    ┌──────┴──────┐                                              │
│    │             │                                              │
│    ▼             ▼                                              │
│  Vector Search  Keyword Search (BM25)                           │
│  all-MiniLM     PostgreSQL FTS                                  │
│  384 dims       OR logic                                        │
│  pgvector       technical terms only                            │
│    │             │                                              │
│    └──────┬──────┘                                              │
│           │                                                     │
│    Reciprocal Rank Fusion                                       │
│    vector 0.7 + keyword 0.3                                     │
│           │                                                     │
│    Deduplicate by doc_id                                        │
│           │                                                     │
│    Top 3 runbooks + Top 3 incidents                             │
│           │                                                     │
│    format_context() → context string → Pass 2                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CORPUS                                       │
│                                                                 │
│  data/runbooks/                                                 │
│    platform/    6 runbooks  (ETL, sync, warehouse, schema)      │
│    commodity/   4 runbooks  (price feed, supplier, futures)     │
│    demand/      5 runbooks  (forecast, promo, retrain)          │
│                                                                 │
│  data/incidents/                                                │
│    platform/    6 incidents                                     │
│    commodity/   5 incidents                                     │
│    demand/      4 incidents                                     │
│                                                                 │
│  30 documents → 259 chunks → 384-dim embeddings → pgvector      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY (Langfuse v4)                  │
│                                                                 │
│  incident_investigation  [root trace @observe]                  │
│    ├── classify_incident    [span @observe]                     │
│    │     input: incident text                                   │
│    │     output: severity, affected_systems, confidence         │
│    ├── retrieve_context     [span @observe]                     │
│    │     input: affected_systems                                │
│    │     output: runbooks_retrieved, incidents_retrieved        │
│    └── investigate_with_context [span @observe]                 │
│          input: context_length, runbooks_used, incidents_used   │
│          output: severity, confidence, confidence_delta,        │
│                  escalate, consistency_flags                    │
│                                                                 │
│  Key metric: confidence_delta (Pass1 → Pass2)                   │
│    +0.50 = relevant context found, grounded report              │
│    -0.25 = irrelevant context, model correctly uncertain        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
│                                                                 │
│  Layer 1: InputValidator     — before any LLM call              │
│  Layer 2: RetrievalSanitizer — before context passed to LLM     │
│  Layer 3: Pydantic schema    — enforces output structure        │
│  Layer 4: ActionGuard        — tool risk classification (W14)   │
│  Layer 5: AuditLogger        — immutable audit trail            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    TWO-PASS PIPELINE                            │
│                                                                 │
│  Pass 1: classify_incident                                      │
│    No context → LLM → IncidentReport                            │
│    confidence: 0.35-0.50 (expected low)                         │
│    affected_systems → used as retrieval query                   │
│                                                                 │
│  Retrieval: retrieve_for_incident                               │
│    affected_systems → infer_metadata_filters                    │
│    → hybrid_search (vector + BM25) → top 3 per corpus type      │
│    → format_context (800 char truncation per chunk)             │
│                                                                 │
│  Consistency check: check_report_consistency                    │
│    severity_escalated_with_context                              │
│    affected_systems_significantly_changed                       │
│    confidence_dropped_with_context                              │
│    escalation_flipped                                           │
│                                                                 │
│  Pass 2: investigate_with_context                               │
│    Context → LLM → IncidentReport (grounded)                    │
│    confidence: 0.70-0.95 (relevant) or 0.10 (irrelevant)        │
│                                                                 │
│  Confidence delta = primary quality signal                      │
└─────────────────────────────────────────────────────────────────┘
