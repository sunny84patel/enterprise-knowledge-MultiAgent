# Makefile — shortcuts for common tasks

.PHONY: install dev stop docker-up docker-down test eval ingest help

help:
	@echo ""
	@echo "Enterprise Knowledge Agent — Commands"
	@echo "────────────────────────────────────────"
	@echo "  make install      Install Python dependencies"
	@echo "  make dev          Start FastAPI backend (hot reload)"
	@echo "  make stop         Kill dev server (process on port 8000)"
	@echo "  make docker-up    Start Qdrant + backend + frontend"
	@echo "  make docker-down  Stop all containers"
	@echo "  make test         Run pytest suite"
	@echo "  make eval         Run RAGAS evaluation"
	@echo "  make benchmark    Run before/after benchmark report"
	@echo "  make ingest FILE=path/to/doc.pdf   Ingest a document"
	@echo ""

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --reload-dir . --reload-exclude '.venv' --reload-exclude '__pycache__' --host 0.0.0.0 --port 8000

stop:
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@pkill -f "uvicorn main:app" 2>/dev/null || true
	@echo "✅ Stopped processes on port 8000 and uvicorn workers"

docker-up:
	docker compose -f deploy/docker-compose.yml up -d
	@echo "✅ Services up:"
	@echo "   Backend  → http://localhost:8000"
	@echo "   Frontend → http://localhost:3000"
	@echo "   Qdrant   → http://localhost:6333/dashboard"

docker-down:
	docker compose -f deploy/docker-compose.yml down

test:
	pytest tests/ -v --tb=short

eval:
	python eval/ragas_eval.py

benchmark:
	python eval/benchmark_report.py

ingest:
	@if [ -z "$(FILE)" ]; then echo "Usage: make ingest FILE=path/to/doc.pdf"; exit 1; fi
	@if [ ! -f "$(FILE)" ]; then echo "Error: file '$(FILE)' not found"; exit 1; fi
	curl -f -X POST http://localhost:8000/ingest \
	  -F "file=@$(FILE)" \
	  -H "accept: application/json" \
	  --connect-timeout 5 --max-time 120

lint:
	ruff check . --fix
	black .
