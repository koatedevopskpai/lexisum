# Part 2 — The architecture: 8 decisions I'd defend in a code review

*Part 2 of 4. Building LexiSum in public — problem → architecture →
benchmarks → lessons learned. Full ADRs live in the repo at
`docs/ARCHITECTURE.md`.*

---

Last week I made the case for a **dual-engine** summariser: extractive
(verbatim clauses) + abstractive (plain-English briefing), with an auditor
between them. This week, the eight decisions that turned a demo into
something I'd ship — each recorded as an Architecture Decision Record (ADR)
in the repo.

## 1. Two engines, not one LLM

The single most important choice was refusing to make one model do both jobs.
The extractive engine isn't an LLM at all — it ranks sentences with
Sentence-BERT + TextRank and returns them unchanged. The LLM is allowed to
paraphrase *because it is explicitly not the compliance artifact*.

**Why:** the two jobs have incompatible failure modes. Separating them lets
you guarantee the property that matters for each.

## 2. Token-level verbatim auditing

`is_verbatim = sentence in source` produces false negatives on real contracts
(curly quotes, newlines, double spaces). LexiSum normalises, then checks a
contiguous token-subsequence. Fabrication still fails; formatting doesn't.

**Why:** the audit is the product. If it can't be trusted, nothing else
matters.

## 3. Dynamic context strategy (`auto` / `single_shot` / `chunked_recursive`)

The original prototype did `document_text[:12000]` — silently dropping the
termination clause from a 60-page contract. LexiSum counts tokens and either
does a single pass or sentence-aware overlapping chunks summarised *in
parallel* and merged. It never crashes on long documents, and never silently
truncates.

**Why:** correctness bugs disguised as cost optimisation are the worst kind.

## 4. Provider-agnostic via LiteLLM

OpenAI, Azure, GCP Vertex, AWS Bedrock — the only difference is a model id and
credentials. No code branches per cloud.

**Why:** the deployment matrix in the README is a table, not four codebases.

## 5. FinOps as a first-class feature

Every model is pre-priced. The UI shows an estimate before you commit; actual
token usage is logged as tagged JSON-lines. Estimates and actuals use the
*same* pricing table, so they reconcile.

**Why:** "how much will this cost?" shouldn't be an afterthought in production.

## 6. In-memory document export

DOCX/PDF are built into `io.BytesIO` buffers — no temp files, no cleanup, no
concurrency bugs. The same engine serves the Streamlit UI and the CLI.

## 7. Async batch processing with bounded concurrency

~200 contracts/day means you can't go one-at-a-time. `asyncio.Semaphore`
bounds in-flight requests; progress callbacks feed the UI and CLI.

## 8. Streamlit for the UI

A generator-based pipeline (`stream_summaries`) yields structured events the
UI renders progressively — including token-by-token streaming of the
abstractive output.

## The point

None of these are "features" — they're *risk controls*. Each one exists
because a specific failure mode was real and observed. That's the difference
between a repo that gets starred and a repo that gets used.

**Next week (Part 3):** the benchmarks — real numbers on 100 CUAD contracts,
including the result that disproved my own assumption about Sentence-BERT.

**Read the ADRs:** <REPO_URL>/blob/main/docs/ARCHITECTURE.md
**Try the demo:** <DEMO_URL>