# Architecture

LexiSum is a **dual-engine** contract summarisation system. It deliberately
separates the two summarisation paradigms that legal work demands:

| Engine | Goal | Guarantee |
|---|---|---|
| **Extractive** | Surface the *exact* critical clauses | 100% verbatim, no hallucination |
| **Abstractive** | Explain obligations/risks in plain language | Faithful, readable, auditable |

A **compliance auditor** sits across both outputs, and a **FinOps tracker**
records the true cost of every LLM call.

## High-level flow

```
Raw contract text
      |
      v
+-------------------+     +----------------------+
| Ingestion &       |     |  Context strategy    |
| sentence parsing  |     |  (auto/single/chunk) |
+---------+---------+     +----------+-----------+
          |                          |
          |  [Extractive]            |  [Abstractive]
          v                          v
+-------------------+     +----------------------+
| Sentence-BERT     |     | LLM (streaming,      |
| TextRank ranker   |     | chunked-recursive)   |
+---------+---------+     +----------+-----------+
          |                          |
          v                          v
+-------------------+     +----------------------+
| Top-N verbatim    |     | 2-paragraph plain    |
| clauses           |     | language summary     |
+---------+---------+     +----------+-----------+
          |                          |
          +------------+-------------+
                       v
            +----------------------+
            | Compliance audit     |
            | (token-level match)  |
            +----------+-----------+
                       v
            +----------------------+
            | FinOps cost log      |
            | estimates vs actuals |
            +----------------------+
```

## Module map

| Path | Responsibility |
|---|---|
| `src/config.py` | Env-driven settings, model context limits, provider config |
| `src/ingestion/` | Sentence parsing + PDF/DOCX/TXT + cloud OCR adapters |
| `src/extractive/` | TF-IDF (baseline) and Sentence-BERT (recommended) TextRank |
| `src/abstractive/` | LiteLLM generator: streaming, chunking, usage accounting |
| `src/compliance/` | Token-level verbatim auditor |
| `src/export/` | In-memory DOCX/PDF briefing generation |
| `src/cost/` | Pricing table + FinOps estimator/logger |
| `src/pipeline.py` | Orchestration + structured streaming events |
| `src/batch_processor.py` | Async, concurrency-bounded batch processing |
| `app.py` | Streamlit UI |
| `main.py` | CLI batch entrypoint |
| `benchmark/` | CUAD-based extractive + abstractive benchmarks |

---

# Architecture Decision Records

## ADR-001: Decouple extractive and abstractive engines

**Context.** A single LLM summary cannot satisfy both compliance (exact
wording) and readability (plain language). LLMs paraphrase and can
hallucinate, which is unacceptable for evidentiary review.

**Decision.** Run two independent engines and reconcile their outputs. The
extractive engine selects verbatim clauses algorithmically; the abstractive
engine produces a plain-language briefing.

**Consequences.**
- (+) Compliance teams get unmodified clause text; executives get readable prose.
- (+) Failure of one engine does not corrupt the other.
- (−) Two code paths to maintain and test.

---

## ADR-002: Token-level verbatim auditing instead of substring matching

**Context.** The naive check `sentence in source` produces false negatives
when punctuation, whitespace, or Unicode curly quotes differ between the
extracted sentence and the source.

**Decision.** Normalise (control chars, whitespace, quotes) then first try an
exact normalised-substring match, falling back to a **contiguous
token-subsequence** match.

**Consequences.**
- (+) Robust to real-world formatting noise; no false compliance failures.
- (+) Still strict — fabricated content is correctly rejected.
- (−) Slightly more CPU per sentence (negligible).

---

## ADR-003: Dynamic context strategy (`auto` / `single_shot` / `chunked_recursive`)

**Context.** Large-context models give the best coherence but are expensive;
small models are cheap but truncate long contracts. Arbitrary truncation
(`text[:12000]`) silently drops critical clauses.

**Decision.** Count tokens with `tiktoken`, then choose per-document:
- `auto` (default): single-shot if tokens ≤ 70% of the model's window, else chunked-recursive.
- Chunking is **sentence-aware** with a configurable overlap (default 10%).
- Chunk summaries are computed **in parallel** via `asyncio.to_thread`.

**Consequences.**
- (+) Never hits `context_length_exceeded`; no silent data loss.
- (+) Users can force a strategy for cost/latency control.
- (−) Chunked mode makes N+1 LLM calls (more expensive, but can use cheaper models).

---

## ADR-004: Provider-agnostic via LiteLLM

**Context.** The brief spans Azure OpenAI, GCP Vertex Gemini, and AWS Bedrock.

**Decision.** Route all LLM calls through LiteLLM. Provider selection is a
model-id + credential change, not a code change.

**Consequences.**
- (+) One codebase serves all three clouds; easy local OpenAI testing.
- (+) Streaming, usage reporting, and `batch_completion` work uniformly.
- (−) One extra dependency and an abstraction layer.

---

## ADR-005: FinOps tracking with estimates *and* actuals

**Context.** Users choose a model before seeing the cost, and teams need to
reconcile spend. The user explicitly asked for FinOps tagging and estimate-vs-actual comparison.

**Decision.** A single `pricing` module is the source of truth for both the
pre-flight estimate (UI) and the post-run actual cost log. Every record is
tagged with `environment`, `team`, `strategy`, `calls`, and `top_n` and
written as JSON-lines for easy ingestion into any analytics stack.

**Consequences.**
- (+) Estimates and actuals are always comparable (same prices).
- (+) Tag-based cost attribution across teams/environments.
- (−) Pricing is a snapshot and must be updated as providers change rates.

---

## ADR-006: In-memory document export

**Context.** Generating DOCX/PDF via temp files creates cleanup, concurrency,
and security concerns.

**Decision.** Build reports into `io.BytesIO` buffers and return bytes.
Streamlit download buttons and the CLI both consume the same bytes.

**Consequences.**
- (+) No temp files, no cleanup, safe for concurrent use.
- (+) Same engine serves UI and CLI.

---

## ADR-007: Async batch processing with bounded concurrency

**Context.** The target workload is ~200 contracts/day. Sequential processing
wastes wall-clock time and does not respect provider rate limits if unbounded.

**Decision.** `BatchProcessor` uses an `asyncio.Semaphore` to bound
concurrency and runs the (CPU/sync) pipeline in a thread via
`asyncio.to_thread`. Progress callbacks feed the UI/CLI.

**Consequences.**
- (+) High throughput with a configurable safety limit on API pressure.
- (+) Progress is observable.
- (−) Concurrency must be tuned per provider quota.

---

## ADR-008: Streamlit for the UI

**Context.** The project needs a demonstrable, low-friction UI that supports
live streaming and file uploads without a separate frontend build.

**Decision.** Streamlit, with a generator-based pipeline (`stream_summaries`)
that yields structured events the UI renders progressively.

**Consequences.**
- (+) Fast to build, one-command deploy to Streamlit Community Cloud.
- (+) Native streaming and download buttons.
- (−) Not suitable for high-scale multi-tenant production (documented as future work).