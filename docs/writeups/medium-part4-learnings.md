# Part 4 — What a rate-limit wall, a merge bug, and a failed hypothesis taught me about shipping LLM tooling

*Part 4 of 4. Building LexiSum in public — the retrospective and the ask.*

---

Over four weeks I built and benchmarked LexiSum in public. This final post is
the part nobody shows you: the failures, the costs, and what I'd do
differently. Then I'm asking for help.

## 1. A rate-limit wall, ~$1.60 and 90 minutes of retries

The abstractive benchmark fires one request per contract across three
providers. LiteLLM's `batch_completion` defaults to **100 workers** — so a
100-contract run fires 100 concurrent requests. On the first run:

- **Gemini free tier** hard-caps at **5 requests/minute**. 92 of 100 failed.
- **OpenAI** hit a **200k tokens/minute** cap mid-run.

The fix became **ADR-009**: chunk requests (`--batch-size 10`), bound
concurrency (`--max-concurrency 4`), retry with backoff, and a delay between
batches. The lesson isn't "add a sleep" — it's that **provider quota is the
binding constraint**, and any batch LLM pipeline that doesn't treat it as
first-class will fail in production exactly the way it failed in my benchmark.

## 2. A merge bug that cost ~$1.58

I added a "resume" feature so a partial run could continue without re-paying
for completed contracts. The first version had a bug: running a *single*
model overwrote the results file, silently deleting the other two models'
records. I had to re-run two models (~$1.58 of API spend) to recover.

The fix is committed with **three unit tests** that specifically guard
cross-model preservation. Lesson: **resumability is a correctness feature,
and it needs tests like one.**

## 3. The hypothesis that failed — and why I'm glad

I assumed Sentence-BERT would clearly beat TF-IDF on clause selection. It
didn't (MAP 0.735 vs 0.727 — essentially tied, ~300× slower). A general
sentence encoder adds little when the task is lexical and the domain is
formulaic.

I shipped the negative result in the README and the benchmark, because the
whole point of the benchmark is to replace assumptions with numbers. The
*next* experiment (legal-domain encoder, query-relevance objective) is now
obvious — and it's a great first contribution.

## 4. The real cost of the whole thing

| Line item | Cost |
|---|---|
| Extractive benchmark | $0 (local) |
| Abstractive generation (100 contracts × 3 models) | ~$2.70 |
| Judge calls (gpt-4o, 45) | ~$0.30 |
| Waste from the two failures above | ~$1.60 |
| **Total** | **~$4.60** |

Most of the cost was my own mistakes. That's a cheap tuition bill, and now
it's documented so nobody else pays it.

## The ask

LexiSum is a working personal reference project, but it's far from done.
The roadmap in the repo's Discussions has real candidates:

- **Fine-tuned Legal-BERT extractive engine**, benchmarked head-to-head
  against SBERT (the obvious next experiment).
- **Cloud storage ingestion** (`--from-s3`, `--from-gcs`).
- **Multi-tenant auth** for real deployments.

If any of that sounds like you, the repo has `good first issue` labels and a
contributing guide. Even simpler: **run `python -m benchmark.reproduce_all`
and post your numbers** — I'll add them to the README.

And if a legal or compliance team ever tells you "AI can't be trusted here" —
show them the part where a token-level auditor verifies every clause is
verbatim. That's the whole point.

**Repo:** <REPO_URL>
**Demo:** <DEMO_URL>
**Roadmap vote:** <REPO_URL>/discussions