# What a LexiSum auditor pass means

The legacy `is_verbatim` name describes normalised source matching, not byte
identity. No extraction or matching algorithm changes are made by task L01.

1. Remove specified ASCII control characters; collapse whitespace; map the
   configured curly quotes, guillemets and en/em dashes to ordinary equivalents.
2. Accept if the non-empty normalised candidate is a substring of the normalised
   source. This can match a fragment inside a larger word or sentence.
3. Otherwise use spaCy tokenisation (installed model if available, blank English
   fallback otherwise), exclude punctuation/space tokens, and accept a contiguous
   equal token sequence. Token equality remains case-sensitive. This fallback
   does not establish equivalent punctuation or legal meaning.
4. Reject candidates that fail both checks. `audit_extractive` aggregates the
   individual results; an empty candidate list currently passes vacuously.

Examples: doubled whitespace or changed quote style can pass without exact byte
identity. A correctly copied but irrelevant sentence can pass. A substring of a
longer clause can pass while omitting an important condition. Therefore the
result does not establish complete clauses, correct selection, semantic support,
legal correctness, authenticity or tamper resistance.

The abstractive check accepts at least one non-empty paragraph block and a total
length greater than 50 characters. An unsupported summary can pass that check.
It is a structure check, not a fact checker or entailment evaluator.

## How to report the benchmark

In the published 100-contract extraction evaluation, all selected clauses passed
the normalised source-text auditor. That bounded rate is not an enforced promise
that the system can never fabricate. Published MAP remains Sentence-BERT 0.735
versus TF-IDF 0.727. The separate gpt-4o judge comparison sampled 15 summaries per
model, with GPT-4o-mini's published overall score 3.21/5. Published generation
costs are USD per contract. These runs have not been reproduced by L01.

Intended use: executive triage. Legal conclusions and generated summaries require
review. L02-L04 remain separate benchmark/semantic-evaluation tasks. The L05 practical
offline core is now recorded in docs/L05.md; it does not reproduce the benchmark.
