"""Small authored fixture; no provider calls or downloaded language models."""
import io
import json
import socket
import zipfile

import pytest

from src.compliance.verbatim_auditor import VerbatimAuditor
from src.cost.cost_tracker import CostTracker
from src.export.document_generator import DocumentExportEngine
from src.extractive.textrank_extractor import TextRankExtractor
from src.ingestion.document_parser import DocumentParser

TEXT = ('The supplier shall provide maintenance services. '
        'Payment is due within thirty days of invoice. '
        'Either party may terminate with fourteen days of written notice. '
        'Confidential information shall not be disclosed.')


def test_real_parse_rank_audit_export_chain():
    parsed = DocumentParser(model_name='lexisum_offline_missing_model').parse_document(TEXT)
    assert parsed['total_sentences'] == 4
    selected = TextRankExtractor().extract_verbatim_summary(parsed['sentences'], top_n=2)
    assert len(selected) == 2
    assert all(s in parsed['sentences'] for s in selected)
    auditor = VerbatimAuditor(model_name='lexisum_offline_missing_model')
    audit = auditor.audit_extractive(TEXT, selected)
    assert audit['passed']
    result = {'metadata': {'total_sentences': 4},
              'extractive_summary': {'sentences': selected, 'audit': audit, 'compliance_verified': audit['passed']},
              'abstractive_summary': {'text': 'A fixture briefing only. No generated-summary fidelity is asserted.', 'structure_verified': True}}
    docx = DocumentExportEngine.create_docx(result)
    with zipfile.ZipFile(io.BytesIO(docx)) as package:
        xml = package.read('word/document.xml').decode('utf-8')
    assert all(sentence in xml for sentence in selected)
    assert DocumentExportEngine.create_pdf(result).startswith(b'%PDF')


def test_cost_ledger_uses_supplied_usage_and_survives_readback(tmp_path):
    ledger = str(tmp_path/'usage.jsonl')
    # Published internal snapshot rates: 1M input at .15 and 2M output at .60.
    # This verifies accounting arithmetic, not current provider prices.
    CostTracker.log_usage('fixture', 'gpt-4o-mini', 1_000_000, 2_000_000,
                          tags={'scope': 'offline_fixture'}, log_path=ledger)
    record = CostTracker.read_log(ledger)[0]
    assert record['input_cost_usd'] == 0.15
    assert record['output_cost_usd'] == 1.20
    assert record['total_cost_usd'] == 1.35
    assert record['tags']['scope'] == 'offline_fixture'


def test_estimator_accounts_for_a_fixed_token_count_without_encoder_download(tmp_path, monkeypatch):
    import tiktoken
    class FixedEncoder:
        def encode(self, text):
            return list(range(10))
    monkeypatch.setattr(tiktoken, 'encoding_for_model', lambda model: FixedEncoder())
    estimate = CostTracker.estimate_cost('gpt-4o-mini', 'Tokenisation is supplied by the fixture.', output_estimate_tokens=100)
    assert estimate['input_tokens'] == 10
    assert estimate['estimated_output_tokens'] == 100
    assert estimate['input_cost_usd'] == 0.000002
    assert estimate['output_cost_usd'] == 0.000060


def test_offline_profile_blocks_network_access():
    with pytest.raises(RuntimeError, match='Network disabled'):
        socket.create_connection(('example.invalid', 443))


def test_empty_document_does_not_invent_clauses():
    parsed = DocumentParser(model_name='lexisum_offline_missing_model').parse_document('  ')
    assert parsed['sentences'] == []
    assert TextRankExtractor().extract_verbatim_summary([], top_n=3) == []
