# LinkedIn

**Post:**

Most "AI summarises your contracts" tools have the same fatal flaw: the summary
is *prose*, and prose isn't admissible. When compliance asks "is this the exact
wording of the clause?", an LLM that paraphrased has already failed.

I built **LexiSum** to solve that with a dual-engine architecture:

🔒 **Extractive engine** — algorithmically selects the most critical clauses
and returns them *verbatim*. A token-level auditor verifies every clause is an
unmodified substring of the source. Zero hallucination by construction.

📝 **Abstractive engine** — a separate LLM writes a two-paragraph plain-English
briefing for executives, streamed live.

Three things I'm especially proud of:

1️⃣ **It never silently truncates.** A dynamic context strategy counts tokens
and switches between single-shot and sentence-aware chunking, so a 60-page
contract gets fully processed — the termination clause doesn't get dropped.

2️⃣ **FinOps is built in.** The UI shows a cost estimate before you run; actual
token usage is logged with tags (environment, team) so you can reconcile
estimated vs actual spend. This is the part most portfolio projects skip.

3️⃣ **It's reproducible.** Both engines are benchmarked on CUAD (510 public
contracts, 13k expert annotations) with ROUGE, BERTScore, and an LLM-as-judge
rubric. One command regenerates every number.

Stack: Python · LiteLLM (provider-agnostic: OpenAI/Azure/GCP/AWS) ·
Sentence-Transformers · spaCy · Streamlit · Docker · 29 offline tests.

Repo: <REPO_URL>
Live demo: <DEMO_URL>

It's not legal advice — but if you work in legal ops or build AI for regulated
industries, I'd love your take on whether verbatim auditing is the right trust
primitive.

#LegalTech #NLP #LLM #AI #FinOps #Python #OpenSource
