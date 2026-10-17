# Evidence index — LexiSum

Five-minute route: this file → [auditor semantics](docs/AUDITOR_SEMANTICS.md) →
[source auditor](src/compliance/verbatim_auditor.py) →
[boundary tests](tests/test_auditor_boundaries.py) → [dated offline result](evidence/L05.md).

## What it is

A public contract-summary reference build: clause extraction, a normalised
source-text auditor, LLM-generated briefings through LiteLLM, usage accounting and
DOCX/PDF exports. Intended use is executive triage. Legal conclusions and generated
summaries require review. This repository does not establish commercial deployment,
legal correctness or a banking track record.

## Inspectable engineering contribution

| Area | Source and trade-off |
|---|---|
| Document parsing | [parser](src/ingestion/document_parser.py) |
| TF-IDF/TextRank clause selection | [extractor](src/extractive/textrank_extractor.py) |
| Sentence-BERT alternative | [SBERT extractor](src/extractive/sbert_extractor.py) |
| Normalised source auditor | [auditor](src/compliance/verbatim_auditor.py), [precise semantics](docs/AUDITOR_SEMANTICS.md) |
| Generated summaries and orchestration | [LiteLLM integration](src/abstractive/llm_generator.py), [pipeline](src/pipeline.py) |
| Cost and export boundaries | [accounting](src/cost/cost_tracker.py), [exports](src/export/document_generator.py) |
| Reproducible offline checks | [lock](requirements-offline.lock), [profile](pytest-offline.ini), [test contracts](tests/offline/test_core_contract.py) |

These are inspectable implementation areas, not a claim of unaided authorship or
commercial adoption. Design rationale is in [ARCHITECTURE](docs/ARCHITECTURE.md).

## Strongest directly reproduced result

L05 recorded **27 passed, zero failures/errors/skips**, in a fresh locked CPython
3.12 environment on 17 October 2026. See [run evidence](evidence/L05.md) and
[scope/commands](docs/L05.md). It exercises parsing, real TF-IDF/TextRank extraction,
the normalised auditor, structural/content exports and usage accounting. SBERT
selection uses fixed embeddings; the estimator uses a fixed encoder. No provider
calls, model download, semantic embedding validation or rendered-layout QA ran.
The original L05 evidence did not execute Ubuntu Actions locally; its local
result must not be restated as a Linux runtime validation or a fresh benchmark.

## Published historical evaluation — not rerun by L01/L05 or this index

[The published benchmark narrative](docs/writeups/medium-part3-benchmarks.md) and
[auditor scope correction](docs/AUDITOR_SEMANTICS.md) report 100 contracts, MAP
0.735 for Sentence-BERT versus 0.727 for TF-IDF, and a 100% normalised source-match
rate for the selected clauses **in that evaluation**. They separately report a
15-summary-per-model comparison and GPT-4o-mini's 3.21/5 overall judge score.
Treat these as historical published results whose full reproduction remains
separate, not numbers established by the 27 offline checks. Published costs are
USD per contract; a GBP conversion needs a dated rate and is not inferred here.

Do not turn the normalised source-match rate into byte identity, correct clause
selection, complete conditions, faithful generated summaries or a promise that
fabrication is impossible. No output constraint here establishes such a promise.

## Reproduce the offline result

```sh
python -m venv .venv
# Activate using your shell's normal command, then:
python -m pip install -r requirements-offline.lock
python -m pytest -c pytest-offline.ini --junitxml=artifacts/offline-results.xml
```

Python 3.12 is the locked profile. Installation needs a package source; tests block
outbound Python connections and disable dotenv loading. This is a process-local
test guard, not an OS sandbox. Full suites, CUAD downloads and live generation are
separate commands with separate dependencies/costs. This index adds no fresh test,
benchmark or provider run; it links existing, dated evidence.

## One success trace and one failure boundary

Success path: parse an authored contract → choose source clauses with the real
TF-IDF/TextRank extractor → auditor finds their normalised text in the source →
produce structural DOCX/PDF outputs. Inspect the offline contract tests and L05
receipt. It establishes that bounded path, not generated-summary truth.

Consequential failure boundary: the candidate “Buyer may terminate” passes against
“Buyer may terminate only with written consent.” The source matches but the
condition is omitted. An irrelevant sentence copied from the source also passes.
An empty extraction list currently passes vacuously; an unsupported paragraph over
50 characters can pass the separate abstractive structure check. These behaviors
are exposed in [boundary tests](tests/test_auditor_boundaries.py), not hidden behind
the word “audited.”

## Corrected claims and remaining limits

L01 replaced the “physically cannot fabricate” implication with the actual matching
rules: specified character/whitespace normalization, then substring or contiguous
case-sensitive token equality. That is source matching, not entailment, authenticity
or tamper resistance. Summary paragraph/length checks are structure checks only.

- No semantic legal/summary faithfulness proof, complete-clause guarantee or legal advice.
- No fresh 100-contract reproduction, statistical superiority or production performance result from L05.
- No real SBERT weights/semantic quality or provider tokenization validation in the offline profile.
- No commercial adoption, client source-code disclosure, financial-services delivery or uptime evidence.
- No promise that every contract fits every provider/context window; configured chunking still needs workload-specific verification.
- No new cloud/provider spend for this evidence index. Benchmark/semantic-evaluation work remains separate and B01 is deferred.
