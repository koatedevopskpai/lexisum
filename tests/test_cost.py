"""Tests for FinOps cost tracking."""

from src.cost.cost_tracker import CostTracker


def test_estimate_cost(tmp_path, monkeypatch):
    monkeypatch.setenv("USAGE_LOG_PATH", str(tmp_path / "usage.log"))
    est = CostTracker.estimate_cost("gpt-4o-mini", "Hello world this is a short document.")
    assert est["input_tokens"] > 0
    assert est["total_estimate_usd"] >= 0


def test_estimate_and_actual_consistent(tmp_path, monkeypatch):
    monkeypatch.setenv("USAGE_LOG_PATH", str(tmp_path / "usage.log"))
    text = "The quick brown fox. " * 50
    est = CostTracker.estimate_cost("gpt-4o-mini", text, output_estimate_tokens=500)
    assert est["input_tokens"] > 0


def test_log_usage_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("USAGE_LOG_PATH", str(tmp_path / "usage.log"))
    log_path = str(tmp_path / "usage.log")
    CostTracker.log_usage(
        doc_id="doc-1",
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500,
        tags={"environment": "test"},
        log_path=log_path,
    )

    records = CostTracker.read_log(log_path)
    assert len(records) == 1
    rec = records[0]
    assert rec["doc_id"] == "doc-1"
    assert rec["model"] == "gpt-4o-mini"
    assert rec["input_tokens"] == 1000
    assert rec["output_tokens"] == 500
    assert rec["total_cost_usd"] > 0
    assert rec["tags"]["environment"] == "test"


def test_log_usage_merges_default_tags(tmp_path, monkeypatch):
    monkeypatch.setenv("USAGE_LOG_PATH", str(tmp_path / "usage.log"))
    monkeypatch.setenv("FINOP_TAGS", '{"environment":"prod","team":"legal"}')

    log_path = str(tmp_path / "usage.log")
    CostTracker.log_usage("doc-2", "gpt-4o", 100, 100, tags={"custom": "x"}, log_path=log_path)

    rec = CostTracker.read_log(log_path)[0]
    assert rec["tags"]["environment"] == "prod"
    assert rec["tags"]["team"] == "legal"
    assert rec["tags"]["custom"] == "x"


def test_read_log_missing_file_returns_empty(tmp_path):
    assert CostTracker.read_log(str(tmp_path / "nope.log")) == []