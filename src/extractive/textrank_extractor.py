"""
TF-IDF + TextRank extractive summariser (baseline).

Ranks sentences via the TextRank graph algorithm where edge weights come
from cosine similarity of TF-IDF sentence vectors. This is a lexical
baseline; the SBERT extractor is the semantic alternative.
"""

from __future__ import annotations

from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TextRankExtractor:
    """Lexical TextRank extractor using TF-IDF similarity."""

    def __init__(
        self,
        damping: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-4,
    ) -> None:
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol

    def score_sentences(self, sentences: List[str]) -> np.ndarray:
        """Return a centrality score for every sentence."""
        n = len(sentences)
        if n == 0:
            return np.array([])
        if n == 1:
            return np.array([1.0])

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf = vectorizer.fit_transform(sentences)
            sim = cosine_similarity(tfidf)
        except ValueError:
            # No vocabulary (e.g. all stop-words): fall back to uniform.
            return np.ones(n) / n

        np.fill_diagonal(sim, 0)
        row_sums = sim.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        transition = sim / row_sums

        scores = np.ones(n) / n
        for _ in range(self.max_iter):
            prev = scores.copy()
            scores = (1 - self.damping) / n + self.damping * transition.T.dot(scores)
            if np.linalg.norm(scores - prev) < self.tol:
                break
        return scores

    def extract_verbatim_summary(self, sentences: List[str], top_n: int = 3) -> List[str]:
        """
        Return the `top_n` most central sentences, in original document order.
        Sentences are returned verbatim (never paraphrased).
        """
        if len(sentences) <= top_n:
            return list(sentences)
        scores = self.score_sentences(sentences)
        top_idx = np.argsort(scores)[-top_n:]
        return [sentences[i] for i in sorted(top_idx)]