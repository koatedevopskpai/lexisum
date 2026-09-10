# Recording the demo & deploying

These are the two highest-leverage tasks for repository visibility. A live
demo link and an inline GIF in the README drive more stars than any backend
code.

## 1. Record `docs/demo.gif` (5 minutes)

1. Run the app:

   ```bash
   streamlit run app.py
   ```

2. Load `examples/sample_contract.txt`.
3. Set the model to `gpt-4o-mini` and click **Process Contracts**.
4. Record the full screen with [ScreenToGif](https://www.screentogif.com/)
   (Windows) or [LICEcap](https://www.cockos.com/licecap/) (macOS).
5. Trim to **8–12 seconds**. Export at 720p, under **5 MB**.
6. Save as `docs/demo.gif` and commit it.

The README already references `docs/demo.gif`, so it will appear at the top
of the repository once committed.

## 2. Deploy to Streamlit Community Cloud (5 minutes)

1. Push the repository to GitHub (public).
2. Go to <https://share.streamlit.io> → **New app** → select the repo →
   main file `app.py`.
3. Deploy. Copy the resulting URL.
4. Replace `<DEMO_URL>` everywhere (README badge + `docs/writeups/*`).

> **Secrets:** Streamlit Community Cloud does not protect secrets for public
> apps. The UI already supports a per-session API key field
> (`API Key (session only)` in the sidebar) so users bring their own key.
> Do **not** bake keys into the app or commit `.env`.

## 3. Add the badges

The README already contains badge markup. After deploying, add the live-app
badge near the top:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](<DEMO_URL>)
```

## 4. Set repository topics

On GitHub, set topics so the repo is discoverable:

```
legaltech, nlp, llm, compliance, contract-analysis, streamlit,
extractive-summarization, abstractive-summarization, finops, litellm,
sentence-transformers
```

## 5. Publish the write-ups

Use the drafts in `docs/writeups/`. Post the live demo link first, the repo
second, and reply to early comments.
