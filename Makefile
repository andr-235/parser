# ================================
# VK Comments Parser - Makefile
# ================================

# Use bash instead of sh for uv support
SHELL := /bin/bash

# uv command detection
UV := $(shell command -v uv 2> /dev/null || echo "uv")

.PHONY: help install install-dev install-prod test lint format clean build run dev docker-build docker-run

# Default target
help: ## Show this help message
	@echo "VK Comments Parser - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ================================
# Installation & Dependencies
# ================================

install: ## Install production dependencies
	$(UV) sync --no-group dev

install-dev: ## Install development dependencies
	$(UV) sync --all-extras
	$(UV) run pre-commit install

install-prod: ## Install production dependencies with production extras
	$(UV) sync --no-group dev --extra production

update: ## Update all dependencies
	$(UV) lock --upgrade
	$(UV) sync --all-extras

# ================================
# Code Quality & Testing
# ================================

test: ## Run tests with coverage
	$(UV) run pytest --cov=app --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	$(UV) run pytest -x --ff

test-integration: ## Run integration tests
	$(UV) run pytest -m integration

lint: ## Run all linting tools
	$(UV) run ruff check app tests
	$(UV) run mypy app
	$(UV) run bandit -r app

lint-fix: ## Run linting with auto-fix
	$(UV) run ruff check --fix app tests
	$(UV) run ruff format app tests

format: ## Format code with black and ruff
	$(UV) run black app tests
	$(UV) run ruff format app tests
	$(UV) run isort app tests

pre-commit: ## Run pre-commit hooks
	$(UV) run pre-commit run --all-files

# ================================
# Development & Running
# ================================

dev: ## Run development server with auto-reload
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Run production server
	$(UV) run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

run: dev ## Alias for dev

shell: ## Open Python shell with project context
	$(UV) run python

# ================================
# Celery Background Tasks
# ================================

celery-worker: ## Run Celery worker
	$(UV) run celery -A app.workers.celery_app worker --loglevel=info

celery-beat: ## Run Celery beat scheduler
	$(UV) run celery -A app.workers.celery_app beat --loglevel=info

celery-flower: ## Run Flower monitoring for Celery
	$(UV) run celery -A app.workers.celery_app flower --host=0.0.0.0 --port=5555

celery-monitor: ## Monitor Celery workers and tasks
	$(UV) run celery -A app.workers.celery_app events

celery-purge: ## Purge all Celery queues (WARNING: destroys pending tasks)
	$(UV) run celery -A app.workers.celery_app purge -f

celery-status: ## Show Celery worker status
	$(UV) run celery -A app.workers.celery_app status

# ================================
# Database Operations
# ================================

db-upgrade: ## Apply database migrations
	$(UV) run alembic upgrade head

db-downgrade: ## Downgrade database by one revision
	$(UV) run alembic downgrade -1

db-migration: ## Create new migration (usage: make db-migration MSG="description")
	$(UV) run alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (WARNING: destroys all data)
	$(UV) run alembic downgrade base
	$(UV) run alembic upgrade head

# ================================
# Docker Operations
# ================================

docker-build: ## Build Docker image
	docker build -t vk-comments-parser .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env vk-comments-parser

docker-dev: ## Run Docker container in development mode
	docker-compose -f docker-compose.dev.yml up --build

docker-prod: ## Run Docker container in production mode
	docker-compose up --build -d

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-clean: ## Clean Docker containers and images
	docker-compose down -v
	docker system prune -f

# ================================
# Project Management
# ================================

clean: ## Clean cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf .venv/

build: ## Build distribution packages
	$(UV) build

# uv doesn't have built-in publish command, use twine
publish: ## Publish to PyPI (requires API token)
	$(UV) run twine upload dist/*

# ================================
# Security & Maintenance
# ================================

security: ## Run security checks
	$(UV) run bandit -r app
	$(UV) run safety check

deps-check: ## Check for dependency vulnerabilities
	$(UV) run safety check

update-deps: ## Update and check dependencies
	$(UV) lock --upgrade
	$(UV) sync --all-extras
	$(UV) run safety check

# ================================
# Environment Setup
# ================================

setup: ## Initial project setup (run once)
	$(UV) sync --all-extras
	$(UV) run pre-commit install
	cp .env.example .env
	@echo "✅ Project setup complete!"
	@echo "⚠️  Don't forget to configure your .env file"

setup-dev: ## Setup development environment
	$(UV) sync --all-extras
	$(UV) run pre-commit install
	@echo "✅ Development environment ready!"

# ================================
# UV-specific Commands
# ================================

uv-info: ## Show UV and virtual environment info
	$(UV) --version
	$(UV) python --version
	@echo "Virtual environment: $(UV) venv --python python3.11 --seed"

tree: ## Show dependency tree
	$(UV) tree

lock: ## Generate lock file
	$(UV) lock

sync: ## Sync dependencies from lock file
	$(UV) sync --all-extras

export-requirements: ## Export requirements.txt for Docker compatibility
	$(UV) export --format requirements-txt --output-file requirements.txt --all-extras

# ================================
# Utility Commands
# ================================

check: ## Run all checks (lint, test, security)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security

ci: ## Run CI pipeline locally
	$(MAKE) lint-fix
	$(MAKE) test
	$(MAKE) security

status: ## Show project status
	@echo "=== Poetry Status ==="
	$(UV) show --outdated
	@echo ""
	@echo "=== Git Status ==="
	git status --short
	@echo ""
	@echo "=== Virtual Environment ==="
	$(UV) env info

# ================================
# Backup & Migration
# ================================

requirements-export: ## Export requirements for legacy systems
	$(UV) export -f requirements.txt --output requirements.txt
	$(UV) export -f requirements.txt --with=dev --output requirements-dev.txt
	$(UV) export -f requirements.txt --with=production --output requirements-prod.txt

poetry-to-pip: requirements-export ## Convert Poetry to pip requirements
