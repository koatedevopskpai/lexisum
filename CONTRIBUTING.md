# Contributing to LexiSum

Thanks for your interest! Here's how to contribute.

## Development setup

```bash
git clone https://github.com/<your-username>/lexisum.git
cd lexisum
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Optional (for benchmarks):

```bash
pip install -r requirements-benchmark.txt
```

## Running tests

```bash
pytest tests/ -v
```

Please add tests for any new behaviour. The suite runs without network calls,
so mock external providers (see `tests/test_pipeline.py` for the pattern).

## Code style

We use `black` and `isort` (configured in `pyproject.toml`):

```bash
black src/ tests/ benchmark/
isort src/ tests/ benchmark/
```

## Pull requests

1. Open an issue first for major changes so we can align on the approach.
2. Keep PRs focused — one logical change per PR.
3. Update `docs/ARCHITECTURE.md` (including a new ADR) for significant design decisions.
4. Ensure `pytest tests/ -v` passes.

## Reporting issues

Include your OS, Python version, the command you ran, and the full traceback.
