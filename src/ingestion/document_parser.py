"""
Document parser that normalises raw text and splits it into sentences.

Legal documents are often dense and highly structured (numbered clauses,
section headers). We split on sentence boundaries using spaCy and keep
lightweight metadata (word count, sentence count) for downstream stages.
"""

from __future__ import annotations

import re
from typing import Dict, List

import spacy
from spacy.lang.en import English


class DocumentParser:
    """Parse and normalise raw contract text into sentences + metadata."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        try:
            self.nlp = spacy.load(model_name, disable=["ner", "tagger", "parser"])
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")
        except OSError:
            self.nlp = English()
            self.nlp.add_pipe("sentencizer")
        self.nlp.max_length = 3_000_000

    def parse_document(self, raw_text: str) -> Dict[str, object]:
        """
        Parse raw text into a dict with:
          - "sentences": list of non-empty, stripped sentences
          - "total_words": approximate word count
          - "total_sentences": number of sentences
        """
        text = self._clean(raw_text)
        if not text.strip():
            return {"sentences": [], "total_words": 0, "total_sentences": 0}

        doc = self.nlp(text)
        sentences: List[str] = []
        for sent in doc.sents:
            s = re.sub(r"\s+", " ", sent.text).strip()
            if s:
                sentences.append(s)

        return {
            "sentences": sentences,
            "total_words": len(re.findall(r"\b\w+\b", text)),
            "total_sentences": len(sentences),
        }

    @staticmethod
    def _clean(text: str) -> str:
        """Strip control characters and normalise whitespace."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()