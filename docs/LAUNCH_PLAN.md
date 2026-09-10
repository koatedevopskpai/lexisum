# LexiSum — 4-Week Public Launch Plan

A serialized launch designed to "carry people along": each week reveals one
layer of the project, building an audience from *problem → architecture →
benchmarks → learnings* before asking for contributions. Every post links the
**live demo first**, the **repo second**.

---

## 1. Goal & success metrics

| Metric | Week-1 target | Week-4 target |
|---|---|---|
| GitHub stars | 25 | 150 |
| Forks | 3 | 15 |
| Live demo visits (Streamlit) | 300 | 1,500 |
| GitHub Discussions threads | 5 | 25 |
| Comments across all posts | 30 | 150 |
| Medium reads | 100 | 800 |

> Stars are a marketing outcome, not a code outcome. The README + live demo
> drive ~90% of them. The write-ups drive the *traffic* to the README.

---

## 2. Pre-launch — Week 0 (before any post)

Nothing below can be skipped. A repo with a broken GIF or dead demo link kills
first impressions.

- [ ] Record and commit `docs/demo.gif` (see `docs/DEMO.md` — 8–12s, <5 MB).
- [ ] Deploy to Streamlit Community Cloud; confirm the URL is stable.
- [ ] Update `<DEMO_URL>` in README badge + all write-ups.
- [ ] Push to GitHub; update `<REPO_URL>` everywhere.
- [ ] Set topics (from `docs/DEMO.md`).
- [ ] Tag `v0.1.0` and write release notes (see §6).
- [ ] Enable GitHub Discussions and add two pinned threads (below).
- [ ] Create the 4 Medium article drafts in your editor (fill from
      `docs/writeups/medium-part*.md`).
- [ ] Sanity: `pytest tests/` passes, README screenshots render, `--help`
      works, benchmark commands run.

**Pinned Discussion threads:**
1. **"Roadmap — what should LexiSum build next?"** (surfaces the roadmap table).
2. **"The benchmark that disproved my assumption (SBERT vs TF-IDF)"** —
   a deliberately provocative title that invites debate.

---

## 3. The 4-week arc

| Week | Theme | Star driver | Channels |
|---|---|---|---|
| 1 | **The problem** — prose isn't admissible | Live demo + GIF "wow" | Show HN, r/MachineLearning, r/LocalLLaMA, LinkedIn, X, Medium P1 |
| 2 | **The architecture** — dual-engine + ADRs | Technical depth, forks | Medium P2, r/MachineLearning deep-dive, LinkedIn, X |
| 3 | **The benchmarks** — real numbers | Credibility, citations | Medium P3, r/MachineLearning [P], r/LocalLLaMA, LinkedIn, X |
| 4 | **The learnings & the ask** — open source | Community, contributors | Medium P4, r/legaltech, Show HN follow-up, LinkedIn, X |

---

## 4. Week-by-week plan

### Week 1 — "The problem" (launch)

**Hook:** *LLM summaries aren't admissible for legal review. LexiSum splits
extractive (verbatim) from abstractive (plain-English) so compliance can
actually verify every clause.*

| Day | Channel | Asset | CTA |
|---|---|---|---|
| Tue 08:00 ET | **Show HN** | `docs/writeups/show-hn.md` | Try the demo |
| Tue 12:00 ET | **LinkedIn** | `docs/writeups/linkedin.md` | Repo + demo |
| Wed 09:00 ET | **X thread** | `docs/writeups/twitter-thread.md` | RT / demo |
| Wed 12:00 ET | **r/MachineLearning** | `docs/writeups/reddit-machinelearning.md` (intro angle) | Feedback |
| Thu 09:00 ET | **Medium P1** | `docs/writeups/medium-part1-problem.md` | Follow the series |
| Thu 12:00 ET | **r/LocalLLaMA** | `docs/writeups/reddit-localllama.md` | Local-model angle |
| Fri 12:00 ET | **r/legaltech** | `docs/writeups/reddit-legaltech.md` | Compliance angle |

**Engagement:** reply to every comment within 60 minutes. Update the README
star/badge counts at day-end. Link Medium P1 at the bottom of every other post.

### Week 2 — "The architecture"

**Hook:** *The 8 decisions I'd defend in a code review — dual-engine, token-level
audit, dynamic context strategy, FinOps, in-memory export, async batch,
provider-agnostic, Streamlit. With ADRs.*

| Day | Channel | Asset | CTA |
|---|---|---|---|
| Tue 09:00 ET | **Medium P2** | `docs/writeups/medium-part2-architecture.md` | Read the ADRs |
| Wed 12:00 ET | **r/MachineLearning deep-dive** | architecture angle of `reddit-machinelearning.md` | Review the ADRs |
| Thu 09:00 ET | **LinkedIn** | architecture teaser | Repo |
| Thu 12:00 ET | **X thread** | architecture highlights | Repo |

**Engagement:** ask one concrete question in each post ("would a
legal-domain encoder change the outcome?"). Pin the best answer to the
"benchmark" Discussion.

### Week 3 — "The benchmarks"

**Hook:** *Real numbers, honestly reported — including the result that
disproved my own assumption. 100 CUAD contracts, 3 providers.*

| Day | Channel | Asset | CTA |
|---|---|---|---|
| Tue 09:00 ET | **Medium P3** | `docs/writeups/medium-part3-benchmarks.md` | Reproduce it |
| Wed 09:00 ET | **r/MachineLearning [P]** | results + `benchmark.reproduce_all` | Verify the numbers |
| Wed 12:00 ET | **r/LocalLLaMA** | cost table ($/1M, 200/day) | Cost analysis |
| Thu 09:00 ET | **LinkedIn** | benchmark summary | Repo |
| Fri 09:00 ET | **X thread** | top-line numbers | Repo |

**Engagement:** publish the raw JSON + tables. Invite people to run
`python -m benchmark.reproduce_all` and post their own numbers.

### Week 4 — "The learnings & the ask"

**Hook:** *What a rate-limit wall, a merge bug, and a failed hypothesis taught
me about shipping LLM tooling. Plus: what should LexiSum build next?*

| Day | Channel | Asset | CTA |
|---|---|---|---|
| Tue 09:00 ET | **Medium P4** | `docs/writeups/medium-part4-learnings.md` | Contribute |
| Wed 09:00 ET | **r/legaltech** | production/trust angle | Try the demo |
| Wed 12:00 ET | **Show HN follow-up** | "I shipped v0.2, here's what I learned" | Contributors |
| Thu 09:00 ET | **LinkedIn** | retrospective | Roadmap vote |
| Thu 12:00 ET | **X thread** | recap + contributor ask | GitHub Discussions |

**Engagement:** turn the roadmap Discussion into a poll. Thank every
contributor publicly. Announce a `good first issue` batch labelled
`hacktoberfest-friendly`.

---

## 5. Channel quick-reference

| Channel | Best day/time (US ET) | Format | Link rule |
|---|---|---|---|
| Show HN | Tue–Thu 08:00 | Text, no image | Demo URL |
| r/MachineLearning | Tue–Thu 09:00–12:00 | `[P]` tag, self-post | Repo |
| r/LocalLLaMA | Tue–Thu 12:00 | Text | Repo |
| r/legaltech | Tue–Thu 12:00 | Text, compliance-first | Demo URL |
| LinkedIn | Tue–Thu 09:00 | Post + GIF | Repo + demo |
| X / Twitter | Tue–Thu 09:00 | Thread + GIF | Demo URL |
| Medium | Tue–Thu 09:00 | Long-form, 4-part series | Repo |
| Dev.to | Any | Mirror of Medium | Repo |

---

## 6. GitHub trending mechanics (the actual star drivers)

1. **README is the product page.** It already has: hero GIF, live-demo badge,
   one-line pitch, architecture diagram, honest benchmark tables, and a
   "Why not just use ChatGPT?" differentiator. Keep the badge counts fresh.
2. **Release `v0.1.0` on Week 1** and `v0.2.0` on Week 4.** Release notes that
   read like a changelog + "what's next" pull in watchers and surface in the
   GitHub newsfeed.
3. **Topics** — `legaltech nlp llm compliance contract-analysis streamlit
   extractive-summarization abstractive-summarization finops litellm
   sentence-transformers` (see `docs/DEMO.md`).
4. **GitHub Discussions** — the pinned roadmap thread converts readers into
   engaged users (the algorithm + your audience both reward it).
5. **README badges** for tests/build/twitter count as social proof.
6. **Commit cadence during launch** — a few small public commits each week
   keep the repo "alive" in feeds; add `good first issue` labels.

---

## 7. Engagement playbook (first 60 minutes decide reach)

- Reply to **every** early comment; the first hour sets the velocity.
- Never link the repo alone — always lead with the **live demo**.
- Cross-link: every post ends with "Part 2 next Tuesday — follow me".
- Tag the tools you built on: **LiteLLM, Streamlit, Sentence-Transformers,
  spaCy** (mention in the post, not spam).
- Share the GIF inline where the platform allows (X, LinkedIn, Reddit).
- Save screenshots/numbers for the retrospective (Week 4 needs receipts).

---

## 8. Weekly checkpoint

End of each week, update the README + a private note:

| Check | Week 1 | Week 2 | Week 3 | Week 4 |
|---|---|---|---|---|
| Stars vs target | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Demo visits | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Discussions active | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| Comments replied < 60 min | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |

If a number is behind, double down on the **live demo** link and reply more
aggressively — those are the two highest-leverage levers.

---

## 9. Content inventory → week map

| Existing asset | Week |
|---|---|
| `docs/writeups/show-hn.md` | 1 (+ Week 4 follow-up) |
| `docs/writeups/reddit-machinelearning.md` | 1 (intro) / 2 (deep-dive) / 3 (benchmarks) |
| `docs/writeups/reddit-localllama.md` | 1 |
| `docs/writeups/reddit-legaltech.md` | 1 / 4 |
| `docs/writeups/linkedin.md` | 1 |
| `docs/writeups/twitter-thread.md` | 1 |
| `docs/writeups/medium-part1-problem.md` | 1 |
| `docs/writeups/medium-part2-architecture.md` | 2 |
| `docs/writeups/medium-part3-benchmarks.md` | 3 |
| `docs/writeups/medium-part4-learnings.md` | 4 |
| `docs/DEMO.md` (GIF + deploy) | Week 0 |
| `docs/ARCHITECTURE.md` (ADRs) | 2 (deep-dive) |
| `benchmark/results/*` (real numbers) | 3 |