"""Tests for the token-level verbatim auditor."""

from src.compliance.verbatim_auditor import VerbatimAuditor


def test_exact_substring_match():
    auditor = VerbatimAuditor()
    source = "The Party shall indemnify the other Party. This is the end."
    sentence = "The Party shall indemnify the other Party."
    assert auditor.is_verbatim(sentence, source)


def test_tolerates_punctuation_and_whitespace():
    auditor = VerbatimAuditor()
    source = "Seller will  indemnify Buyer.\n\nFor   any breach."
    sentence = "Seller will indemnify Buyer."
    assert auditor.is_verbatim(sentence, source)


def test_tolerates_curly_quotes():
    auditor = VerbatimAuditor()
    source = 'The "Agreement" governs this relationship.'
    sentence = "The \u201cAgreement\u201d governs this relationship."
    assert auditor.is_verbatim(sentence, source)


def test_token_subsequence_fallback():
    auditor = VerbatimAuditor()
    source = "This contract has many clauses. The Governing Law is New York."
    # Punctuation differs (period vs comma) so exact fails, token match should pass.
    sentence = "The Governing Law is New York"
    assert auditor.is_verbatim(sentence, source)


def test_rejects_fabricated_content():
    auditor = VerbatimAuditor()
    source = "Only these words appear in the source document."
    sentence = "A completely fabricated sentence about taxes."
    assert not auditor.is_verbatim(sentence, source)


def test_empty_sentence_is_not_verbatim():
    auditor = VerbatimAuditor()
    assert not auditor.is_verbatim("", "some source text")


def test_audit_extractive_pass_and_fail():
    auditor = VerbatimAuditor()
    source = "Party A agrees. Party B shall pay within 30 days."
    passed = auditor.audit_extractive(source, ["Party A agrees.", "Party B shall pay within 30 days."])
    assert passed["passed"] is True

    failed = auditor.audit_extractive(source, ["Party A agrees.", "This clause does not exist."])
    assert failed["passed"] is False
    assert failed["details"][1]["is_verbatim"] is False


def test_audit_abstractive_structure():
    auditor = VerbatimAuditor()
    good = auditor.audit_abstractive("Paragraph one is a long summary sentence.\n\nParagraph two follows.")
    assert good["passed"] is True

    bad = auditor.audit_abstractive("")
    assert bad["passed"] is False