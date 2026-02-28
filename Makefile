dev:
    uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
    uv run ruff check src/ tests/

format:
    uv run ruff format src/ tests/

test:
    uv run pytest -v --tb=short

ingest:
    uv run python scripts/ingest.py

docker-up:
    docker compose up --build -d

docker-down:
    docker compose down