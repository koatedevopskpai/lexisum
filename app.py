"""
LexiSum Streamlit UI.

The primary user-facing entrypoint. Supports:
  - single or multiple document upload (PDF / TXT / DOCX)
  - model selection (any LiteLLM model id)
  - extractive sentence count
  - context-strategy selection (auto / single_shot / chunked_recursive)
  - pre-flight cost estimates
  - live streaming of the abstractive summary
  - actual-cost reporting (FinOps)
  - DOCX / PDF export
"""

from __future__ import annotations

import os
from typing import Dict

import streamlit as st

from src.config import settings
from src.cost.cost_tracker import CostTracker
from src.cost.pricing import PRICING_PER_MILLION, compute_cost
from src.export.document_generator import DocumentExportEngine
from src.ingestion.local_files import load_pdf, load_text_file
from src.pipeline import LegalSummarizationPipeline

MODELS = sorted(PRICING_PER_MILLION.keys())

st.set_page_config(
    page_title="LexiSum | Compliance-Safe Legal Summarizer",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .hero-title { font-size: 2.4rem; font-weight: 800; color: #0f172a; margin-bottom: .2rem; }
    .hero-sub   { font-size: 1.05rem; color: #64748b; margin-bottom: 1.5rem; }
    .badge-ok   { background:#dcfce7; color:#166534; padding:4px 10px; border-radius:6px; font-weight:600; font-size:.85rem; }
    .badge-bad  { background:#fee2e2; color:#991b1b; padding:4px 10px; border-radius:6px; font-weight:600; font-size:.85rem; }
    .cost-box   { background:#f1f5f9; border-left:4px solid #3b82f6; padding:12px 16px; border-radius:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-title">⚖️ LexiSum</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Dual-engine contract intelligence: compliance-safe verbatim clauses + plain-language executive briefings.</div>',
    unsafe_allow_html=True,
)

# ---------------- Sidebar configuration ----------------
with st.sidebar:
    st.header("⚙️ Configuration")

    model_choice = st.selectbox("Abstractive Model", MODELS, index=MODELS.index(settings.abstractive_model) if settings.abstractive_model in MODELS else 0)
    strategy = st.radio(
        "Context Strategy",
        ["auto", "single_shot", "chunked_recursive"],
        index=0,
        help="Auto picks single-shot when the doc fits, else chunked-recursive.",
    )
    num_sentences = st.slider("Extractive Sentences", 1, 5, settings.extractive_top_n)
    output_filename = st.text_input("Report Filename", value="Contract_Executive_Briefing")

    # Optional BYO-key (used on Streamlit Cloud where secrets aren't available)
    api_key = st.text_input("API Key (session only)", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.markdown("---")
    ctx = PRICING_PER_MILLION.get(model_choice, {}).get("context", "unknown")
    st.caption(f"Context window: {ctx:,} tokens" if isinstance(ctx, int) else "Context window: unknown")
    st.caption("Estimates use public pricing. Actuals are logged to `logs/usage.log`.")


# ---------------- Upload ----------------
uploaded_files = st.file_uploader(
    "Upload Legal Agreements (PDF, TXT, DOCX)",
    type=["pdf", "txt", "docx"],
    accept_multiple_files=True,
)


def _extract_text_from_upload(file) -> str:
    if file.name.lower().endswith(".pdf"):
        return load_pdf(file)
    if file.name.lower().endswith(".docx"):
        from src.ingestion.local_files import load_docx
        return load_docx(file)
    return load_text_file(file)


# ---------------- Processing ----------------
if uploaded_files:
    docs: Dict[str, str] = {}
    with st.spinner("Extracting text from uploaded files..."):
        for f in uploaded_files:
            try:
                docs[f.name] = _extract_text_from_upload(f)
            except Exception as e:  # pragma: no cover - UI error handling
                st.error(f"Failed to read {f.name}: {e}")

    if docs:
        # Pre-flight cost estimate
        st.markdown("### 💰 Pre-Flight Cost Estimate")
        total_est = 0.0
        for name, text in docs.items():
            est = CostTracker.estimate_cost(model_choice, text, output_estimate_tokens=600)
            total_est += est["total_estimate_usd"]
            st.markdown(
                f'<div class="cost-box"><b>{name}</b> — '
                f'{est["input_tokens"]:,} input tokens · '
                f'~${est["total_estimate_usd"]:.4f} estimated</div>',
                unsafe_allow_html=True,
            )
        st.markdown(f"**Total estimated cost: ${total_est:.4f}**")

        if st.button("🚀 Process Contracts", type="primary"):
            for name, raw_text in docs.items():
                st.markdown(f"---\n### 📄 {name}")

                pipeline = LegalSummarizationPipeline(
                    model_name=model_choice,
                    extractive_top_n=num_sentences,
                    strategy=strategy,
                )

                ext_container = st.container()
                abs_container = st.container()
                status = st.status("Running dual-engine pipeline...", expanded=True)

                final_result = None
                usage = None

                try:
                    for event in pipeline.stream_summaries(raw_text, doc_id=name):
                        if event["stage"] == "extractive":
                            with ext_container:
                                st.markdown("#### 📌 Verbatim Extractive Clauses")
                                for i, s in enumerate(event["sentences"], 1):
                                    st.info(f"**Clause {i}:** {s}")
                                if event["audit"]["passed"]:
                                    st.markdown('<span class="badge-ok">✓ Verbatim Audit Passed</span>', unsafe_allow_html=True)
                                else:
                                    st.markdown('<span class="badge-bad">✗ Verbatim Audit Failed</span>', unsafe_allow_html=True)
                            status.update(label="Extractive complete. Streaming abstractive...")

                        elif event["stage"] == "abstractive":
                            if "abs_placeholder" not in st.session_state:
                                with abs_container:
                                    st.markdown("#### 📝 Executive Plain-Language Summary")
                                    st.session_state["abs_placeholder"] = st.empty()
                            st.session_state["abs_buffer"] = st.session_state.get("abs_buffer", "") + event["delta"]
                            st.session_state["abs_placeholder"].markdown(st.session_state["abs_buffer"] + "▌")

                        elif event["stage"] == "complete":
                            final_result = event["result"]
                            usage = event["usage"]
                            st.session_state["abs_placeholder"].markdown(final_result["abstractive_summary"]["text"])
                            status.update(label="✅ Complete", state="complete", expanded=False)

                except Exception as e:  # pragma: no cover - UI error handling
                    status.update(label=f"❌ Error: {e}", state="error")
                    continue

                # Usage summary (FinOps actuals)
                if usage:
                    actual_cost = compute_cost(
                        model_choice, usage["input_tokens"], usage["output_tokens"]
                    )
                    st.caption(
                        f"Strategy: `{usage['strategy']}` · LLM calls: {usage['calls']} · "
                        f"{usage['input_tokens']:,} in / {usage['output_tokens']:,} out tokens · "
                        f"**actual cost: ${actual_cost:.4f}**"
                    )

                # Exports
                if final_result:
                    st.markdown("##### 📥 Export")
                    c1, c2 = st.columns(2)
                    with c1:
                        docx_buf = DocumentExportEngine.create_docx(final_result, doc_title=output_filename)
                        st.download_button(
                            "⬇️ Download DOCX",
                            data=docx_buf,
                            file_name=f"{name.rsplit('.', 1)[0]}_{output_filename}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"docx_{name}",
                        )
                    with c2:
                        pdf_buf = DocumentExportEngine.create_pdf(final_result, doc_title=output_filename)
                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_buf,
                            file_name=f"{name.rsplit('.', 1)[0]}_{output_filename}.pdf",
                            mime="application/pdf",
                            key=f"pdf_{name}",
                        )

                # Reset per-doc streaming state
                st.session_state.pop("abs_placeholder", None)
                st.session_state.pop("abs_buffer", None)