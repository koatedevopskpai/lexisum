# r/legaltech

**Title:**
> I built a contract summarizer where compliance can verify every clause is verbatim — and execs still get plain English

**Body:**

The blocker I kept running into when applying LLMs to contracts wasn't quality —
it was **admissibility**. If a summary paraphrases an indemnification clause,
it can't be relied on for review, and the whole thing gets rejected by legal ops.

So I built **LexiSum** around a simple split:

**1. Verbatim clause extraction (no LLM).**
The tool algorithmically selects the most central clauses and returns them
*word-for-word*. A token-level auditor then checks each one against the source
contract and flags anything that isn't an exact match. You get a green check
that says "these clauses are unmodified," not "the model probably copied them."

**2. Plain-language executive briefing (LLM).**
A separate engine writes a two-paragraph summary of obligations, liabilities,
and termination conditions — the thing a non-lawyer can actually read.

Other things that mattered for real use:

- **Long contracts don't break it.** A context strategy switches to
  sentence-aware chunking for long documents so the termination clause never
  gets silently truncated.
- **Cost transparency.** Every run shows a cost estimate up front and logs the
  actual token usage with tags (environment, team) so you can reconcile spend.
- **Export.** DOCX/PDF briefings ready to circulate.

It's not legal advice and it's not a replacement for counsel — it's a triage
and briefing tool that keeps the audit trail clean.

Repo: <REPO_URL>
Demo: <DEMO_URL>

I'd genuinely like feedback from people in legal ops: is a verbatim audit
check the right trust primitive, or would you rather see a clause-level diff
against a standard playbook?
