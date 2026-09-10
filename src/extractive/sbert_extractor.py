"""
Sentence-BERT + TextRank extractive summariser (recommended).

Replaces the TF-IDF similarity matrix with Sentence-BERT embeddings so the
ranking captures *semantic* similarity between legal clauses rather than
lexical overlap. Sentences are returned verbatim - never paraphrased.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class SBertExtractor:
    """Semantic TextRank extractor built on Sentence-Transformers embeddings."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        damping: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-4,
    ) -> None:
        self.model_name = model_name
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def extract_verbatim_summary(self, sentences: List[str], top_n: int = 3) -> List[str]:
        """
        Rank sentences via TextRank over SBERT cosine similarities.
        Returns the top_n sentences in original document order.
        """
        if len(sentences) <= top_n:
            return list(sentences)

        model = self._load_model()
        embeddings = model.encode(sentences, show_progress_bar=False)
        embeddings = np.asarray(embeddings, dtype=np.float32)

        sim = cosine_similarity(embeddings)
        np.fill_diagonal(sim, 0)

        row_sums = sim.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        transition = sim / row_sums

        n = len(sentences)
        scores = np.ones(n) / n
        for _ in range(self.max_iter):
            prev = scores.copy()
            scores = (1 - self.damping) / n + self.damping * transition.T.dot(scores)
            if np.linalg.norm(scores - prev) < self.tol:
                break

        top_idx = np.argsort(scores)[-top_n:]
        return [sentences[i] for i in sorted(top_idx)]