.PHONY: setup run test lint format gate export-csv

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

gate:
	python scripts/ci_eval_gate.py

export-csv:
	python scripts/export_artifacts_csv.py
