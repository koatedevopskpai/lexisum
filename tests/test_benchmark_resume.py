"""Tests for the resumable abstractive benchmark merge logic (offline)."""

import json

from benchmark import run_abstractive_benchmark as rb


def _make_contracts(n: int) -> list:
    return [{"contract_id": f"C{i}", "contract_text": "x" * 500} for i in range(n)]


def _record(contract_id: str, model: str, error=None) -> dict:
    return {
        "contract_id": contract_id,
        "model": model,
        "summary": "" if error else f"s-{contract_id}",
        "error": error,
        "input_tokens": 0 if error else 1,
        "output_tokens": 0 if error else 1,
        "cost_usd": 0.0,
    }


def test_resume_preserves_other_models(tmp_path, monkeypatch):
    """Records for models NOT in the current run must be preserved."""
    json.dump(_make_contracts(3), open(tmp_path / "cuad_sample.json", "w"))
    existing = [_record("C1", "M1"), _record("C2", "M1", error="old fail")]
    json.dump(existing, open(tmp_path / "abstractive_results.json", "w"))

    calls = []

    def fake(model, contracts, **kw):
        calls.append((model, [c["contract_id"] for c in contracts]))
        return [_record(c["contract_id"], model) for c in contracts]

    monkeypatch.setattr(rb, "run_single_model_on_contracts", fake)

    rb.run_abstractive_benchmark(
        sample_size=3, output_dir=str(tmp_path), models=["M2"],
        batch_size=1, max_concurrency=1, batch_delay=0,
    )

    res = json.load(open(tmp_path / "abstractive_results.json", encoding="utf-8"))
    by_model = {}
    for r in res:
        by_model.setdefault(r["model"], []).append(r["contract_id"])
    assert by_model["M1"] == ["C1", "C2"]  # untouched by the M2 run
    assert by_model["M2"] == ["C0", "C1", "C2"]
    assert calls == [("M2", ["C0", "C1", "C2"])]


def test_resume_replaces_errors_only(tmp_path, monkeypatch):
    """Only previously-failed contracts are re-run; successes are kept."""
    json.dump(_make_contracts(3), open(tmp_path / "cuad_sample.json", "w"))
    existing = [_record("C1", "M"), _record("C2", "M", error="old fail")]
    json.dump(existing, open(tmp_path / "abstractive_results.json", "w"))

    calls = []

    def fake(model, contracts, **kw):
        calls.append([c["contract_id"] for c in contracts])
        return [_record(c["contract_id"], model) for c in contracts]

    monkeypatch.setattr(rb, "run_single_model_on_contracts", fake)

    rb.run_abstractive_benchmark(
        sample_size=3, output_dir=str(tmp_path), models=["M"],
        batch_size=1, max_concurrency=1, batch_delay=0,
    )

    res = json.load(open(tmp_path / "abstractive_results.json", encoding="utf-8"))
    assert calls == [["C0", "C2"]]
    assert sorted(r["contract_id"] for r in res) == ["C0", "C1", "C2"]
    assert all(r["error"] is None for r in res)


def test_resume_skips_when_all_done(tmp_path, monkeypatch):
    """A fully-complete model is skipped without calling the provider."""
    json.dump(_make_contracts(2), open(tmp_path / "cuad_sample.json", "w"))
    existing = [_record("C0", "M"), _record("C1", "M")]
    json.dump(existing, open(tmp_path / "abstractive_results.json", "w"))

    calls = []

    def fake(model, contracts, **kw):
        calls.append(model)
        return []

    monkeypatch.setattr(rb, "run_single_model_on_contracts", fake)

    rb.run_abstractive_benchmark(
        sample_size=2, output_dir=str(tmp_path), models=["M"],
        batch_size=1, max_concurrency=1, batch_delay=0,
    )

    assert calls == []
    res = json.load(open(tmp_path / "abstractive_results.json", encoding="utf-8"))
    assert len(res) == 2