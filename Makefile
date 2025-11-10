.PHONY: setup demo fmt lint test

setup:
	bash infra/scripts/setup.sh

demo:
	bash infra/scripts/demo.sh

fmt:
	uv run black .
	uv run ruff check . --fix

lint:
	uv run ruff check .

test:
	uv run pytest -q
