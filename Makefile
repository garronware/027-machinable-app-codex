.PHONY: setup dev test lint check eval-help

setup:
	uv sync
	cd src/frontend && npm ci

dev:
	@uv run uvicorn backend.main:app --reload & backend_pid=$$!; \
	trap 'kill $$backend_pid 2>/dev/null || true' EXIT INT TERM; \
	cd src/frontend && npm start

test:
	uv run pytest

lint:
	uv run ruff check src tests
	cd src/frontend && npm run lint
	cd src/frontend && npm run typecheck

check: lint test

eval-help:
	uv run python -m tests.evaluation.evaluate_vision --help
