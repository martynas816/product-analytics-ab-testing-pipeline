SHELL := /bin/bash

.PHONY: help demo up down reset logs psql

help:
	@echo "Targets:"
	@echo "  make demo   - one command demo: load events -> dbt build/tests -> monitoring -> AB decision"
	@echo "  make up     - start postgres (detached)"
	@echo "  make down   - stop containers"
	@echo "  make reset  - delete containers + volumes (fresh DB)"
	@echo "  make logs   - follow pipeline logs"
	@echo "  make psql   - open psql inside the postgres container"

demo:
	docker compose up --build --abort-on-container-exit pipeline
	@echo ""
	@echo "Outputs written to ./outputs:"
	@ls -1 outputs || true

up:
	docker compose up -d postgres

down:
	docker compose down

reset:
	docker compose down -v

logs:
	docker compose logs -f pipeline

psql:
	docker compose exec -it postgres psql -U analytics -d analytics


# Local quality checks (non-Docker)
lint:
	python -m ruff check .

format:
	python -m black .

format-check:
	python -m black --check .

typecheck:
	python -m mypy .

test:
	python -m pytest

quality: format-check lint typecheck test
