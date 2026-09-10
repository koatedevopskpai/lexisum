# Dev.to / Medium article

**Title options**
- "Why I split my legal summarizer into two engines (and why the obvious LLM approach fails)"
- "Building a compliance-safe contract summarizer: verbatim extraction + plain-English LLMs"
- "Putting an audit layer around an LLM: a dual-engine legal summarizer"

---

## The problem: prose isn't admissible

When a legal team adopts an LLM summariser, the demo looks great and the
review fails. The reason is almost always the same: the summary is *prose*, and
prose paraphrases. Ask "is this the exact wording of the indemnification
clause?" and the honest answer is "no."

In regulated work, that's not a quality issue — it's a **trust** issue. If you
can't verify that a clause is unmodified, you can't rely on it.

I built **LexiSum** around that constraint. This post covers the architecture
and the specific decisions I'd defend in a code review.

---

## The core decision: two engines, not one

The single most important choice was refusing to make one LLM do both jobs.

| Engine | Job | Guarantee |
|---|---|---|
| Extractive | Surface the exact critical clauses | 100% verbatim |
| Abstractive | Explain them to non-lawyers | Readable + auditable |

The extractive engine is **not** an LLM. It ranks sentences with Sentence-BERT
embeddings + TextRank and returns them unchanged. The abstractive engine is an
LLM, and it's allowed to paraphrase — because it's explicitly not the
compliance artifact.

See `docs/ARCHITECTURE.md` for the full ADR set, but the short version: the
two jobs have incompatible failure modes. Separating them lets you guarantee
the property that matters for each.

---

## Making the verbatim guarantee real

The naive check is:

```python
is_verbatim = sentence in source_text
```

This produces false negatives constantly. Real contracts use curly quotes,
double spaces, and newlines. A clause can be genuinely verbatim and still fail
this test.

LexiSum normalises first (control chars, whitespace, Unicode quotes), then
tries an exact match, then falls back to a **contiguous token-subsequence**
match. Fabricated content still fails; formatting noise doesn't. The auditor
lives in `src/compliance/verbatim_auditor.py`.

---

## Never silently truncate

The original prototype did this:

```python
prompt = f"...{document_text[:12000]}"
```

For a 25-page contract, that silently drops everything after a few pages —
including, often, termination and liability clauses. That's a correctness bug
disguised as a cost optimisation.

LexiSum instead counts tokens with `tiktoken` and picks a strategy:

- **single_shot** — one call with the full document (best coherence).
- **chunked_recursive** — sentence-aware overlapping chunks, summarised *in
  parallel* with `asyncio.to_thread`, then merged.
- **auto** — single-shot when the doc fits within 70% of the model's context
  window, otherwise chunked.

Chunking at sentence boundaries (not raw token windows) means you never cut a
clause in half, and a 10% overlap preserves context across boundaries.

---

## Provider-agnostic by design

The same code targets OpenAI, Azure OpenAI, GCP Vertex, and AWS Bedrock. The
only difference is the model id and credentials. That's [LiteLLM] doing the
heavy lifting, and it's why the "cloud deployment" section of the README is a
matrix rather than four code branches.

---

## FinOps as a first-class feature

Cost is a feature, not a footnote. LexiSum:

1. Shows a **pre-flight estimate** in the UI before the user commits.
2. Logs **actual** token usage as tagged JSON-lines.
3. Uses the **same pricing table** for both, so estimates and actuals are
   directly comparable.

The tags (`environment`, `team`, `strategy`, `calls`) mean you can slice spend
by team or see how often the expensive chunked path triggers. This is the part
most side projects skip and most production reviews ask about.

---

## Reproducible evaluation

Claims are cheap. LexiSum benchmarks both engines on **CUAD** — 510 public
commercial contracts with 13,000+ expert annotations:

- Extractive: ROUGE-1/2/L, latency, verbatim pass rate, plus an Oracle upper
  bound from the gold clauses.
- Abstractive: BERTScore and a 5-dimension LLM-as-judge rubric, plus cost.

`python -m benchmark.reproduce_all` regenerates every number. The tables are
written straight to Markdown for the README.

---

## What I'd do differently / next

- A fine-tuned Legal-BERT extractor, benchmarked head-to-head with SBERT.
- Human adjudication on a small sample to validate the LLM judge.
- Cloud storage ingestion (`--from-s3`, `--from-gcs`) for batch pipelines.

---

## Try it

- Repo: <REPO_URL>
- Demo: <DEMO_URL>

If you build in a regulated domain, I'd love to hear whether verbatim auditing
is the right trust primitive, or whether clause-level diffs against a playbook
would be more useful.

*Not legal advice.*
