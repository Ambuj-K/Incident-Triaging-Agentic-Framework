# Retrieval Pipeline Evolution Log

## Purpose
This document tracks every meaningful change made to the retrieval pipeline
after the initial implementation, including the problem observed, the fix
applied, and the lesson learned. Intended for revision, posterity, and
onboarding.

---

## Phase 1 — Schema and Structured Output (Week 2)

### Iteration 1.1 — Initial IncidentReport Schema
**Problem:** Raw LLM output had no enforcement. Confidence returned as string
"High" instead of float. Severity returned as "High" instead of enum value.
Fields silently dropped with no error signal. Word count constraints ignored.

**Fix:** Introduced Pydantic schema with:
- `Severity` enum enforcing low/medium/high/critical only
- `Complexity` enum enforcing simple/medium/complex only
- `float` fields with `ge=0.0, le=1.0` for confidence
- `field_validator` for summary word count
- `field_validator` for non-empty affected_systems

**Lesson:** Natural language instructions cannot enforce output structure.
Programmatic validation via Pydantic is the only reliable enforcement
mechanism.

---

### Iteration 1.2 — Split Confidence Into Two Fields
**Problem:** Single confidence field conflated general domain knowledge
with system-specific knowledge. Call 18 showed model correctly distinguishes
these — 95% on common causes, 0% on specific system. Single field lost
this signal.

**Fix:** Split into:
- `general_diagnosis_confidence` — confidence based on known failure patterns
- `system_specific_confidence` — confidence given available system context

**Lesson:** Schema design should reflect genuine semantic distinctions the
model can reason about. One field for two different things loses information.

---

### Iteration 1.3 — Added Structural Flags
**Problem:** Contradictory input (Call 33) and insufficient context (Call 39)
were expressed as prose, not as structured signals the pipeline could route on.

**Fix:** Added boolean fields:
- `contradiction_detected` — true if incident contains conflicting information
- `insufficient_context` — true if input lacks enough detail for reliable triage

**Lesson:** Every state the agent needs to act on must be a structured field,
not buried in prose. Prose cannot be routed on programmatically.

---

### Iteration 1.4 — Added Complexity Field
**Problem:** No complexity classification meant no basis for model routing in
cost optimization layer (Week 12). Agent had no signal for when to escalate
to more expensive models.

**Fix:** Added `complexity: Complexity` field with enum simple/medium/complex
and explicit definitions in system prompt.

**Lesson:** Design for downstream needs. The complexity field has no immediate
use in Week 2 but is the foundation for cost routing in Week 12. Retrofitting
schema fields later is messier than adding them early.

---

### Iteration 1.5 — System Prompt Evolution

**v1 — Basic prompt**
Generic triage instructions, no severity definitions, no confidence rules.
Result: severity defaulted to critical for ambiguous incidents, confidence
always 0.95-1.0 regardless of uncertainty.

**v2 — Added severity and confidence definitions**
Explicit severity definitions (critical/high/medium/low) and confidence
rules (below 0.7 if root cause unconfirmed).
Result: Severity calibrated correctly. Confidence improved but still
too high on unconfirmed root causes.

**v3 — Added explicit confidence thresholds and potential impact rule**
Added:
- Must be below 0.5 if no logs or diagnostic data provided
- Must be below 0.4 if no system context provided
- Must be below 0.3 if input is vague or ambiguous
- If potential impact not yet realized, severity must not exceed high

Result: Confidence correctly calibrated. ML forecasting incident correctly
classified high (not critical) because orders not yet sent. This is the
locked production system prompt.

**Lesson:** System prompt is engineered iteratively against observed failures,
not written correctly on the first attempt. Each iteration addresses a
specific observed miscalibration.

---

### Iteration 1.6 — Duplicate System Prompt Definitions Removed
**Problem:** Complexity definitions appeared twice in system prompt after
iterative editing. Duplicate definitions create ambiguity — model may
average them or pick the last one.

**Fix:** Removed second complexity definition block, kept the more detailed
first version.

**Lesson:** System prompts accumulate cruft during iteration. Audit for
duplicates after each round of changes.

---

## Phase 2 — Corpus Creation (Week 3, Days 1-3)

### Iteration 2.1 — YAML Frontmatter Added to All Documents
**Problem:** First 5 runbooks (RUNBOOK-001 through RUNBOOK-005) written
without YAML frontmatter. Ingestion pipeline cannot extract metadata for
filtering without consistent frontmatter across all documents.

**Fix:** Added YAML frontmatter block to all runbooks and incidents:
```yaml
---
doc_id: RUNBOOK-001
doc_type: runbook
team: platform_engineering
incident_family: data_pipeline
severity_range: [medium, high, critical]
systems: [...]
last_verified: 2026-03-01
last_incident: 2026-02-03
status: active
---
```

**Lesson:** Establish document standards before writing content, not after.
Retrofitting metadata to 15 documents is tedious. Retrofitting to 150
documents is a serious problem.

---

### Iteration 2.2 — Frontmatter Structure Corrected
**Problem:** Some runbooks had frontmatter in the wrong position — content
before the opening `---`. Frontmatter must be the very first content in the
file. Also discovered some files had duplicate metadata sections (human
readable metadata block AND YAML frontmatter).

**Fix:**
- Moved frontmatter to top of all files
- Removed duplicate human-readable metadata sections
- YAML frontmatter is the single source of truth for metadata

**Lesson:** Frontmatter parsers use exact pattern matching. A blank line
or any content before `---` breaks parsing silently — the file ingests
with no metadata rather than throwing an error.

---

### Iteration 2.3 — Timezone and Location Corrections
**Problem:** All runbooks and incidents used IST timestamps and referenced
Indian locations (Nagpur DC). Organisation is US/Europe based.

**Fix:**
- Changed all IST timestamps to EST
- Replaced Nagpur DC with Cincinnati DC
- Updated regional references to US/European contexts

**Lesson:** Domain realism matters for retrieval quality. An agent reasoning
about "Nagpur DC" in a US retail context will produce less coherent
investigation reports than one working with real regional contexts.

---

### Iteration 2.4 — Double .md Extension Fixed
**Problem:** INCIDENT-009 saved as
`INCIDENT-009-duplicate-purchase-order-2025-12-11.md.md` — double extension
caused by editor auto-appending .md to an already .md filename.

**Fix:**
```bash
mv INCIDENT-009...md.md INCIDENT-009...md
```

**Lesson:** Verify filenames after creation. Double extensions cause silent
ingestion failures — the file is found but may not be processed correctly
depending on the extension check logic.

---

## Phase 3 — Ingestion Pipeline (Week 3, Days 3-5)

### Iteration 3.1 — Initial Ingestion: 1 Chunk Per Document
**Problem:** First ingestion run produced exactly 1 chunk per document.
All 30 documents produced 30 total chunks. Chunker was not splitting on
section headers.

**Root cause:** Markdown files had no `##` header syntax. Section titles
were plain text lines with no markdown formatting:
Overview          ← plain text, no ## prefix
The inventory sync job...
Trigger Conditions  ← plain text, no ## prefix

**Fix:** Updated `chunk_by_section` to detect plain text headers by matching
against a known section name list in addition to `##` prefixed headers:
```python
KNOWN_SECTIONS = {
    "overview", "trigger conditions", "severity classification",
    "diagnostic steps", "resolution steps", "escalation criteria",
    "related systems", "historical notes", "incident summary",
    "timeline", "root cause", "contributing factors",
    "resolution", "impact", "follow-up actions",
    "related runbook", "lessons learned",
}
```

**Result:** 259 chunks from 30 documents (8-10 chunks per document).

**Lesson:** Chunking strategy must match actual document structure.
A chunker written for `##` headers on documents without `##` headers
produces exactly 1 chunk per document — the entire document as one unit.
Always debug chunk count before proceeding to embedding.

---

### Iteration 3.2 — Retrieval Quality: Wrong Documents Retrieved
**First retrieval test results (before fix):**
- Query 1 (inventory sync): RUNBOOK-003 at top, RUNBOOK-001 not in top 3
- Query 4 (duplicate POs): No runbooks retrieved at all

**Root cause analysis:** Two problems:
1. Title-only chunk (5 words: "RUNBOOK-001: Inventory Sync Job Failure")
   producing a near-meaningless embedding that polluted vector space
2. Chunks had no document identity — "The inventory sync job reconciles..."
   does not embed the fact that it is about RUNBOOK-001

**Fix 1 — Raise minimum chunk word count from 10 to 15:**
```python
if len(section_content.split()) < 15:
    continue
```
Eliminated title-only chunks.

**Fix 2 — Prepend doc_id and section name to chunk content:**
```python
content=f"{metadata.get('doc_id', '')}: {section_name}\n{section_content}"
```
Embedding now captures document identity alongside section content.

**Result after fix:**
- Query 1: RUNBOOK-001 at 0.741 (was not in top 3)
- Query 4: RUNBOOK-005 at 0.756 (was completely missing)
- 5 of 5 queries retrieving correct primary document on both sides

**Lesson:** Chunk content must be self-identifying. A chunk that makes sense
in isolation but loses its document context when embedded will not retrieve
correctly on document-specific queries. Prepending doc_id is a simple fix
with significant retrieval quality impact.

---

### Iteration 3.3 — Duplicate Results From Same Document
**Problem:** Query 4 returned RUNBOOK-005 twice in top 3 results — two
different sections from the same document both ranking highly. Wastes top_k
slots and gives the agent redundant context.

**Fix:** Added deduplication by doc_id in `search_similar`:
```python
seen_doc_ids = set()
for row in rows:
    doc_id = row[0]
    if deduplicate and doc_id in seen_doc_ids:
        continue
    seen_doc_ids.add(doc_id)
    results.append(...)
```
Fetch `top_k * 3` rows before deduplication to ensure enough unique
documents after filtering.

**Lesson:** Deduplication is always needed when chunking produces multiple
chunks per document. Without it, one highly relevant document can consume
all top_k slots leaving no room for other relevant documents.

---

### Iteration 3.4 — RUNBOOK-002 Missing From Commodity Price Feed Query
**Problem:** After deduplication, commodity price feed query returned only
RUNBOOK-015 (regional demand anomaly) at 0.306 for runbooks — completely
wrong document at low similarity.

**Root cause:** After deduplication the query was only retrieving top_k=5
rows total. With deduplication consuming rows, not enough rows were being
fetched to find RUNBOOK-002.

**Fix:** Updated `retrieve_for_incident` to request `top_k * 2` from
`search_similar` before returning `top_k` results:
```python
runbooks = retrieve(query, top_k=top_k * 2, doc_type="runbook")
return {"runbooks": runbooks[:top_k], ...}
```

**Result:** RUNBOOK-002 correctly retrieved at 0.701.

**Lesson:** Deduplication and filtering reduce your effective result set.
Always fetch more than you need before applying post-processing filters.
A good rule of thumb: fetch 3x your desired result count, filter, return top_k.

---

## Phase 4 — Infrastructure (Week 3, Days 1-2)

### Iteration 4.1 — Database Provider: Docker → Neon
**Problem:** Docker not available in local environment.

**Fix:** Switched to Neon (free hosted PostgreSQL with pgvector).
Region initially ap-southeast-1 (Singapore) caused DNS resolution failures
from local network. Switched to us-east-1 which resolved correctly.

**Lesson:** Cloud database providers are a valid alternative to local Docker
for development. Free tier limitations (auto-pause after 5 minutes inactivity)
require connection retry logic.

---

### Iteration 4.2 — Connection Retry for Neon Cold Starts
**Problem:** Neon free tier pauses projects after 5 minutes inactivity.
First connection after pause fails with DNS/connection error while project
wakes up.

**Fix:** Added retry with exponential backoff to `get_connection`:
```python
def get_connection(retries: int = 3, delay: int = 2):
    for attempt in range(retries):
        try:
            return psycopg2.connect(DATABASE_URL, sslmode="require",
                                    connect_timeout=10)
        except psycopg2.OperationalError:
            time.sleep(delay)
            delay *= 2
    raise last_error
```

**Lesson:** Cloud database cold starts are a production reality. Retry logic
with backoff is standard practice for any database connection that may
not be immediately available.

---

### Iteration 4.3 — Numpy Version Conflict
**Problem:** sentence-transformers pulled numpy 2.4.4 which is incompatible
with torch 2.2.2 compiled against numpy 1.x.

**Fix:** Pinned numpy below 2.0:
```toml
"numpy<2.0"
```

**Lesson:** When adding ML libraries to a project, pin transitive
dependencies that have known breaking changes between major versions.
Numpy 1.x vs 2.x is a known compatibility boundary for the entire
PyTorch/sentence-transformers ecosystem.

---

### Iteration 4.4 — Editable Install Not Creating .pth File
**Problem:** `uv pip install -e .` did not create the expected
`incident-triage.pth` file in site-packages. Scripts could not import
`incident_triage` package even after editable install.

**Fix (temporary):** Added `sys.path.insert` to all scripts:
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

**Fix (permanent, pending):** Added `[tool.hatch.build] sources = ["src"]`
to pyproject.toml. Permanent fix not yet verified — sys.path workaround
remains in scripts.

**Lesson:** src layout editable installs require explicit configuration
in the build backend. Hatchling requires `sources = ["src"]` to correctly
create the .pth file pointing to the src directory rather than the
project root.

---

## Current Baseline Metrics (End of Week 3)

### Retrieval Quality (Semantic Search Only)
Query                              Top Runbook         Score   Top Incident        Score
Inventory sync failure             RUNBOOK-001         0.741   INCIDENT-001        0.781
Commodity price feed failure       RUNBOOK-002         0.701   INCIDENT-002        0.762
ML forecast negative values        RUNBOOK-003         0.702   INCIDENT-003        0.670
Duplicate purchase orders          RUNBOOK-005         0.756   INCIDENT-009        0.780
Data warehouse storage exhaustion  RUNBOOK-008         0.637   INCIDENT-008        0.820

Primary document correct: 5/5 runbooks, 5/5 incidents
Average top-1 similarity: 0.707 runbooks, 0.763 incidents

### Corpus Stats
Total documents:  30 (15 runbooks, 15 incidents, 0 system docs)
Total chunks:     259
Chunks per doc:   8-10 average
Embedding model:  all-MiniLM-L6-v2 (384 dimensions)
Vector store:     pgvector on Neon PostgreSQL

### Known Issues and Pending Work

SYSTEM-inventory-management.md: frontmatter parsing failure (BOM/whitespace)
→ Fix in Week 4 when writing remaining system docs
IST timestamps in RUNBOOK-001: should be EST
→ Fix during Week 4 corpus additions
sys.path workaround in all scripts: packaging issue not permanently resolved
→ Investigate hatchling src layout fix
0 system docs ingested: systems/ folder empty
→ Write 5 system docs in Week 4


---

## Phase 5 — Retrieval Evals (Week 4)

### Overview
Built a formal eval framework to measure retrieval quality with precision
metrics against a ground truth dataset. Progressive query hardening revealed
the boundaries of semantic search and defined concrete targets for hybrid
search.

---

### Iteration 5.1 — Eval Framework Design
**Problem:** Retrieval quality was assessed qualitatively — eyeballing
results and judging whether the right document appeared. This is not
measurable, not repeatable, and cannot detect regressions when the
pipeline changes.

**Fix:** Built `RetrievalTestCase` dataclass and `evaluate_retrieval`
function measuring:
- Precision@1 (P@1): correct document in position 1
- Precision@3 (P@3): correct document in top 3
- Both P@1: correct runbook AND correct incident both at position 1

Ground truth dataset maps each query to an expected runbook and expected
incident. Eval runs retrieval against each query and compares top result
to ground truth.

**Design decision:** P@1 is the primary metric because your agent will
consume the top result first. P@3 is a secondary diagnostic — if P@3 is
high but P@1 is low, the right document exists in results but ranking
is wrong. If both are low, retrieval is fundamentally broken for that
query type.

**Lesson:** Quantitative evals are not optional. "Looks right to me" is
not a baseline. You cannot improve what you cannot measure and you cannot
detect regressions without a reproducible baseline number.

---

### Iteration 5.2 — Baseline on 10 Standard Queries
**Queries:** 10 detailed natural language incident descriptions closely
matching document content language.

**Results:**
Runbook  P@1: 100% (10/10)
Runbook  P@3: 100% (10/10)
Incident P@1: 100% (10/10)
Incident P@3: 100% (10/10)
Both     P@1: 100% (10/10)
Similarity range: 0.630 - 0.762

**Finding:** Semantic search performs perfectly on natural language queries
that use vocabulary close to document content. Doc ID prefixing and
section-based chunking are the primary contributors to this result.

**Caveat:** 100% on 10 hand-crafted queries is not production performance.
Test queries were written by the same person who wrote the documents,
using matching vocabulary. Real incidents use different language.

---

### Iteration 5.3 — First Hardening Round: 5 Shorter Queries
**Added queries:** Abbreviated, informal versions of the same incidents.
Examples:
- "PO duplication 6 suppliers"
- "sync job down DCs wrong stock"
- "errno 28 warehouse writes failing"
- "ML model retrain gone wrong produce negative"
- "spot market needed weather DC stockout risk"

**Results (15 total queries):**
Runbook  P@1: 100% (15/15)
Runbook  P@3: 100% (15/15)
Incident P@1: 100% (15/15)
Incident P@3: 100% (15/15)
Both     P@1: 100% (15/15)
Similarity range on short queries: 0.493 - 0.676

**Finding:** Semantic search handles abbreviated queries correctly even
at lower similarity scores (0.5 range). Doc ID prefixing means "PO
duplication" still surfaces RUNBOOK-005 because "RUNBOOK-005" and
"duplicate" coexist in chunk content.

**Observation:** Similarity scores on short queries are 0.1-0.2 lower
than on detailed queries. This is expected — less query content means
less signal for the embedding model. The correct documents still rank
first but with less margin over alternatives.

---

### Iteration 5.4 — Second Hardening Round: 5 Adversarial Queries
**Added queries:** Technical acronyms, exact metric values, and
near-miss disambiguation cases that semantic search is known to
handle poorly.
- "exit code 0 but nothing written"
- "ivfflat index OOM during ingestion"
- "CBOT hours grain API slow"
- "BGP routing issue all external APIs down"
- "retrain MAPE 22% previous 9%"

**Results (20 total queries):**
Runbook  P@1: 95%  (19/20)
Runbook  P@3: 100% (20/20)
Incident P@1: 80%  (16/20)
Incident P@3: 100% (20/20)
Both     P@1: 80%  (16/20)

**Per-query failures:**

| Query | Expected | Got | Issue |
|-------|----------|-----|-------|
| exit code 0 but nothing written | INCIDENT-006 | INCIDENT-002 | Exact phrase match needed |
| ivfflat index OOM during ingestion | INCIDENT-008 | INCIDENT-002 | Technical term, low similarity 0.243 |
| CBOT hours grain API slow | INCIDENT-004 | INCIDENT-002 | Acronym not in semantic space |
| retrain MAPE 22% previous 9% | RUNBOOK-014 | RUNBOOK-003 | Near-miss disambiguation |
| retrain MAPE 22% previous 9% | INCIDENT-003 | INCIDENT-012 | Metric values need exact match |

**Three failure mode categories identified:**

1. **Technical acronyms** — CBOT, MAPE, OOM, ivfflat
   Semantic search maps these to unrelated concepts or ignores them.
   BM25 keyword search handles exact term matching natively.

2. **Exact metric values** — "exit code 0", "22% MAPE", "9%"
   Semantic embedding treats numbers as tokens without understanding
   their significance as exact values. Keyword search matches exactly.

3. **Near-miss disambiguation** — RUNBOOK-003 vs RUNBOOK-014
   Both are ML forecasting documents. Semantic similarity scores are
   close. The specific technical term "MAPE" in the query should boost
   RUNBOOK-014 (model retrain regression) but semantic search cannot
   distinguish them on this signal.

**INCIDENT-002 false positive pattern:**
INCIDENT-002 (commodity price feed) appeared as the wrong result for
three different failures. This suggests INCIDENT-002 has broad semantic
overlap with multiple query types — likely because commodity price feed
failures share vocabulary with many other incident types. Worth monitoring
whether INCIDENT-002 continues to be a false positive attractor after
hybrid search.

---

### Iteration 5.5 — Targets Set for Hybrid Search
**Baseline (semantic only):**
Runbook  P@1: 95%
Incident P@1: 80%
Both     P@1: 80%

**Target (hybrid search):**
Runbook  P@1: 100%
Incident P@1: 95%+
Both     P@1: 95%+

**Specific failures hybrid search must fix:**
- CBOT acronym → INCIDENT-004
- ivfflat OOM → INCIDENT-008
- exit code 0 → INCIDENT-006
- MAPE metrics → RUNBOOK-014 and INCIDENT-003

**Approach:** Reciprocal Rank Fusion (RRF) combining:
- Vector similarity (existing semantic search)
- PostgreSQL full text search / BM25 keyword search (new)

RRF score = Σ 1/(k + rank) across both result lists where k=60
(standard value from original RRF paper). No weight tuning required —
RRF is robust to relative weighting across signal types.

---

## Decisions Locked

These decisions were made deliberately and should not be revisited
without a specific measurable reason:

1. **Chunking by section name** — not fixed token size, not by paragraph
2. **Minimum 15 words per chunk** — eliminates title-only noise chunks
3. **Doc ID prefixed to every chunk** — chunk content is self-identifying
4. **Deduplication by doc_id** — one result per document in top_k
5. **Fetch 3x before deduplication** — ensures enough unique docs after filtering
6. **all-MiniLM-L6-v2 embedding model** — 384 dimensions, no API dependency
7. **Neon PostgreSQL with pgvector** — no local Docker required
8. **Sentence-transformers with numpy<2.0** — pinned for compatibility
9. **Eval framework measures P@1 and P@3** — P@1 is primary metric,
   P@3 is diagnostic for ranking vs retrieval failures
10. **Progressive query hardening** — start with natural language,
   add abbreviated, add adversarial — reveals failure modes systematically
11. **RRF for hybrid fusion** — no weight tuning, robust combination
    of semantic and keyword signals