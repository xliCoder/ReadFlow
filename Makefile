.PHONY: test build lint format

build:
	cd readflow/api && pip install -e ".[dev]" --quiet

test:
	cd readflow/api && pytest

lint:
	cd readflow/api && black --check app && isort --check-only app

format:
	cd readflow/api && black app && isort app
