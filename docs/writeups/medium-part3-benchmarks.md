# Part 3 — The benchmarks: real numbers, including the result that disproved my own assumption

*Part 3 of 4. Building LexiSum in public. Everything below is reproducible
with `python -m benchmark.reproduce_all` — no vibes, just numbers.*

---

Claims are cheap. So when I finished LexiSum's two engines, I benchmarked both
on a public legal corpus before publishing anything.

**Corpus:** CUAD (Contract Understanding Atticus Dataset) — 510 commercial
contracts with 13,000+ expert annotations across 41 clause types. I used a
100-contract sample.

## Extractive: TF-IDF vs Sentence-BERT

The extractive engine ranks sentences by how likely they are to contain an
expert-annotated clause. The natural metric is *ranking quality*: MAP and
nDCG@10, plus precision/recall at top-3.

| Method | MAP | nDCG@10 | Precision@3 | Latency | Verbatim |
|---|---|---|---|---|---|
| TF-IDF + TextRank | 0.727 | **0.855** | **0.883** | **0.005s** | 100% |
| Sentence-BERT + TextRank | **0.735** | 0.824 | 0.873 | 1.501s | 100% |
| Oracle (gold sentences) | 1.000 | 1.000 | 1.000 | 0.000s | 100% |

**The result that disproved my own assumption:** I expected the general
Sentence-BERT model to clearly beat TF-IDF. It didn't — essentially tied on
MAP, worse on nDCG@10, and ~300× slower. Legal clauses are formulaic, so
lexical overlap is already a strong signal. The lesson is in the README, not
hidden: a *general* encoder adds little; the next experiment is a
**legal-domain** encoder or a query-relevance objective.

## Abstractive: 3 models, 2 metrics, real cost

100 contracts, 2-paragraph executive briefings, judged by BERTScore (semantic
overlap with expert clauses) and a 5-dimension LLM-as-judge rubric
(obligations, risk/liability, termination, plain language, faithfulness).

| Model | BERTScore F1 | Rubric | Cost/contract |
|---|---|---|---|
| **gpt-4o-mini** | 0.768 | **3.21** | **$0.0017** |
| claude-haiku-4-5 | **0.776** | 2.95 | $0.0141 |
| gemini-3.6-flash | 0.702 | 1.63 | $0.0112 |

### What the numbers say

- **Claude Haiku 4.5** leads on BERTScore — its summaries most closely match
  the expert-annotated clauses.
- **GPT-4o-mini** wins the rubric (best obligation coverage and faithfulness)
  and is **~8× cheaper per contract** than Claude. At 200 contracts/day:
  ~$0.34 (gpt-4o-mini) vs ~$2.82 (claude-haiku-4-5).
- **Gemini Flash** trails on quality at a mid-tier price.

### The honest caveat

Rubric scores are modest overall (1.6–3.2). A 2-paragraph briefing cannot
cover the 20–50 clauses an expert flags in a typical CUAD contract — so
faithfulness is inherently bounded. That's a real property of the task, not a
model failure. It's exactly why the **extractive, verbatim engine exists as a
sibling**: the briefing is for humans, the exact clauses are for compliance.

## Reproduce it

```bash
pip install -r requirements.txt -r requirements-benchmark.txt
python -m benchmark.reproduce_all
```

Every number in this post regenerates from scratch. If you run it and get
different results, tell me — that's the point.

**Next week (Part 4):** what a rate-limit wall, a merge bug, and a failed
hypothesis taught me about shipping LLM tooling — plus the contribution ask.

**Repo:** <REPO_URL>
**Demo:** <DEMO_URL>