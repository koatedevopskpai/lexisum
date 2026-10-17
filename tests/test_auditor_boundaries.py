"""Document consequential boundaries without changing matching behaviour."""
import pytest
from src.compliance.verbatim_auditor import VerbatimAuditor

@pytest.fixture(scope="module")
def auditor():
    # Use the built-in English fallback; no model download is needed.
    return VerbatimAuditor(model_name="lexisum_missing_fixture_model")

def test_pass_does_not_mean_byte_identity(auditor):
    source = 'Buyer  shall pay. '
    candidate = 'Buyer shall pay.'
    assert candidate not in source
    assert auditor.is_verbatim(candidate, source)

def test_irrelevant_source_text_can_pass(auditor):
    assert auditor.is_verbatim('The cover is blue.', 'The cover is blue. Payment is due tomorrow.')

def test_substring_can_omit_a_condition(auditor):
    assert auditor.is_verbatim('Buyer may terminate', 'Buyer may terminate only with written consent.')

def test_token_matching_accepts_punctuation_change(auditor):
    assert auditor.is_verbatim('Buyer pays; Seller ships.', 'Buyer pays. Seller ships.')

def test_empty_extraction_list_currently_passes(auditor):
    assert auditor.audit_extractive('No clauses selected.', [])['passed'] is True

def test_structure_check_can_accept_unsupported_single_paragraph(auditor):
    result = auditor.audit_abstractive('An invented outcome with no source support still exceeds fifty characters.')
    assert result['passed'] is True
    assert result['paragraph_blocks'] == 1
