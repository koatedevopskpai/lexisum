# r/MachineLearning  `[P]`

**Title:**
> [P] LexiSum: a dual-engine legal summarizer with a token-level verbatim auditor and a reproducible CUAD benchmark

**Body:**

I wanted a project that treats *hallucination* as a measurable failure mode
rather than a caveat, so I built LexiSum — a contract summariser with two
independent engines and an evaluation harness on a public corpus.

**Method**

1. **Extractive engine.** TextRank over Sentence-BERT cosine similarities
   (`all-MiniLM-L6-v2`). Returns top-N sentences verbatim, in document order.
2. **Verbatim auditor.** Normalise (control chars, whitespace, Unicode
   quotes), then exact-substring match with a contiguous token-subsequence
   fallback. This removes the false negatives that a naive `in` check produces
   on real legal text while still rejecting fabricated content.
3. **Abstractive engine.** LLM summary via LiteLLM with a dynamic context
   strategy: single-shot when the document fits within 70% of the model's
   window, otherwise sentence-aware overlapping chunks summarised in parallel
   and merged.

**Evaluation (CUAD — 510 contracts, 13k expert annotations)**

- Extractive: ROUGE-1/2/L F1, latency, verbatim pass rate, with an Oracle
  upper bound from the gold clauses.
- Abstractive: BERTScore (`distilbert-base-uncased`) + a 5-dimension
  LLM-as-judge rubric (obligation coverage, risk/liability, termination
  clarity, plain language, faithfulness), plus cost per contract.

Everything is reproducible: `python -m benchmark.reproduce_all`. Results are
written to Markdown tables for direct inclusion in the README.

**What I'd like feedback on**

- Is the LLM-as-judge rubric reasonable for legal faithfulness, or should I
  move to human adjudication on a small sample?
- Chunk overlap is a fixed 10%; would a learned/dynamic overlap help?
- Any standard legal-summarisation baselines I'm missing (e.g. LexSumm, LexT5)?

Repo + numbers: <REPO_URL>
