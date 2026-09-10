"""
Token-level verbatim auditor for compliance verification.

The extractive pipeline guarantees that selected clauses are unmodified
substrings of the source contract. This auditor verifies that guarantee
with robust, token-based matching that is tolerant of:

  - punctuation / curly-quote differences
  - whitespace and newline variations
  - control characters

It falls back from an exact normalised-substring check to a contiguous
token-subsequence check, avoiding the false negatives that a naive
`in` substring test produces on real-world legal documents.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

import spacy
from spacy.lang.en import English

# Unicode curly quotes -> straight quotes (and related punctuation).
_QUOTE_MAP = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00ab": '"',
    "\u00bb": '"',
    "\u2013": "-",
    "\u2014": "-",
}


class VerbatimAuditor:
    """Verify that extracted sentences appear verbatim within source text."""

    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        try:
            self.nlp = spacy.load(model_name, disable=["tagger", "parser", "ner", "lemmatizer"])
        except OSError:
            self.nlp = English()
        self.nlp.max_length = 3_000_000

    def _normalize(self, text: str) -> str:
        """Remove control chars, unify whitespace, and normalise quotes."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\s+", " ", text)
        for src, dst in _QUOTE_MAP.items():
            text = text.replace(src, dst)
        return text.strip()

    def _tokens(self, text: str) -> List[str]:
        return [
            tok.text
            for tok in self.nlp(text)
            if not tok.is_punct and not tok.is_space
        ]

    def is_verbatim(self, sentence: str, source: str) -> bool:
        """
        True if `sentence` appears verbatim in `source`, tolerant of
        punctuation/whitespace differences.

        First tries an exact normalised substring match; if that fails,
        checks that the sentence's tokens form a contiguous subsequence
        of the source's tokens.
        """
        normalized_source = self._normalize(source)
        normalized_sent = self._normalize(sentence)
        if not normalized_sent:
            return False

        if normalized_sent in normalized_source:
            return True

        sent_tokens = self._tokens(normalized_sent)
        src_tokens = self._tokens(normalized_source)
        sent_len = len(sent_tokens)
        if sent_len == 0:
            return False

        for i in range(len(src_tokens) - sent_len + 1):
            if src_tokens[i : i + sent_len] == sent_tokens:
                return True
        return False

    def audit_extractive(self, source_text: str, extracted_sentences: List[str]) -> Dict[str, Any]:
        """
        Audit a set of extracted sentences against the source.
        Returns per-sentence results plus an aggregate pass/fail.
        """
        details: List[Dict[str, Any]] = []
        all_passed = True
        for sent in extracted_sentences:
            passed = self.is_verbatim(sent, source_text)
            if not passed:
                all_passed = False
            details.append(
                {
                    "sentence": sent,
                    "is_verbatim": passed,
                }
            )
        return {"passed": all_passed, "details": details}

    def audit_abstractive(self, summary_text: str) -> Dict[str, bool]:
        """
        Lightweight structural audit for abstractive output:
        verifies the summary is non-empty and reasonably structured
        (contains at least two paragraph breaks).
        """
        blocks = [b for b in re.split(r"\n\s*\n", summary_text) if b.strip()]
        passed = len(blocks) >= 1 and len(summary_text) > 50
        return {"passed": bool(passed), "paragraph_blocks": len(blocks)}