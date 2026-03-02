.PHONY: dev lint format test ingest mcp docker-up docker-down docker-ingest

dev:
	PYTHONPATH=. uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

test:
	uv run pytest -v --tb=short

ingest:
	PYTHONPATH=. uv run python scripts/ingest.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-ingest:
	docker compose exec app python scripts/ingest.py

mcp:
	PYTHONPATH=. uv run python src/mcp_server.py
