"""Tests for the DOCX / PDF export engine."""

from src.export.document_generator import DocumentExportEngine

SAMPLE_RESULT = {
    "metadata": {"word_count": 150, "total_sentences": 10},
    "extractive_summary": {
        "sentences": ["Clause one sentence.", "Clause two sentence."],
        "compliance_verified": True,
        "audit": {"passed": True, "details": []},
    },
    "abstractive_summary": {
        "text": "First paragraph of the summary.\n\nSecond paragraph covering risks.",
        "structure_verified": True,
    },
}


def test_create_docx_returns_valid_bytes():
    data = DocumentExportEngine.create_docx(SAMPLE_RESULT, doc_title="Test")
    assert data.startswith(b"PK")  # DOCX is a zip container


def test_create_pdf_returns_valid_bytes():
    data = DocumentExportEngine.create_pdf(SAMPLE_RESULT, doc_title="Test")
    assert data.startswith(b"%PDF")


def test_export_handles_unicode():
    result = {
        "metadata": {},
        "extractive_summary": {"sentences": ["Caf\u00e9 & co <test>"], "compliance_verified": True, "audit": {}},
        "abstractive_summary": {"text": "Some \u201cquoted\u201d text.", "structure_verified": True},
    }
    pdf = DocumentExportEngine.create_pdf(result)
    assert pdf.startswith(b"%PDF")

    docx = DocumentExportEngine.create_docx(result)
    assert docx.startswith(b"PK")