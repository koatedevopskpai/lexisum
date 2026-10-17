<div align="center">

# ⚖️ LexiSum

**Contract extraction with source-text matching and generated executive briefings.**
Verbatim extractive clauses + plain-language LLM briefings — audited, streamed, and costed.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-32%20passing-brightgreen.svg)](tests/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<!-- Replace with your recorded demo GIF -->
![LexiSum in action](docs/demo.gif)

</div>

---

## 🎯 Why LexiSum?

Legal teams face a fundamental tension:

- **Compliance** needs the *exact* legal wording of critical clauses — no paraphrasing, no hallucination.
- **Executives** need a *plain-language* summary of obligations, risks, and termination conditions.

Generative models can paraphrase or introduce unsupported claims. LexiSum separates clause extraction from generated prose and applies a source-text auditor to extraction. The auditor does not establish legal correctness or evidentiary admissibility.

> **Intended use: executive triage. Legal conclusions and generated summaries require review.**

---

## ✨ Features

- 🔒 **Source-matched extraction** — algorithmic selection checked with normalised substring/token matching; not a byte-exact or semantic guarantee.
- 📝 **Plain-Language Abstractive Summary** — 2-paragraph executive briefing for non-legal stakeholders.
- 🧠 **Smart Context Strategy** — `auto` / `single_shot` / `chunked_recursive` handles contracts of any size without truncation.
- ⚡ **Real-Time Streaming** — summarises render token-by-token in the UI.
- 💰 **FinOps Cost Tracking** — pre-flight estimates + post-run actuals, tagged and logged to `logs/usage.log`.
- ☁️ **Cloud-Agnostic** — OpenAI, Azure OpenAI, GCP Vertex, AWS Bedrock via [LiteLLM](https://github.com/BerriAI/litellm).
- 📄 **DOCX & PDF Export** — professional, in-memory briefings, no temp files.
- 🐳 **Docker Ready** — one command to run the full stack.
- 🧪 **Tested** — 29 unit tests covering the auditor, extractors, pipeline, cost tracker, and export engine.
- 📊 **Benchmarked** — reproducible evaluation on the public CUAD corpus.

---

## 🏗️ Architecture

```
Raw contract text
      │
      ▼
┌─────────────────────┐
│ Ingestion & Parser  │
└─────┬───────────┬───┘
      │           │
 [Extractive]  [Abstractive]
      ▼           ▼
┌───────────┐  ┌──────────────────────┐
│ Sentence- │  │ LLM (streaming,      │
│ BERT      │  │ chunked-recursive)   │
│ TextRank  │  │ GPT-4o / Claude /    │
│ ranker    │  │ Gemini               │
└─────┬─────┘  └──────────┬───────────┘
      ▼                   ▼
┌───────────┐  ┌──────────────────────┐
│ Top-N     │  │ 2 plain-language     │
│ verbatim  │  │ paragraphs           │
│ clauses   │  └──────────┬───────────┘
└─────┬─────┘             │
      └─────────┬─────────┘
                ▼
     ┌────────────────────────┐
     │ Verbatim & Format Audit│
     │ (token-level match)    │
     └────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design and **8 Architecture Decision Records** explaining *why* each choice was made.

---

## 🚀 Quickstart

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/lexisum.git
cd lexisum
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure environment

```bash
cp .env.example .env
# Add your API key(s) — OpenAI, Azure, GCP, or AWS
```

### 3. Run the UI

```bash
streamlit run app.py
```

Open <http://localhost:8501>.

### 4. Or run with Docker

```bash
docker compose up --build
```

### 5. Batch processing (CLI)

```bash
python main.py --input-dir ./contracts --output-dir ./summaries --concurrency 5
```

---

## 🧪 Tests

```bash
# Small no-network core check, no provider or model download
python -m pip install -r requirements-offline.lock
python -m pytest -c pytest-offline.ini

# Full existing suite (separate dependencies and integration assumptions)
# pytest tests/ -v
```

The offline-core profile covers extraction, source matching, basic export formats and usage accounting. It does not reproduce the benchmark or validate generated-summary faithfulness. See [L05 design and limits](docs/L05.md).

---

## 💰 Cost & Strategy Trade-offs

LexiSum lets you tune the cost/quality/latency trade-off per document.

| Strategy | LLM Calls | Best For | Notes |
|---|---|---|---|
| `single_shot` | 1 | Docs < ~70% of context window | Highest coherence, fastest |
| `chunked_recursive` | N + 1 | Very long contracts (100+ pages) | Cheap small models OK; parallel chunks |
| `auto` (default) | dynamic | General production | Picks based on token count |

All runs are logged to `logs/usage.log` with input/output token counts, model, strategy, and USD cost — **FinOps-ready**.

Example estimate (25-page contract, ~30k input tokens):

| Model | Estimated Cost |
|---|---|
| gpt-4o-mini | ~$0.005 |
| gemini/gemini-3.6-flash | ~$0.03 |
| claude-haiku-4-5 | ~$0.03 |
| gpt-4o | ~$0.08 |

---

## Auditor scope

See [AUDITOR_SEMANTICS.md](docs/AUDITOR_SEMANTICS.md) for the matching algorithm,
examples and interpretation. The legacy `is_verbatim` field means a pass under
that algorithm, not byte identity. The abstractive audit checks non-empty output
longer than 50 characters and counts paragraph blocks; it is not a faithfulness
judge. Draft write-ups and generated publication assets must be reconciled with
this scope before reuse; this correction does not verify their other claims.

## 📊 Benchmarks

LexiSum ships a reproducible benchmark suite on the **CUAD (Contract Understanding Atticus Dataset)** — 510 commercial legal contracts with 13,000+ expert annotations across 41 clause types.

### Extractive: TF-IDF vs Sentence-BERT

```bash
python -m benchmark.reproduce        # extractive only
python -m benchmark.reproduce_all    # full suite
```

**Corpus:** CUAD — 100 commercial legal contracts (sampled from 389 valid).
**Task:** rank sentences by the likelihood they contain an expert-annotated clause.
**Metrics:** MAP and nDCG@10 (ranking quality), precision/recall at top-N, ROUGE-L, latency, and verbatim pass rate.

| Method | MAP | nDCG@10 | Precision@3 | Recall@3 | ROUGE-L | Latency (s) | Verbatim |
|---|---|---|---|---|---|---|---|
| TF-IDF + TextRank | 0.727 | **0.855** | **0.883** | 0.050 | **0.1748** | **0.005** | 100% |
| Sentence-BERT + TextRank | **0.735** | 0.824 | 0.873 | 0.049 | 0.1482 | 1.501 | 100% |
| Oracle (Gold Sentences) | 1.000 | 1.000 | 1.000 | 0.059 | 0.1222 | 0.000 | 100% |

**Honest takeaway.** The general-purpose `all-MiniLM-L6-v2` embeddings did **not** meaningfully outperform the lexical TF-IDF baseline on CUAD clause selection (MAP 0.735 vs 0.727) and are ~300× slower. This is a useful negative result: legal clauses are highly formulaic, so lexical overlap is a strong signal, and a *general* sentence encoder adds little. The next experiment is a **legal-domain encoder** (e.g. Legal-BERT / Contract-BERT) or a query-relevance objective. Both engines had a **100% normalised source-text auditor pass rate in that evaluation**; this does not prove correct clause selection or faithful generated summaries. The Oracle is the ranking upper bound.

> The original design brief assumed SBERT would win by ~13%. Benchmarking disproved that assumption — which is exactly why the benchmark exists.

### Abstractive: multi-model comparison

Compares `gpt-4o-mini`, `claude-haiku-4-5`, and `gemini/gemini-3.6-flash` using **BERTScore** and a **5-dimension LLM-as-judge rubric** (obligations, risk/liability, termination, plain language, faithfulness) plus per-contract cost.

```bash
# Generate summaries (rate-limit-safe by default: batch_size=10, concurrency=4,
# LiteLLM retries with backoff, batch-delay between batches)
python -m benchmark.run_abstractive_benchmark --sample-size 100

# Evaluate with BERTScore + LLM-as-judge (gpt-4o)
python -m benchmark.evaluate_abstractive --judge-sample-size 15
```

Throttle knobs (all optional): `--batch-size`, `--max-concurrency`, `--max-retries`,
`--batch-retries`, `--request-timeout`, `--batch-delay`. See `docs/ARCHITECTURE.md` → ADR-009.

**Corpus:** CUAD — 100 contracts. **Judge:** `gpt-4o` on 15 samples per model, not 100 judged outputs per model. These are previously published results, not rerun for this correction. Raw JSON is described as living in `benchmark/results/` (git-ignored); the public snapshot does not independently reproduce those runs. Costs below are published USD per contract, not current quotes.

| Model | BERTScore F1 | Rubric Overall | Obligations | Risk/Liability | Termination | Plain Lang. | Faithful | Avg Cost |
|---|---|---|---|---|---|---|---|---|
| **gpt-4o-mini** | 0.768 | **3.21** | **3.20** | **3.00** | 2.80 | 4.13 | **2.93** | **$0.0017** |
| claude-haiku-4-5 | **0.776** | 2.95 | 2.67 | 2.60 | 2.67 | **4.20** | 2.60 | $0.0141 |
| gemini/gemini-3.6-flash | 0.702 | 1.63 | 1.60 | 1.20 | 1.20 | 2.53 | 1.60 | $0.0112 |

**Honest takeaway.**
- **BERTScore** (semantic overlap with expert-annotated clauses) is led by Claude Haiku 4.5 (0.776), with GPT-4o-mini a close second (0.768) and Gemini Flash trailing (0.702).
- **Rubric** (LLM-as-judge): GPT-4o-mini is the best *all-rounder* — strongest on obligation coverage and faithfulness — and it is **~8× cheaper per contract** than Claude Haiku 4.5. At 200 contracts/day the abstractive cost is ~$0.34 (gpt-4o-mini) vs ~$2.82 (claude-haiku-4-5).
- **Caveat:** rubric scores are modest overall (1.6–3.2) and the judge sample is small. Limited coverage and factual faithfulness are different questions: brevity does not excuse an unsupported claim. Source matching of extracted clauses does not validate generated prose.

---

## ☁️ Cloud Deployment

| Component | AWS | GCP | Azure |
|---|---|---|---|
| Ingestion | S3 + Textract | Cloud Storage + Document AI | Blob + Form Recognizer |
| Extractive | SageMaker JumpStart | Vertex AI Endpoint | Azure AI Language |
| Abstractive | Bedrock (Claude) | Vertex AI (Gemini) | Azure OpenAI (GPT-4o) |
| Batch | Step Functions + Lambda | Cloud Workflows + Cloud Run | Logic Apps + Functions |

Provider selection is a model-id + credential change via LiteLLM — no code changes.

---

## 📁 Project Structure

```
lexisum/
├── app.py                     # Streamlit UI
├── main.py                    # CLI batch processor
├── src/
│   ├── config.py              # Env-driven settings
│   ├── ingestion/             # Parsing + cloud OCR adapters
│   ├── extractive/            # TF-IDF + Sentence-BERT TextRank
│   ├── abstractive/           # LiteLLM generator (streaming/chunking)
│   ├── compliance/            # Token-level verbatim auditor
│   ├── export/                # In-memory DOCX/PDF
│   ├── cost/                  # Pricing + FinOps tracker
│   ├── pipeline.py            # Orchestration
│   └── batch_processor.py     # Async batch runner
├── benchmark/                 # CUAD extractive + abstractive benchmarks
├── tests/                     # 29 unit tests
└── docs/                      # Architecture + ADRs
```

---

## 🗺️ Roadmap

- [x] Dual-engine pipeline with verbatim audit
- [x] Streaming UI + FinOps cost tracking
- [x] Docker + tests
- [x] Reproducible CUAD benchmark suite
- [ ] Fine-tuned Legal-BERT extractive model (benchmark vs SBERT)
- [ ] Cloud storage ingestion (`--from-s3`, `--from-gcs`)
- [ ] Multi-tenant auth (roadmap only — not required for local use)

---

## 🤝 Contributing

PRs welcome. Open an issue first for major changes.

## 📜 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgements

Built on [LiteLLM](https://github.com/BerriAI/litellm), [Sentence-Transformers](https://www.sbert.net/), [Streamlit](https://streamlit.io/), and [spaCy](https://spacy.io/).
