"""
Core orchestration pipeline for LexiSum.

A single `process_contract` call runs the full dual-engine flow:

  1. Parse & normalise the raw contract text.
  2. Extractive: select top-N verbatim clauses (SBERT or TextRank).
  3. Compliance: verify the selected clauses appear verbatim in the source.
  4. Abstractive: generate a plain-language 2-paragraph summary (streaming,
     with context-strategy support).
  5. Compliance: structural audit of the abstractive output.
  6. FinOps: log actual token usage with tags.

A `stream_summaries` generator variant yields structured events so the UI
can render progressive output and live-streaming.
"""

from __future__ import annotations

from typing import Any, Dict, Generator, Optional

from src.abstractive.llm_generator import AbstractiveGenerator
from src.compliance.verbatim_auditor import VerbatimAuditor
from src.config import settings
from src.cost.cost_tracker import CostTracker
from src.extractive.sbert_extractor import SBertExtractor
from src.extractive.textrank_extractor import TextRankExtractor
from src.ingestion.document_parser import DocumentParser


def _build_extractor(engine: Optional[str] = None):
    engine = (engine or settings.extractive_engine).lower()
    if engine == "textrank":
        return TextRankExtractor()
    return SBertExtractor(model_name=settings.sbert_model)


class LegalSummarizationPipeline:
    """Dual-engine extractive + abstractive legal summarisation pipeline."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        extractive_top_n: Optional[int] = None,
        strategy: Optional[str] = None,
        extractive_engine: Optional[str] = None,
    ) -> None:
        self.parser = DocumentParser()
        self.extractor = _build_extractor(extractive_engine)
        self.abstractor = AbstractiveGenerator(
            model_name or settings.abstractive_model,
            strategy=strategy,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
        )
        self.auditor = VerbatimAuditor()
        self.model_name = self.abstractor.model_name
        self.top_n = extractive_top_n or settings.extractive_top_n

    # ------------------------------------------------------------------
    # Blocking entry point
    # ------------------------------------------------------------------
    def process_contract(self, raw_text: str, doc_id: str = "unknown") -> Dict[str, Any]:
        """Run the full pipeline and return a complete result dict."""
        result: Dict[str, Any] = {}
        usage: Dict[str, Any] = {}
        for event in self.stream_summaries(raw_text, doc_id):
            if event["stage"] == "complete":
                result = event["result"]
                usage = event["usage"]
        return {"result": result, "usage": usage}

    # ------------------------------------------------------------------
    # Streaming entry point (UI-friendly)
    # ------------------------------------------------------------------
    def stream_summaries(
        self, raw_text: str, doc_id: str = "unknown"
    ) -> Generator[Dict[str, Any], None, None]:
        """Yield structured pipeline events as work progresses."""
        # 1. Extractive
        parsed = self.parser.parse_document(raw_text)
        ext_sentences = self.extractor.extract_verbatim_summary(
            parsed["sentences"], top_n=self.top_n
        )
        ext_audit = self.auditor.audit_extractive(raw_text, ext_sentences)
        yield {"stage": "extractive", "sentences": ext_sentences, "audit": ext_audit}

        # 2. Abstractive (streamed)
        full_text = ""
        for delta in self.abstractor.generate_plain_language_summary_stream(raw_text):
            full_text += delta
            yield {"stage": "abstractive", "delta": delta}

        abs_audit = self.auditor.audit_abstractive(full_text)

        # 3. FinOps logging (actuals)
        usage = self.abstractor.get_usage()
        CostTracker.log_usage(
            doc_id=doc_id,
            model=self.model_name,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            tags={
                "strategy": usage["strategy"],
                "calls": usage["calls"],
                "top_n": self.top_n,
                "engine": self._engine_name(),
            },
        )

        # 4. Assemble result
        result = {
            "metadata": {
                "word_count": parsed["total_words"],
                "total_sentences": parsed["total_sentences"],
            },
            "extractive_summary": {
                "sentences": ext_sentences,
                "compliance_verified": ext_audit["passed"],
                "audit": ext_audit,
            },
            "abstractive_summary": {
                "text": full_text,
                "structure_verified": abs_audit["passed"],
            },
        }
        yield {"stage": "complete", "result": result, "usage": usage}

    def _engine_name(self) -> str:
        return "sbert" if isinstance(self.extractor, SBertExtractor) else "textrank"