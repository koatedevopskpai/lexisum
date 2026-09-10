.PHONY: help install install-bench test lint format run docker benchmark benchmark-extractive benchmark-abstractive clean

help:
	@echo "LexiSum - available targets:"
	@echo "  install             Install runtime dependencies + spaCy model"
	@echo "  install-bench       Install benchmark dependencies"
	@echo "  test                Run the test suite"
	@echo "  run                 Run the Streamlit UI"
	@echo "  docker              Build and run via docker compose"
	@echo "  benchmark-all       Reproduce the full benchmark suite"
	@echo "  benchmark-extractive   Extractive benchmark only"
	@echo "  benchmark-abstractive  Abstractive benchmark + evaluation"
	@echo "  clean               Remove caches and generated artifacts"

install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

install-bench:
	pip install -r requirements-benchmark.txt

test:
	pytest tests/ -v

run:
	streamlit run app.py

docker:
	docker compose up --build

benchmark-all:
	python -m benchmark.reproduce_all

benchmark-extractive:
	python -m benchmark.run_benchmark

benchmark-abstractive:
	python -m benchmark.run_abstractive_benchmark && python -m benchmark.evaluate_abstractive

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf benchmark/results logs/*.log