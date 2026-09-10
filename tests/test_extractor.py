"""Tests for extractive summarisation engines."""

import numpy as np

from src.extractive.sbert_extractor import SBertExtractor
from src.extractive.textrank_extractor import TextRankExtractor

DOC_SENTENCES = [
    "The Company shall provide consulting services.",
    "Either party may terminate this agreement with thirty days notice.",
    "Payment is due within thirty days of invoice.",
    "This clause covers indemnification of the parties.",
    "Confidential information shall not be disclosed.",
]


def test_textrank_returns_verbatim_sentences():
    extractor = TextRankExtractor()
    selected = extractor.extract_verbatim_summary(DOC_SENTENCES, top_n=3)
    assert len(selected) == 3
    assert all(s in DOC_SENTENCES for s in selected)


def test_textrank_respects_top_n():
    extractor = TextRankExtractor()
    selected = extractor.extract_verbatim_summary(DOC_SENTENCES, top_n=2)
    assert len(selected) == 2


def test_textrank_short_input_returns_all():
    extractor = TextRankExtractor()
    selected = extractor.extract_verbatim_summary(DOC_SENTENCES[:2], top_n=3)
    assert len(selected) == 2


def test_sbert_returns_verbatim_sentences(monkeypatch):
    """Test SBERT logic without downloading an embedding model."""
    extractor = SBertExtractor()

    # Fake an embedding model returning random unit vectors.
    class FakeModel:
        def encode(self, sentences, show_progress_bar=False):
            rng = np.random.default_rng(0)
            vecs = rng.normal(size=(len(sentences), 4))
            norm = np.linalg.norm(vecs, axis=1, keepdims=True)
            norm[norm == 0] = 1
            return vecs / norm

    extractor._model = FakeModel()

    selected = extractor.extract_verbatim_summary(DOC_SENTENCES, top_n=3)
    assert len(selected) == 3
    assert all(s in DOC_SENTENCES for s in selected)


def test_sbert_short_input_returns_all(monkeypatch):
    extractor = SBertExtractor()

    class FakeModel:
        def encode(self, sentences, show_progress_bar=False):
            return np.zeros((len(sentences), 4))

    extractor._model = FakeModel()
    selected = extractor.extract_verbatim_summary(DOC_SENTENCES[:1], top_n=3)
    assert selected == DOC_SENTENCES[:1]