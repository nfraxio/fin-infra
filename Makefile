SHELL := /bin/bash
RMI ?= all

.PHONY: help accept compose_up wait seed down pytest_accept unit unitv clean clean-pycache test lint type format

DC_FILE := docker-compose.test.yml
COMPOSE := docker compose -f $(DC_FILE)

help: ## Show available commands
	@echo "Available commands:"
	@echo ""
	@echo "Testing:"
	@echo "  unit              Run unit tests (quiet)"
	@echo "  unitv             Run unit tests (verbose)"
	@echo "  accept            Run acceptance tests"
	@echo "  test              Run all tests (unit + acceptance)"
	@echo ""
	@echo "Code Quality:"
	@echo "  format            Format code with black and isort"
	@echo "  lint              Lint code with flake8 and ruff"
	@echo "  type              Type check with mypy"
	@echo ""
	@echo "Docker Compose:"
	@echo "  compose_up        Start test services (if COMPOSE_PROFILES set)"
	@echo "  down              Tear down test services"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean             Remove caches, build artifacts, logs"
	@echo "  clean-pycache     Remove only __pycache__ directories"
	@echo ""

# --- Acceptance ---
compose_up:
	@if [ -n "$$COMPOSE_PROFILES" ]; then \
		echo "[accept] Starting services with profiles=$$COMPOSE_PROFILES"; \
		$(COMPOSE) up -d --wait; \
	else \
		echo "[accept] No external services requested (set COMPOSE_PROFILES=redis to enable Redis)"; \
	fi

wait:
	@if [ -n "$$COMPOSE_PROFILES" ]; then \
		echo "[accept] Waiting for services (redis)"; \
		poetry run python scripts/wait_for.py 127.0.0.1 6379 20 || exit $$?; \
	else \
		echo "[accept] Nothing to wait for in library mode"; \
	fi

seed:
	@echo "[accept] No DB seed step — skipping seed"

pytest_accept:
	@echo "[accept] Running acceptance tests locally (marked with 'acceptance')"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[accept] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
	poetry run pytest -q -m acceptance

accept:
	@echo "[accept] Running acceptance (library mode)"
	@status=0; \
	$(MAKE) compose_up || status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) wait || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) seed || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) pytest_accept || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		echo "[accept] Acceptance complete"; \
	else \
		echo "[accept] Acceptance failed"; \
	fi; \
	exit $$status

down:
	@if [ -n "$$COMPOSE_PROFILES" ]; then \
		echo "[accept] Tearing down services"; \
		$(COMPOSE) down -v; \
	else \
		echo "[accept] Nothing to tear down"; \
	fi

# --- Unit tests ---
unit:
	@echo "[unit] Running unit tests (quiet)"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[unit] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
	poetry run pytest -q tests/unit

unitv:
	@echo "[unit] Running unit tests (verbose)"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[unit] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
	poetry run pytest -vv tests/unit

# --- Code Quality ---
format:
	@echo "[format] Formatting with black and isort"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[format] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only dev >/dev/null 2>&1 || true; \
	poetry run black . --line-length 100; \
	poetry run isort . --profile black --line-length 100

lint:
	@echo "[lint] Running flake8 and ruff"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[lint] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only dev >/dev/null 2>&1 || true; \
	poetry run flake8 --select=E,F; \
	poetry run ruff check .

type:
	@echo "[type] Running mypy"
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "[type] Poetry is not installed. Please install Poetry (https://python-poetry.org/docs/#installation)"; \
		exit 2; \
	fi; \
	poetry install --no-interaction --only dev >/dev/null 2>&1 || true; \
	poetry run mypy src

# --- Cleanup helpers ---
clean:
	@echo "[clean] Removing Python caches, build artifacts, and logs"
	rm -rf **/__pycache__ __pycache__ .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info *.log

clean-pycache:
	@echo "[clean] Removing all __pycache__ directories recursively"
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +

# --- Combined test target ---
test:
	@echo "[test] Running unit and acceptance tests"
	@status=0; \
	$(MAKE) unit || status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) accept || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		echo "[test] All tests passed"; \
	else \
		echo "[test] Tests failed"; \
	fi; \
	exit $$status
