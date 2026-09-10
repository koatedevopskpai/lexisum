<div align="center">

# ⚖️ LexiSum

**Compliance-safe verbatim clause extraction + plain-language executive briefings — in one pipeline.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-29%20passing-brightgreen.svg)](tests/)
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

Wrapping an LLM in a prompt is not enough: generative models paraphrase, hallucinate, and are not admissible for evidentiary review. LexiSum solves this with a **dual-engine architecture** and a **token-level verbatim auditor**.

> **Zero hallucination on extractive tasks. Human-grade plain language on abstractive tasks.**

---

## ✨ Features

- 🔒 **100% Verbatim Extractive Summary** — algorithmically selected, audited, guaranteed unmodified.
- 📝 **Plain-Language Abstractive Summary** — 2-paragraph executive briefing for non-legal stakeholders.
- 🧠 **Smart Context Strategy** — `auto` / `single_shot` / `chunked_recursive` handles contracts of any size without truncation.
- ⚡ **Real-Time Streaming** — summaries render token-by-token in the UI.
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
pytest tests/ -v
```

Covers: token-level verbatim auditing, extractive ranking, chunking strategy, pipeline integration, FinOps cost logging, and DOCX/PDF export.

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
| claude-3-5-haiku | ~$0.008 |
| gpt-4o | ~$0.16 |
| claude-3-5-sonnet | ~$0.10 |

---

## 📊 Benchmarks

LexiSum ships a reproducible benchmark suite on the **CUAD (Contract Understanding Atticus Dataset)** — 510 commercial legal contracts with 13,000+ expert annotations across 41 clause types.

### Extractive: TF-IDF vs Sentence-BERT

```bash
python -m benchmark.reproduce        # extractive only
python -m benchmark.reproduce_all    # full suite
```

Metrics: ROUGE-1/2/L F1, latency, and verbatim compliance. Results are auto-written to `benchmark/results/BENCHMARK.md`.

<!-- Paste generated table here after running the benchmark -->

### Abstractive: multi-model comparison

Compares `gpt-4o-mini`, `claude-3-5-haiku`, and `gemini-1.5-flash` using **BERTScore** and a **5-dimension LLM-as-judge rubric** (obligations, risk/liability, termination, plain language, faithfulness) plus per-contract cost.

<!-- Paste generated table here after running the benchmark -->

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