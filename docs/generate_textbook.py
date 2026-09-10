"""
Generate the LexiSum textbook as a DOCX.

Run:  python docs/generate_textbook.py
Output: docs/LexiSum_Textbook.docx

The document is written like a technical reference book. Demo GIFs are
inserted as bordered placeholders (Figure N) with a matching entry in
Appendix B (Demo GIF Production List) so you can record them and drop them
into Word in sequence.
"""

from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor

OUTPUT = "docs/LexiSum_Textbook.docx"

# ---------------------------------------------------------------------------
# Demo GIF registry (Figure numbers are ordered by appearance in the book)
# ---------------------------------------------------------------------------
GIFS = [
    {
        "fig": 1,
        "path": "docs/demo.gif",
        "chapter": 1,
        "caption": "The hero demo: upload a contract, click Process, and watch "
        "the dual-engine pipeline produce verbatim clauses and a streamed "
        "plain-language summary.",
    },
    {
        "fig": 2,
        "path": "docs/gifs/02_pipeline_flow.gif",
        "chapter": 3,
        "caption": "The full pipeline: ingestion, extractive ranking, verbatim "
        "audit, abstractive generation, and FinOps logging.",
    },
    {
        "fig": 3,
        "path": "docs/gifs/03_extractive_clauses.gif",
        "chapter": 5,
        "caption": "The extractive engine selecting the top-N clauses with the "
        "verbatim audit badge.",
    },
    {
        "fig": 4,
        "path": "docs/gifs/04_streaming_summary.gif",
        "chapter": 6,
        "caption": "The abstractive summary streaming token-by-token in the UI.",
    },
    {
        "fig": 5,
        "path": "docs/gifs/05_context_strategy.gif",
        "chapter": 6,
        "caption": "Selecting the context strategy (auto / single-shot / "
        "chunked-recursive) for a long contract.",
    },
    {
        "fig": 6,
        "path": "docs/gifs/06_audit_verification.gif",
        "chapter": 7,
        "caption": "The compliance auditor verifying every clause is verbatim, "
        "with a pass/fail badge.",
    },
    {
        "fig": 7,
        "path": "docs/gifs/07_cost_estimate_actual.gif",
        "chapter": 8,
        "caption": "The pre-flight cost estimate shown before processing and the "
        "actual logged cost afterwards.",
    },
    {
        "fig": 8,
        "path": "docs/gifs/08_ui_multi_upload.gif",
        "chapter": 9,
        "caption": "The Streamlit UI processing multiple contracts with progress "
        "and export buttons.",
    },
    {
        "fig": 9,
        "path": "docs/gifs/09_cli_batch.gif",
        "chapter": 9,
        "caption": "The CLI batch processor summarising a directory of contracts "
        "with progress logging.",
    },
    {
        "fig": 10,
        "path": "docs/gifs/10_benchmark_reproduce.gif",
        "chapter": 11,
        "caption": "Running `python -m benchmark.reproduce_all` and generating "
        "the results tables.",
    },
    {
        "fig": 11,
        "path": "docs/gifs/11_docker_deploy.gif",
        "chapter": 12,
        "caption": "Building and launching the full stack with `docker compose up`.",
    },
]

GIF_BY_FIG = {g["fig"]: g for g in GIFS}

# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

ACCENT = "1D4ED8"
CODE_BG = "F1F5F9"
BOX_BG = "EFF6FF"


def shade_paragraph(paragraph, fill=CODE_BG):
    pPr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def border_paragraph(paragraph, color=ACCENT, sz="10"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "6")
        el.set(qn("w:color"), color)
        pBdr.append(el)
    pPr.append(pBdr)


def add_body(doc, text, justify=True):
    p = doc.add_paragraph(text)
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def add_bullets(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def add_code(doc, code):
    p = doc.add_paragraph()
    shade_paragraph(p)
    run = p.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    return p


def add_figure(doc, fig_no, caption=None):
    gif = GIF_BY_FIG[fig_no]
    cap = caption or gif["caption"]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    border_paragraph(p)
    shade_paragraph(p, fill=BOX_BG)
    run = p.add_run(f"[ FIGURE {fig_no} — INSERT GIF HERE ]\n{gif['path']}")
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
    cap_p = doc.add_paragraph()
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap_p.add_run(f"Figure {fig_no}. {cap}")
    cap_run.italic = True
    cap_run.font.size = Pt(9)
    return cap_p


def add_table(doc, headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers), style="Table Grid")
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.size = Pt(10)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = t.rows[i].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
    if col_widths:
        for row in t.rows:
            for idx, w in enumerate(col_widths):
                if idx < len(row.cells):
                    row.cells[idx].width = Inches(w)
    doc.add_paragraph()
    return t


def chapter(doc, number, title):
    doc.add_page_break()
    h = doc.add_heading(f"Chapter {number}", level=1)
    h2 = doc.add_heading(title, level=1)
    return h2


def section(doc, title):
    return doc.add_heading(title, level=2)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

def build():
    doc = Document()

    # Base fonts
    normal = doc.styles["Normal"]
    normal.font.name = "Cambria"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)

    # ---------------- Title page ----------------
    for _ in range(4):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("LEXISUM")
    r.font.size = Pt(40)
    r.bold = True
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    st = doc.add_paragraph()
    st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = st.add_run("A Compliance-Safe Dual-Engine System for Legal Contract Summarization")
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("A Technical Reference, from Problem to Production")
    r.font.size = Pt(12)
    r.italic = True

    for _ in range(3):
        doc.add_paragraph()

    meta = [
        "Version 0.1.0",
        "September 2026",
        "Repository: <REPO_URL>",
        "Live demo: <DEMO_URL>",
    ]
    for line in meta:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(line).font.size = Pt(11)

    doc.add_page_break()

    # ---------------- Contents ----------------
    doc.add_heading("Contents", level=1)
    contents = [
        "Preface",
        "Chapter 1 — The Problem: Prose Is Not Admissible",
        "Chapter 2 — Fundamentals of Text Summarization",
        "Chapter 3 — System Overview and Architecture",
        "Chapter 4 — Ingestion and Text Parsing",
        "Chapter 5 — The Extractive Engine",
        "Chapter 6 — The Abstractive Engine",
        "Chapter 7 — The Compliance Auditor",
        "Chapter 8 — FinOps: Estimating and Tracking Cost",
        "Chapter 9 — Orchestration: Pipeline, Batch, CLI, and UI",
        "Chapter 10 — The Export Engine",
        "Chapter 11 — Benchmarking and Results",
        "Chapter 12 — Deployment and Operations",
        "Chapter 13 — Cost Analysis",
        "Chapter 14 — Lessons Learned and Failure Modes",
        "Chapter 15 — Roadmap and Future Work",
        "Appendix A — Quick Reference",
        "Appendix B — Demo GIF Production List",
        "Appendix C — Architecture Decision Records (Summary)",
        "Appendix D — Glossary",
    ]
    for item in contents:
        doc.add_paragraph(item, style="List Number")

    doc.add_page_break()

    # ---------------- Preface ----------------
    doc.add_heading("Preface", level=1)
    add_body(
        doc,
        "This book is a complete technical reference for LexiSum, a dual-engine "
        "system for summarizing legal contracts with a hard compliance guarantee. "
        "LexiSum was designed to answer one question that most LLM-based legal "
        "tools avoid: can we summarize a contract for busy executives without "
        "ever fabricating a clause? The answer is a system with two independent "
        "engines, a token-level audit trail, and cost accounting that never "
        "relies on hope.",
    )
    add_body(
        doc,
        "The book is organized to take the reader from first principles to a "
        "deployed system. Chapters 1 and 2 establish the problem and the "
        "background. Chapters 3 through 10 dissect each component of the "
        "architecture. Chapters 11 through 13 present measured results and "
        "costs. Chapters 14 and 15 close with lessons learned and a roadmap. "
        "Appendices provide a quick reference, the production list for the demo "
        "GIFs you will record, a summary of the Architecture Decision Records, "
        "and a glossary.",
    )
    add_body(
        doc,
        "Throughout the book, bracketed placeholders mark the position of demo "
        "GIFs. Appendix B lists all eleven GIFs in the exact order in which they "
        "appear, so you can record them and insert them into the document in "
        "sequence. Before publishing, replace the repository and demo URL "
        "placeholders with your real links.",
    )

    # ---------------- Chapter 1 ----------------
    chapter(doc, 1, "The Problem: Prose Is Not Admissible")
    section(doc, "1.1 The Familiar Demo")
    add_body(
        doc,
        "Every legal-technology demo follows the same script. Someone uploads a "
        "twenty-five-page contract, an LLM produces an elegant summary, and the "
        "room nods in agreement. Then compliance asks the question that ends "
        "the demonstration: is this the exact wording of the indemnification "
        "clause? The answer is no. The model paraphrased, and paraphrased legal "
        "text cannot be relied upon for evidentiary review. The tool is shelved.",
    )
    section(doc, "1.2 The Tension Inside a Legal Team")
    add_body(
        doc,
        "A legal team needs two different products from the same document. "
        "Compliance needs the exact wording of critical clauses, word for word, "
        "with nothing invented. Executives need a plain-language briefing that "
        "describes obligations, liabilities, and termination terms in language "
        "a non-lawyer can read. These are incompatible requirements. You cannot "
        "guarantee verbatim fidelity and produce fluent prose in a single "
        "output, because fluency is precisely what compliance cannot trust.",
    )
    section(doc, "1.3 The Thesis")
    add_body(
        doc,
        "LexiSum's thesis is simple: stop asking one model to do both jobs. "
        "Separate the task into an extractive engine that selects and returns "
        "sentences verbatim, and an abstractive engine that writes the readable "
        "briefing. Place a token-level auditor between the two so every claim "
        "can be verified against the source. This is the pattern for any "
        "regulated domain, not just law: whenever an LLM's output must be "
        "verifiable, split the exact step from the fluent step and audit the "
        "seam between them.",
    )
    add_figure(doc, 1)

    # ---------------- Chapter 2 ----------------
    chapter(doc, 2, "Fundamentals of Text Summarization")
    section(doc, "2.1 Two Families of Summarization")
    add_body(
        doc,
        "Text summarization has two families. Extractive summarization selects "
        "existing sentences from the source and returns them unchanged; it can "
        "never invent content, but it cannot rephrase either. Abstractive "
        "summarization generates new sentences, which reads more naturally but "
        "introduces the risk of paraphrase and hallucination. LexiSum uses both, "
        "each for the job it can do reliably.",
    )
    add_table(
        doc,
        ["Property", "Extractive", "Abstractive"],
        [
            ["Output", "Existing sentences, verbatim", "Newly generated prose"],
            ["Hallucination risk", "None by construction", "Present; needs auditing"],
            ["Readability", "Depends on source style", "High, plain language"],
            ["Admissibility", "Verifiable against source", "Not directly admissible"],
            ["Engine in LexiSum", "Sentence-BERT / TF-IDF + TextRank", "LLM via LiteLLM"],
        ],
        col_widths=[1.6, 2.4, 2.4],
    )
    section(doc, "2.2 Graph-Based Ranking: TextRank")
    add_body(
        doc,
        "TextRank models a document as a graph in which sentences are nodes and "
        "edge weights measure pairwise similarity. A PageRank-style iteration "
        "distributes 'centrality' across the graph, and the highest-scoring "
        "sentences are selected as the summary. The similarity matrix can be "
        "computed lexically with TF-IDF vectors or semantically with "
        "Sentence-BERT embeddings.",
    )
    section(doc, "2.3 Similarity, Embeddings, and Context")
    add_body(
        doc,
        "TF-IDF vectors capture term overlap; Sentence-BERT embeddings capture "
        "meaning. Both feed the same ranking algorithm. For the abstractive "
        "engine, modern LLMs expose a context window measured in tokens; when a "
        "document exceeds that window, a robust system must either use a "
        "larger-window model or chunk the document and merge partial summaries. "
        "LexiSum supports both, automatically.",
    )

    # ---------------- Chapter 3 ----------------
    chapter(doc, 3, "System Overview and Architecture")
    section(doc, "3.1 The Dual-Engine Design")
    add_body(
        doc,
        "Raw contract text enters an ingestion layer that normalizes and splits "
        "it into sentences. The extractive engine ranks those sentences and "
        "returns the top few verbatim. The compliance auditor verifies each "
        "selected clause is an unmodified substring of the source. In parallel, "
        "the abstractive engine writes a two-paragraph executive briefing, "
        "streamed to the user. Finally, a FinOps layer records the actual token "
        "usage so estimated and real costs always reconcile.",
    )
    add_figure(doc, 2)
    section(doc, "3.2 Module Map")
    add_table(
        doc,
        ["Module", "Responsibility"],
        [
            ["src/config.py", "Environment-driven settings, model context limits, provider config"],
            ["src/ingestion/", "Sentence parsing, local loaders, cloud OCR adapters"],
            ["src/extractive/", "TF-IDF and Sentence-BERT TextRank engines"],
            ["src/abstractive/", "LiteLLM generator: streaming, chunking, usage accounting"],
            ["src/compliance/", "Token-level verbatim auditor"],
            ["src/export/", "In-memory DOCX and PDF briefing generation"],
            ["src/cost/", "Pricing table and FinOps estimator/logger"],
            ["src/pipeline.py", "Orchestration and structured streaming events"],
            ["src/batch_processor.py", "Async, concurrency-bounded batch processing"],
            ["app.py / main.py", "Streamlit UI and CLI batch entrypoint"],
            ["benchmark/", "CUAD-based extractive and abstractive benchmarks"],
        ],
        col_widths=[1.9, 4.5],
    )
    section(doc, "3.3 Design Decisions")
    add_body(
        doc,
        "Every significant decision is recorded as an Architecture Decision "
        "Record (ADR) in docs/ARCHITECTURE.md. The nine ADRs cover the "
        "dual-engine split, token-level auditing, the dynamic context strategy, "
        "provider abstraction through LiteLLM, FinOps tracking, in-memory "
        "export, async batch processing, the Streamlit UI, and rate-limit-aware "
        "benchmark batching. Appendix C summarizes them.",
    )

    # ---------------- Chapter 4 ----------------
    chapter(doc, 4, "Ingestion and Text Parsing")
    section(doc, "4.1 From File to Sentences")
    add_body(
        doc,
        "The DocumentParser normalizes raw text, strips control characters, and "
        "splits the document into sentences with spaCy. Because legal documents "
        "are dense and formatted, the parser also records word and sentence "
        "counts that downstream stages use. A sentencizer fallback keeps parsing "
        "working even when the full spaCy pipeline is disabled for speed.",
    )
    add_code(
        doc,
        "parsed = DocumentParser().parse_document(raw_text)\n"
        "sentences = parsed['sentences']\n"
        "print(parsed['total_words'], parsed['total_sentences'])"
    )
    section(doc, "4.2 Local and Cloud Loaders")
    add_body(
        doc,
        "Local loaders accept paths or file-like objects for TXT, PDF, and DOCX, "
        "so the same helpers serve the CLI and the Streamlit UI. For cloud "
        "workflows, optional adapters wrap Google Document AI and AWS Textract, "
        "importing their SDKs lazily so the core install stays lean.",
    )

    # ---------------- Chapter 5 ----------------
    chapter(doc, 5, "The Extractive Engine")
    section(doc, "5.1 Ranking Sentences, Never Paraphrasing")
    add_body(
        doc,
        "The extractive engine returns the most central sentences of a contract "
        "in original document order. Because it selects rather than generates, "
        "the output is verbatim by construction. Two engines implement the same "
        "TextRank algorithm with different similarity signals.",
    )
    add_table(
        doc,
        ["Engine", "Similarity", "Strengths", "Cost"],
        [
            ["TF-IDF + TextRank", "Lexical term overlap", "Fast, zero dependencies", "~0.005 s/contract"],
            ["Sentence-BERT + TextRank", "Semantic embeddings", "Robust to paraphrase", "~1.5 s/contract"],
        ],
        col_widths=[1.6, 1.7, 1.9, 1.2],
    )
    section(doc, "5.2 Scoring")
    add_body(
        doc,
        "Both engines expose a score_sentences method that returns a centrality "
        "score for every sentence. The benchmark harness uses these full "
        "rankings to compute ranking-quality metrics, not just the top few. "
        "Section 5.3 shows the extractor at work in the UI.",
    )
    add_figure(doc, 3)

    # ---------------- Chapter 6 ----------------
    chapter(doc, 6, "The Abstractive Engine")
    section(doc, "6.1 Provider Abstraction with LiteLLM")
    add_body(
        doc,
        "All LLM calls route through LiteLLM, so OpenAI, Azure OpenAI, Google "
        "Vertex, and AWS Bedrock are one model id and one set of credentials "
        "away. Streaming, usage reporting, and batch completion work uniformly "
        "across providers.",
    )
    section(doc, "6.2 The Dynamic Context Strategy")
    add_body(
        doc,
        "Contracts vary in length, and model context windows vary widely. "
        "LexiSum counts tokens with tiktoken and chooses a strategy per "
        "document. In single-shot mode the full document is sent in one call, "
        "which maximizes coherence. In chunked-recursive mode, the document is "
        "split at sentence boundaries with a configurable overlap, each chunk "
        "is summarized in parallel, and the summaries are merged into the final "
        "briefing. The auto strategy picks between the two based on whether the "
        "document fits within seventy percent of the model's window. The system "
        "never truncates silently and never fails with a context overflow.",
    )
    add_figure(doc, 4)
    add_figure(doc, 5)
    section(doc, "6.3 Streaming")
    add_body(
        doc,
        "The final summary streams token by token. Users watch the briefing "
        "appear rather than staring at a spinner, and the pipeline can also "
        "report progress on intermediate chunk summaries.",
    )

    # ---------------- Chapter 7 ----------------
    chapter(doc, 7, "The Compliance Auditor")
    section(doc, "7.1 Why a Naive Check Fails")
    add_body(
        doc,
        "The obvious test, sentence in source, fails on real contracts: curly "
        "quotes, newlines, and double spaces all produce false negatives. A "
        "genuinely verbatim clause can fail a naive check.",
    )
    section(doc, "7.2 Token-Level Verification")
    add_body(
        doc,
        "The auditor normalizes text by removing control characters, unifying "
        "whitespace, and mapping Unicode quotes to their ASCII equivalents. It "
        "then checks for an exact normalized substring; if that fails, it checks "
        "that the sentence's tokens form a contiguous subsequence of the "
        "source's tokens. Fabricated content is still rejected; formatting noise "
        "is not. The extractive audit returns a pass/fail per sentence, and the "
        "abstractive audit performs a structural sanity check on the briefing.",
    )
    add_figure(doc, 6)

    # ---------------- Chapter 8 ----------------
    chapter(doc, 8, "FinOps: Estimating and Tracking Cost")
    section(doc, "8.1 A Single Source of Truth")
    add_body(
        doc,
        "A pricing table in src/cost/pricing.py is the single source of truth "
        "for USD-per-million-token costs. Both the pre-flight estimator and the "
        "post-run cost logger read from it, so estimates and actuals are always "
        "comparable.",
    )
    add_table(
        doc,
        ["Model", "Input /1M", "Output /1M"],
        [
            ["gpt-4o-mini", "$0.15", "$0.60"],
            ["gpt-4o", "$2.50", "$10.00"],
            ["claude-haiku-4-5", "$1.00", "$5.00"],
            ["claude-sonnet-4-5", "$3.00", "$15.00"],
            ["gemini/gemini-3.6-flash", "$0.75", "$3.75"],
        ],
        col_widths=[2.4, 1.5, 1.5],
    )
    section(doc, "8.2 Estimates, Actuals, and Tags")
    add_body(
        doc,
        "Before a user commits, the UI shows an estimated cost per document. "
        "After generation, the pipeline logs the actual token usage to a "
        "JSON-lines file, tagged with environment, team, strategy, and call "
        "count. Because estimates and actuals share one pricing table, the "
        "reconciliation is exact.",
    )
    add_figure(doc, 7)

    # ---------------- Chapter 9 ----------------
    chapter(doc, 9, "Orchestration: Pipeline, Batch, CLI, and UI")
    section(doc, "9.1 The Pipeline")
    add_body(
        doc,
        "LegalSummarizationPipeline runs parse, extract, audit, generate, "
        "structure-audit, and log. It exposes a blocking process_contract method "
        "and a stream_summaries generator that yields structured events so the "
        "UI can render progress progressively.",
    )
    section(doc, "9.2 Async Batch Processing")
    add_body(
        doc,
        "A target workload of two hundred contracts per day rules out "
        "one-at-a-time processing. BatchProcessor bounds in-flight requests with "
        "an asyncio.Semaphore, runs the synchronous pipeline in a thread, and "
        "reports progress through callbacks.",
    )
    section(doc, "9.3 The Streamlit UI")
    add_body(
        doc,
        "The UI accepts multiple PDF, TXT, or DOCX files, offers model, "
        "strategy, and sentence-count controls, shows pre-flight estimates, "
        "streams the abstractive summary, reports actual cost, and exports "
        "DOCX and PDF briefings. A session-only API key field supports "
        "deployments without baked-in secrets.",
    )
    add_figure(doc, 8)
    section(doc, "9.4 The CLI")
    add_body(
        doc,
        "main.py processes a directory of contracts or a single file with "
        "bounded concurrency, writing JSON, DOCX, and PDF outputs per document. "
        "Progress is logged to the console.",
    )
    add_figure(doc, 9)

    # ---------------- Chapter 10 ----------------
    chapter(doc, 10, "The Export Engine")
    add_body(
        doc,
        "Briefings are built directly into memory buffers, avoiding temporary "
        "files and the cleanup, concurrency, and security problems they bring. "
        "The same engine produces DOCX and PDF reports for the UI download "
        "buttons and the CLI. Each report contains document metadata, the "
        "verbatim extractive clauses with their audit verdict, and the "
        "plain-language executive summary.",
    )
    add_code(
        doc,
        "docx_bytes = DocumentExportEngine.create_docx(result)\n"
        "pdf_bytes  = DocumentExportEngine.create_pdf(result)",
    )

    # ---------------- Chapter 11 ----------------
    chapter(doc, 11, "Benchmarking and Results")
    section(doc, "11.1 Corpus and Metrics")
    add_body(
        doc,
        "Both engines are evaluated on the CUAD (Contract Understanding Atticus "
        "Dataset), a corpus of 510 commercial contracts with more than 13,000 "
        "expert annotations across 41 clause types. A 100-contract sample was "
        "used. The extractive task is clause selection, so ranking quality is "
        "measured with MAP and nDCG@10 in addition to precision and recall at "
        "the top few sentences. The abstractive task is evaluated with BERTScore "
        "and a five-dimension LLM-as-judge rubric, plus real per-contract cost.",
    )
    section(doc, "11.2 Extractive Results")
    add_table(
        doc,
        ["Method", "MAP", "nDCG@10", "Prec@3", "Latency (s)", "Verbatim"],
        [
            ["TF-IDF + TextRank", "0.727", "0.855", "0.883", "0.005", "100%"],
            ["Sentence-BERT + TextRank", "0.735", "0.824", "0.873", "1.501", "100%"],
            ["Oracle (gold sentences)", "1.000", "1.000", "1.000", "0.000", "100%"],
        ],
        col_widths=[2.2, 0.9, 1.1, 1.0, 1.2, 1.0],
    )
    add_body(
        doc,
        "The surprising and honestly reported result is that the general "
        "Sentence-BERT model does not meaningfully beat the lexical TF-IDF "
        "baseline on this task, and is roughly three hundred times slower. "
        "Legal clauses are formulaic, so lexical overlap is already a strong "
        "signal; a general encoder adds little. The obvious next experiment is "
        "a legal-domain encoder such as Legal-BERT.",
    )
    section(doc, "11.3 Abstractive Results")
    add_table(
        doc,
        ["Model", "BERTScore F1", "Rubric", "Cost/contract"],
        [
            ["gpt-4o-mini", "0.768", "3.21", "$0.0017"],
            ["claude-haiku-4-5", "0.776", "2.95", "$0.0141"],
            ["gemini/gemini-3.6-flash", "0.702", "1.63", "$0.0112"],
        ],
        col_widths=[2.2, 1.4, 1.0, 1.4],
    )
    add_body(
        doc,
        "Claude Haiku 4.5 leads on BERTScore; GPT-4o-mini wins the rubric and "
        "is roughly eight times cheaper per contract. Rubric scores are modest "
        "overall because a two-paragraph briefing cannot cover the twenty to "
        "fifty clauses an expert flags per contract; this is a property of the "
        "task, not a model failure, and it is exactly why the extractive "
        "verbatim engine exists as a sibling.",
    )
    section(doc, "11.4 Reproduction")
    add_body(
        doc,
        "Every number in this book regenerates from scratch with one command, "
        "so readers can verify the results rather than trusting them.",
    )
    add_code(
        doc,
        "python -m benchmark.reproduce_all",
    )
    add_figure(doc, 10)

    # ---------------- Chapter 12 ----------------
    chapter(doc, 12, "Deployment and Operations")
    section(doc, "12.1 Containers")
    add_body(
        doc,
        "A Dockerfile packages the app with its spaCy model, and a "
        "docker-compose file wires environment variables and a persistent log "
        "volume. One command starts the full stack.",
    )
    add_figure(doc, 11)
    section(doc, "12.2 Hosted UI")
    add_body(
        doc,
        "Streamlit Community Cloud deploys the app directly from the repository. "
        "Because public apps cannot hide secrets, the UI supports a session-only "
        "API key field so users bring their own credentials.",
    )
    section(doc, "12.3 Cloud Provider Matrix")
    add_table(
        doc,
        ["Component", "AWS", "GCP", "Azure"],
        [
            ["Ingestion", "S3 + Textract", "Cloud Storage + Document AI", "Blob + Form Recognizer"],
            ["Abstractive", "Bedrock (Claude)", "Vertex AI (Gemini)", "Azure OpenAI (GPT)"],
            ["Batch", "Step Functions + Lambda", "Cloud Workflows + Cloud Run", "Logic Apps + Functions"],
        ],
        col_widths=[1.4, 2.0, 2.0, 2.0],
    )
    section(doc, "12.4 Operations: Rate Limits and Resumability")
    add_body(
        doc,
        "Provider quotas are the binding constraint in batch LLM workloads. The "
        "benchmark harness chunks requests, bounds concurrency, retries with "
        "backoff, and pauses between batches (ADR-009). Generation is also "
        "resumable: re-running skips already-completed contracts and preserves "
        "other models' records, so a partial run can be continued without "
        "re-paying for completed work.",
    )

    # ---------------- Chapter 13 ----------------
    chapter(doc, 13, "Cost Analysis")
    section(doc, "13.1 Actual Spend for the Benchmark")
    add_body(
        doc,
        "The complete benchmark spent roughly four dollars and sixty cents, "
        "dominated by generation and judge calls. Two failures added about a "
        "dollar and sixty cents of avoidable spend, which is documented openly "
        "in Chapter 14.",
    )
    add_table(
        doc,
        ["Line item", "Cost"],
        [
            ["Extractive benchmark", "$0.00 (local)"],
            ["Abstractive generation (100 contracts x 3 models)", "~$2.70"],
            ["Judge calls (gpt-4o, 45)", "~$0.30"],
            ["Avoidable failures", "~$1.60"],
            ["Total", "~$4.60"],
        ],
        col_widths=[4.2, 1.6],
    )
    section(doc, "13.2 Running Cost at 200 Contracts per Day")
    add_body(
        doc,
        "At two hundred contracts per day, the abstractive engine costs about "
        "thirty-four cents with gpt-4o-mini, or about two dollars and eighty-two "
        "cents with claude-haiku-4-5. The extractive engine runs locally and "
        "adds no per-call cost. These figures make the quality-per-dollar "
        "trade-off concrete: the cheapest model is also the rubric winner.",
    )

    # ---------------- Chapter 14 ----------------
    chapter(doc, 14, "Lessons Learned and Failure Modes")
    section(doc, "14.1 The Rate-Limit Wall")
    add_body(
        doc,
        "The first benchmark run fired one hundred concurrent requests because "
        "LiteLLM's batch completion defaults to one hundred workers. Gemini's "
        "free tier hard-capped at five requests per minute, failing ninety-two "
        "of one hundred contracts; OpenAI hit its tokens-per-minute cap "
        "mid-run. The remedy became ADR-009: chunk, bound concurrency, retry "
        "with backoff, and delay between batches.",
    )
    section(doc, "14.2 The Merge Bug")
    add_body(
        doc,
        "A resume feature meant to skip completed contracts had a bug: running a "
        "single model overwrote the results file and deleted the other two "
        "models' records, forcing an avoidable re-run of about one dollar and "
        "fifty-eight cents. The fix is committed with three unit tests that "
        "guard cross-model preservation. Resumability is a correctness feature "
        "and deserves tests like one.",
    )
    section(doc, "14.3 The Hypothesis That Failed")
    add_body(
        doc,
        "The assumption that Sentence-BERT would clearly outperform TF-IDF on "
        "clause selection was disproven by the benchmark. The negative result is "
        "published rather than hidden, because the purpose of a benchmark is to "
        "replace assumptions with numbers. The experiment that is now obvious a "
        "legal-domain encoder is exactly the kind of contribution the roadmap "
        "invites.",
    )
    section(doc, "14.4 What I Would Do Differently")
    add_bullets(
        doc,
        [
            "Treat provider quota as a first-class design constraint from day one.",
            "Write tests for data-integrity features such as resumable runs before shipping them.",
            "Smoke-test every provider and model id before spending real money on a full run.",
            "Design the evaluation to measure ranking quality, not just top-N accuracy.",
        ],
    )

    # ---------------- Chapter 15 ----------------
    chapter(doc, 15, "Roadmap and Future Work")
    add_table(
        doc,
        ["Work item", "Status"],
        [
            ["Dual-engine pipeline with verbatim audit", "Done"],
            ["Streaming UI and FinOps cost tracking", "Done"],
            ["Docker, tests, and reproducible CUAD benchmarks", "Done"],
            ["Fine-tuned Legal-BERT extractive engine", "Planned"],
            ["Cloud storage ingestion (--from-s3, --from-gcs)", "Planned"],
            ["Multi-tenant authentication", "Planned"],
        ],
        col_widths=[4.6, 1.4],
    )
    add_body(
        doc,
        "The natural next experiments are a legal-domain extractive encoder "
        "benchmarked head-to-head against Sentence-BERT, cloud storage "
        "ingestion for batch workflows, and authentication for real "
        "deployments. Contribution guidelines and good-first-issue labels make "
        "these accessible entry points for new contributors.",
    )

    # ---------------- Appendix A ----------------
    doc.add_page_break()
    doc.add_heading("Appendix A — Quick Reference", level=1)
    add_table(
        doc,
        ["Command", "Purpose"],
        [
            ["pip install -r requirements.txt", "Install runtime dependencies"],
            ["python -m spacy download en_core_web_sm", "Download the sentence model"],
            ["streamlit run app.py", "Launch the UI"],
            ["python main.py --input-dir ./contracts", "Batch-process a directory"],
            ["pytest tests/ -v", "Run the test suite"],
            ["python -m benchmark.reproduce_all", "Reproduce all benchmarks"],
            ["docker compose up --build", "Run the full stack"],
        ],
        col_widths=[3.6, 3.0],
    )

    # ---------------- Appendix B ----------------
    doc.add_page_break()
    doc.add_heading("Appendix B — Demo GIF Production List", level=1)
    add_body(
        doc,
        "The eleven figures below appear in this document in exactly this order. "
        "Record each GIF, save it to the path shown, and insert it at the "
        "corresponding Figure N placeholder in Word. Keep each clip between "
        "eight and twelve seconds, under five megabytes, at 720p.",
    )
    rows = [
        [str(g["fig"]), g["path"], f"Chapter {g['chapter']}", g["caption"]]
        for g in sorted(GIFS, key=lambda x: x["fig"])
    ]
    add_table(
        doc,
        ["Figure", "File path", "Chapter", "What to record"],
        rows,
        col_widths=[0.7, 2.3, 1.1, 3.2],
    )

    # ---------------- Appendix C ----------------
    doc.add_page_break()
    doc.add_heading("Appendix C — Architecture Decision Records (Summary)", level=1)
    add_table(
        doc,
        ["ADR", "Decision"],
        [
            ["ADR-001", "Decouple extractive and abstractive engines"],
            ["ADR-002", "Token-level verbatim auditing instead of substring matching"],
            ["ADR-003", "Dynamic context strategy (auto / single-shot / chunked-recursive)"],
            ["ADR-004", "Provider-agnostic via LiteLLM"],
            ["ADR-005", "FinOps tracking with estimates and actuals"],
            ["ADR-006", "In-memory document export"],
            ["ADR-007", "Async batch processing with bounded concurrency"],
            ["ADR-008", "Streamlit for the UI"],
            ["ADR-009", "Rate-limit-aware benchmark batching"],
        ],
        col_widths=[0.8, 5.6],
    )

    # ---------------- Appendix D ----------------
    doc.add_page_break()
    doc.add_heading("Appendix D — Glossary", level=1)
    add_table(
        doc,
        ["Term", "Definition"],
        [
            ["Abstractive", "Generating new sentences to summarize a document"],
            ["ADR", "Architecture Decision Record; a documented design decision"],
            ["BERTScore", "Semantic similarity metric for generated text"],
            ["CUAD", "Contract Understanding Atticus Dataset"],
            ["Extractive", "Selecting existing sentences verbatim"],
            ["FinOps", "Financial operations: tracking and reconciling cloud cost"],
            ["LiteLLM", "A library that unifies LLM providers behind one API"],
            ["MAP", "Mean average precision; a ranking-quality metric"],
            ["nDCG", "Normalized discounted cumulative gain; a ranking-quality metric"],
            ["TextRank", "Graph-based sentence-ranking algorithm"],
            ["Verbatim", "Word-for-word, unmodified"],
        ],
        col_widths=[1.4, 5.2],
    )

    doc.core_properties.title = "LexiSum: A Technical Reference"
    doc.core_properties.author = "Koate"
    doc.save(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    build()