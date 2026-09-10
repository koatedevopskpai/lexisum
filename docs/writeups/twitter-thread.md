# X / Twitter thread

**Tweet 1/8**
> Most "AI contract summarizers" fail a simple test: compliance asks "is this the exact clause wording?" and the answer is no — the LLM paraphrased.
>
> I built LexiSum to fix that.
>
> Dual-engine: verbatim clauses + plain-English briefing.
>
> 🧵👇
>
> <DEMO_URL>

**Tweet 2/8**
> Engine 1 — Extractive (no LLM):
>
> Sentence-BERT + TextRank picks the most central clauses and returns them word-for-word.
>
> A token-level auditor then verifies each clause is an unmodified substring of the source.
>
> Zero hallucination by construction. ✅

**Tweet 3/8**
> Engine 2 — Abstractive:
>
> A separate LLM writes a 2-paragraph plain-English briefing (obligations, liabilities, termination), streamed token-by-token.
>
> Compliance gets exact text. Execs get readability. Nobody compromises.

**Tweet 4/8**
> The part most projects get wrong: long documents.
>
> LexiSum counts tokens and auto-switches between single-shot and sentence-aware overlapping chunks.
>
> A 60-page contract never silently loses its termination clause. 🧠

**Tweet 5/8**
> FinOps from day one:
>
> 💰 cost estimate shown BEFORE you run
> 📊 actual token usage logged with tags (environment, team)
> 🔍 estimates vs actuals reconcile, because both use the same pricing table
>
> Because "how much will this cost?" shouldn't be an afterthought.

**Tweet 6/8**
> Provider-agnostic via @LiteLLM:
>
> OpenAI · Azure · GCP Vertex · AWS Bedrock — a model-id change, not a rewrite.
>
> UI with @streamlit. Ships with Docker. 29 offline tests. 🐳

**Tweet 7/8**
> Reproducible science, not vibes:
>
> Benchmarked on CUAD (510 public contracts, 13k expert annotations).
> • Extractive → ROUGE + Oracle upper bound
> • Abstractive → BERTScore + LLM-as-judge rubric + cost
>
> One command: `python -m benchmark.reproduce_all`

**Tweet 8/8**
> Code + demo:
>
> 🔗 <REPO_URL>
> 🚀 <DEMO_URL>
>
> Not legal advice — but it shows how to put a trust/audit layer around LLMs in a regulated domain.
>
> Feedback welcome. RT if useful 🙏
