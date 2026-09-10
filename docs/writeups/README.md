# Write-ups & launch copy

The 4-week launch sequence lives in **`../LAUNCH_PLAN.md`** — read it first.
This folder holds ready-to-post drafts; each one maps to a week and channel
in that plan.

## Medium 4-part series (the backbone of the launch)

| Part | File | Week | Theme |
|---|---|---|---|
| 1 | [`medium-part1-problem.md`](medium-part1-problem.md) | 1 | Prose isn't admissible — why two engines |
| 2 | [`medium-part2-architecture.md`](medium-part2-architecture.md) | 2 | 8 decisions / ADRs |
| 3 | [`medium-part3-benchmarks.md`](medium-part3-benchmarks.md) | 3 | Real benchmark numbers |
| 4 | [`medium-part4-learnings.md`](medium-part4-learnings.md) | 4 | Failures, costs, and the contribution ask |

## Channel posts

| Channel | File | Week | Notes |
|---|---|---|---|
| Hacker News | [`show-hn.md`](show-hn.md) | 1 | Post Tue–Thu ~8–10am US Eastern |
| r/LocalLLaMA | [`reddit-localllama.md`](reddit-localllama.md) | 1 / 3 | Emphasise local models + cost |
| r/MachineLearning | [`reddit-machinelearning.md`](reddit-machinelearning.md) | 1 / 2 / 3 | Use `[P]` tag; lead with the benchmark |
| r/legaltech | [`reddit-legaltech.md`](reddit-legaltech.md) | 1 / 4 | Lead with the compliance/audit angle |
| LinkedIn | [`linkedin.md`](linkedin.md) | 1 | Attach the GIF; tag LiteLLM/Streamlit |
| X / Twitter | [`twitter-thread.md`](twitter-thread.md) | 1 | Thread + GIF |
| Dev.to / Medium | [`devto-medium.md`](devto-medium.md) | mirror | Long-form engineering story |

## Before posting

1. Record `docs/demo.gif` and deploy the live demo (`docs/DEMO.md`).
2. Replace `<REPO_URL>` and `<DEMO_URL>` everywhere.
3. Confirm benchmark numbers against `benchmark/results/` (they're real).

## Universal posting rules

1. **Lead with the problem, not the tech.** "LLM summaries aren't admissible
   for legal review" beats "I used Sentence-BERT."
2. **Always link the live demo first**, repo second.
3. **Show the GIF inline** where the platform allows it.
4. **Be honest about limitations** (pricing snapshots, benchmark sample size,
   not legal advice). Credibility drives engagement.
5. **Reply to every early comment** — the first 60 minutes determine reach.