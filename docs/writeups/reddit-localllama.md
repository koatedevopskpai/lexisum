# r/LocalLLaMA

**Title:**
> Built a legal contract summarizer that separates "verbatim clauses" from "LLM prose" — runs against local or hosted models via LiteLLM

**Body:**

Most "LLM summarises your contract" projects have the same flaw: the summary
is prose, and prose isn't admissible. Legal teams need the *exact* clause text
for compliance, and a *readable* summary for everyone else. Those are different
problems, so I stopped pretending one LLM call solves both.

**LexiSum** is a dual-engine pipeline:

- **Extractive** (local, no LLM): Sentence-BERT + TextRank picks the most
  central sentences and returns them verbatim. A token-level auditor proves
  each clause is an unmodified substring of the source.
- **Abstractive** (your choice of model): a 2-paragraph plain-English briefing,
  streamed.

Why this might interest this sub:

- **Runs on anything LiteLLM supports** — local llama.cpp/Ollama endpoints,
  OpenAI, Azure, Vertex, Bedrock. Point it at your own endpoint and the
  extractive engine still runs free/offline.
- **Context strategy that doesn't silently truncate.** `auto` counts tokens
  and switches between single-shot and sentence-aware overlapping chunks
  (summarised in parallel) based on the model's window. Small local models
  with 8k context can handle a 60-page contract without dropping the
  termination clause.
- **Cost-aware.** Pre-flight estimate shown before you run, actuals logged as
  tagged JSON-lines. Useful if you're metering your own GPU time too.

Benchmark on CUAD (public contract corpus) with ROUGE for the extractive side,
BERTScore + rubric for the abstractive side. One command reproduces it.

Repo: <REPO_URL>
Demo: <DEMO_URL>

Not legal advice. Curious whether folks would want a fully offline mode
(no cloud calls at all) as a first-class flag — would that be useful?

<REPO_URL>
