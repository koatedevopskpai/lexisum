"""End-to-end pipeline tests with mocked extractive + abstractive engines."""

import pytest

from src.pipeline import LegalSummarizationPipeline

SAMPLE_CONTRACT = (
    "This Service Agreement is entered into between Acme Corp and Beta LLC. "
    "Acme shall provide cloud hosting services to Beta. "
    "Beta shall pay Acme a monthly fee of one thousand dollars. "
    "Either party may terminate this agreement with thirty days written notice. "
    "Acme shall indemnify Beta against third party claims arising from the services. "
    "Confidential information exchanged shall be protected for three years. "
    "This agreement is governed by the laws of Delaware. "
)


class FakeExtractor:
    """Returns fixed verbatim sentences."""

    def extract_verbatim_summary(self, sentences, top_n=3):
        if len(sentences) <= top_n:
            return list(sentences)
        return [sentences[0], sentences[2], sentences[4]]


class FakeAbstractor:
    def __init__(self, *args, **kwargs):
        self.total_input_tokens = 100
        self.total_output_tokens = 50
        self.call_count = 1
        self.strategy_used = "single_shot"
        self.model_name = "gpt-4o-mini"

    def generate_plain_language_summary_stream(self, document_text):
        yield "This is the first paragraph of the executive summary."
        yield " "
        yield "This is the second paragraph covering liabilities and termination."
        yield "\n\n"
        yield "This is the final paragraph."

    def get_usage(self):
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "calls": self.call_count,
            "strategy": self.strategy_used,
        }


@pytest.fixture
def pipeline(monkeypatch, tmp_path):
    # Force a fake extractor (no model download) and a fake abstractor.
    monkeypatch.setenv("USAGE_LOG_PATH", str(tmp_path / "usage.log"))

    import src.pipeline as pipeline_module

    monkeypatch.setattr(pipeline_module, "TextRankExtractor", FakeExtractor)
    monkeypatch.setattr(pipeline_module, "SBertExtractor", FakeExtractor)
    monkeypatch.setattr(pipeline_module, "AbstractiveGenerator", FakeAbstractor)

    return LegalSummarizationPipeline(extractive_engine="textrank")


def test_process_contract_complete(pipeline):
    out = pipeline.process_contract(SAMPLE_CONTRACT, doc_id="test-1")
    result = out["result"]

    # Extractive
    assert result["extractive_summary"]["compliance_verified"] is True
    assert len(result["extractive_summary"]["sentences"]) == 3

    # Abstractive
    assert len(result["abstractive_summary"]["text"]) > 0

    # Metadata
    assert result["metadata"]["total_sentences"] > 0

    # Usage
    assert out["usage"]["input_tokens"] == 100
    assert out["usage"]["strategy"] == "single_shot"


def test_stream_summaries_events(pipeline):
    events = list(pipeline.stream_summaries(SAMPLE_CONTRACT, doc_id="test-2"))
    stages = [e["stage"] for e in events]
    assert stages[0] == "extractive"
    assert "abstractive" in stages
    assert stages[-1] == "complete"

    complete = events[-1]
    assert complete["result"]["abstractive_summary"]["text"]
    assert "usage" in complete


def test_pipeline_logs_usage(pipeline, tmp_path):
    pipeline.process_contract(SAMPLE_CONTRACT, doc_id="cost-test")
    log_file = tmp_path / "usage.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "cost-test" in content