# ================================
# VK Comments Parser - Makefile
# ================================

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
	poetry install --only=main

install-dev: ## Install development dependencies
	poetry install --with=dev
	poetry run pre-commit install

install-prod: ## Install production dependencies with gunicorn
	poetry install --only=main --with=production

update: ## Update all dependencies
	poetry update
	poetry show --outdated

# ================================
# Code Quality & Testing
# ================================

test: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	poetry run pytest -x --ff

test-integration: ## Run integration tests
	poetry run pytest -m integration

lint: ## Run all linting tools
	poetry run ruff check app tests
	poetry run mypy app
	poetry run bandit -r app

lint-fix: ## Run linting with auto-fix
	poetry run ruff check --fix app tests
	poetry run ruff format app tests

format: ## Format code with black and ruff
	poetry run black app tests
	poetry run ruff format app tests
	poetry run isort app tests

pre-commit: ## Run pre-commit hooks
	poetry run pre-commit run --all-files

# ================================
# Development & Running
# ================================

dev: ## Run development server with auto-reload
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Run production server
	poetry run gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

run: dev ## Alias for dev

shell: ## Open Python shell with project context
	poetry run python

# ================================
# Database Operations
# ================================

db-upgrade: ## Apply database migrations
	poetry run alembic upgrade head

db-downgrade: ## Downgrade database by one revision
	poetry run alembic downgrade -1

db-migration: ## Create new migration (usage: make db-migration MSG="description")
	poetry run alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Reset database (WARNING: destroys all data)
	poetry run alembic downgrade base
	poetry run alembic upgrade head

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
	poetry build

publish: ## Publish to PyPI (requires API token)
	poetry publish

# ================================
# Security & Maintenance
# ================================

security: ## Run security checks
	poetry run bandit -r app
	poetry run safety check

deps-check: ## Check for dependency vulnerabilities
	poetry run safety check

update-deps: ## Update and check dependencies
	poetry update
	poetry run safety check
	poetry show --outdated

# ================================
# Environment Setup
# ================================

setup: ## Initial project setup (run once)
	poetry install --with=dev,production
	poetry run pre-commit install
	cp .env.example .env
	@echo "✅ Project setup complete!"
	@echo "⚠️  Don't forget to configure your .env file"

setup-dev: ## Setup development environment
	poetry install --with=dev
	poetry run pre-commit install
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
	poetry show --outdated
	@echo ""
	@echo "=== Git Status ==="
	git status --short
	@echo ""
	@echo "=== Virtual Environment ==="
	poetry env info

# ================================
# Backup & Migration
# ================================

requirements-export: ## Export requirements for legacy systems
	poetry export -f requirements.txt --output requirements.txt
	poetry export -f requirements.txt --with=dev --output requirements-dev.txt
	poetry export -f requirements.txt --with=production --output requirements-prod.txt

poetry-to-pip: requirements-export ## Convert Poetry to pip requirements 