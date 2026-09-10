# Part 1 — Why "just ask ChatGPT" fails for legal contracts

*This is part 1 of a 4-part series building LexiSum in public. Follow along as
we go from problem → architecture → benchmarks → lessons learned.*

---

Every legal-tech demo goes the same way. Someone uploads a 25-page contract,
an LLM produces a beautiful summary, everyone nods. Then compliance asks the
question that ends the demo:

> "Is that the exact wording of the indemnification clause?"

And the answer is *no*. The model paraphrased. Paraphrased legal text is not
admissible for evidentiary review, and the whole tool gets shelved.

That is not an LLM quality problem. It's a **task-design** problem.

## The tension legal teams actually live in

Legal work needs two different things from the same document:

1. **Compliance** needs the *exact* wording of critical clauses — word for
   word, no paraphrase, no hallucination, nothing invented.
2. **Executives** need a plain-language briefing — obligations, liabilities,
   termination terms — that a non-lawyer can actually read.

Those are incompatible jobs. You cannot guarantee verbatim fidelity and
produce readable prose in the same output. An LLM summariser optimises for
*fluency*, which is exactly what compliance can't trust.

## The fix: stop asking one model to do both

I built **LexiSum** around a simple split — two independent engines:

- **Extractive engine** (no LLM): algorithmically selects the most central
  sentences and returns them *verbatim*. A token-level auditor then verifies
  each clause is an unmodified substring of the source. Zero hallucination by
  construction.
- **Abstractive engine** (LLM): a separate model writes a two-paragraph
  plain-English briefing for the executives.

Compliance gets exact text. Executives get readability. Neither side
compromises, and the audit trail is clean.

## What "verbatim" actually requires

The naive check is `sentence in source_text`. It fails constantly: contracts
use curly quotes, double spaces, and newlines. A clause can be genuinely
verbatim and still fail that test. LexiSum normalises first (control chars,
whitespace, Unicode quotes), then falls back to a **contiguous
token-subsequence** match. Fabricated content still fails; formatting noise
doesn't.

## Why this matters beyond legal

This is the pattern for any regulated domain: finance, insurance, healthcare,
government. Whenever an LLM's output must be *verifiable*, you separate the
"must be exact" step from the "can be fluent" step and audit the seam between
them.

## The plan

- **Part 2 (next week):** the architecture — 8 decisions I'd defend in a code
  review, with ADRs.
- **Part 3:** the benchmarks — real numbers on 100 contracts, including the
  result that disproved my own assumption.
- **Part 4:** what a rate-limit wall and a merge bug taught me about shipping
  LLM tooling.

**Try it live:** <DEMO_URL>
**Repo:** <REPO_URL>

*Not legal advice. It's a triage tool with an audit trail — not a
replacement for counsel.*