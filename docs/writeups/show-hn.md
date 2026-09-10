# Show HN

**Title:**
> Show HN: LexiSum – Compliance-safe legal contract summarizer (verbatim clauses + plain-English briefings)

**URL:**
> <REPO_URL> (or <DEMO_URL> — HN allows either; link the demo if it's stable)

**Body:**

I built LexiSum after watching a legal team try to use an LLM to summarise
contracts. It worked until compliance asked the obvious question: *"Is this
the exact wording of the clause?"* It wasn't — the model had paraphrased, and
paraphrased legal text is useless for evidentiary review.

LexiSum splits the job into two engines:

- **Extractive** — selects the top-N most central sentences algorithmically
  (Sentence-BERT + TextRank) and returns them *verbatim*. A token-level
  auditor verifies every selected clause is an unmodified substring of the
  source, tolerant of whitespace/punctuation/quote differences but strict
  enough to reject anything fabricated.
- **Abstractive** — an LLM writes a 2-paragraph plain-English briefing for
  executives, streamed token-by-token.

A few things I cared about:

- **No silent truncation.** A context strategy (`auto`) counts tokens and
  either does a single-shot call or sentence-aware overlapping chunks
  summarised in parallel and merged. It never drops the termination clause
  because the doc was long.
- **FinOps from day one.** Every model is pre-priced, the UI shows an estimate
  before you commit, and actual token usage is logged with tags so estimates
  can be reconciled against reality.
- **Provider-agnostic.** LiteLLM means OpenAI/Azure/GCP/AWS is a model-id
  change, not a rewrite.
- **Reproducible benchmark.** Extractive engines are evaluated on CUAD
  (510 contracts, 13k expert annotations) with ROUGE; abstractive models with
  BERTScore + an LLM-as-judge rubric. `python -m benchmark.reproduce_all`
  regenerates every number.

Stack: Python, LiteLLM, Sentence-Transformers, spaCy, Streamlit, Docker.
29 tests, all offline.

Happy to answer questions about the audit approach, the chunking strategy, or
the cost model. It's not legal advice, and pricing is a snapshot — but the
architecture is the part I'd defend.

<REPO_URL>
