# ================================
# VK Comments Parser - Makefile
# ================================

# Use bash instead of sh for Poetry support
SHELL := /bin/bash

# Poetry command detection
POETRY := $(shell command -v poetry 2> /dev/null || echo "~/.local/share/pypoetry/venv/bin/poetry")

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
	$(POETRY) install --only=main

install-dev: ## Install development dependencies
	$(POETRY) install --with=dev
	$(POETRY) run pre-commit install

install-prod: ## Install production dependencies with gunicorn
	$(POETRY) install --only=main --with=production

update: ## Update all dependencies
	$(POETRY) update
	$(POETRY) show --outdated

# ================================
# Code Quality & Testing
# ================================

test: ## Run tests with coverage
	$(POETRY) run pytest --cov=app --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	$(POETRY) run pytest -x --ff

test-integration: ## Run integration tests
	$(POETRY) run pytest -m integration

lint: ## Run all linting tools
	$(POETRY) run ruff check app tests
	$(POETRY) run mypy app
	$(POETRY) run bandit -r app

lint-fix: ## Run linting with auto-fix
	$(POETRY) run ruff check --fix app tests
	$(POETRY) run ruff format app tests

format: ## Format code with black and ruff
	$(POETRY) run black app tests
	$(POETRY) run ruff format app tests
	$(POETRY) run isort app tests

pre-commit: ## Run pre-commit hooks
	$(POETRY) run pre-commit run --all-files

# ================================
# Development & Running
# ================================

dev: ## Run development server with auto-reload
	$(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Run production server
	$(POETRY) run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

run: dev ## Alias for dev

shell: ## Open Python shell with project context
	$(POETRY) run python

# ================================
# Celery Background Tasks
# ================================

celery-worker: ## Run Celery worker
	$(POETRY) run celery -A app.workers.celery_app worker --loglevel=info

celery-beat: ## Run Celery beat scheduler
	$(POETRY) run celery -A app.workers.celery_app beat --loglevel=info

celery-flower: ## Run Flower monitoring for Celery
	$(POETRY) run celery -A app.workers.celery_app flower --host=0.0.0.0 --port=5555

celery-monitor: ## Monitor Celery workers and tasks
	$(POETRY) run celery -A app.workers.celery_app events

celery-purge: ## Purge all Celery queues (WARNING: destroys pending tasks)
	$(POETRY) run celery -A app.workers.celery_app purge -f

celery-status: ## Show Celery worker status
	$(POETRY) run celery -A app.workers.celery_app status

# ================================
# Database Operations
# ================================

db-upgrade: ## Apply database migrations
	$(POETRY) run alembic upgrade head

db-downgrade: ## Downgrade database by one revision
	$(POETRY) run alembic downgrade -1

db-migration: ## Create new migration (usage: make db-migration MSG="description")
	$(POETRY) run alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (WARNING: destroys all data)
	$(POETRY) run alembic downgrade base
	$(POETRY) run alembic upgrade head

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

build: ## Build distribution packages
	$(POETRY) build

publish: ## Publish to PyPI (requires API token)
	$(POETRY) publish

# ================================
# Security & Maintenance
# ================================

security: ## Run security checks
	$(POETRY) run bandit -r app
	$(POETRY) run safety check

deps-check: ## Check for dependency vulnerabilities
	$(POETRY) run safety check

update-deps: ## Update and check dependencies
	$(POETRY) update
	$(POETRY) run safety check
	$(POETRY) show --outdated

# ================================
# Environment Setup
# ================================

setup: ## Initial project setup (run once)
	$(POETRY) install --with=dev,production
	$(POETRY) run pre-commit install
	cp .env.example .env
	@echo "✅ Project setup complete!"
	@echo "⚠️  Don't forget to configure your .env file"

setup-dev: ## Setup development environment
	$(POETRY) install --with=dev
	$(POETRY) run pre-commit install
	@echo "✅ Development environment ready!"

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
	$(POETRY) show --outdated
	@echo ""
	@echo "=== Git Status ==="
	git status --short
	@echo ""
	@echo "=== Virtual Environment ==="
	$(POETRY) env info

# ================================
# Backup & Migration
# ================================

requirements-export: ## Export requirements for legacy systems
	$(POETRY) export -f requirements.txt --output requirements.txt
	$(POETRY) export -f requirements.txt --with=dev --output requirements-dev.txt
	$(POETRY) export -f requirements.txt --with=production --output requirements-prod.txt

poetry-to-pip: requirements-export ## Convert Poetry to pip requirements 