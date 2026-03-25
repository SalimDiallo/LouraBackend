.PHONY: help build up down restart logs shell migrate backup clean status

# Colors
GREEN  := \033[0;32m
YELLOW := \033[1;33m
NC     := \033[0m

help: ## Show this help message
	@echo "$(GREEN)Loura Backend - Available Commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Docker commands
build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up -d
	@echo "$(GREEN)✅ Services started$(NC)"
	@echo "Web: http://localhost:8000"

down: ## Stop all services
	docker compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: ## Restart all services
	docker compose restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

logs: ## View logs (all services)
	docker compose logs -f

logs-web: ## View web service logs
	docker compose logs -f web

logs-celery: ## View celery worker logs
	docker compose logs -f celery_worker

status: ## Show service status
	@echo "$(YELLOW)Container Status:$(NC)"
	@docker compose ps
	@echo ""
	@echo "$(YELLOW)Health Checks:$(NC)"
	@docker compose exec db pg_isready -U loura_user && echo "$(GREEN)✅ PostgreSQL$(NC)" || echo "$(RED)❌ PostgreSQL$(NC)"
	@docker compose exec redis redis-cli ping > /dev/null && echo "$(GREEN)✅ Redis$(NC)" || echo "$(RED)❌ Redis$(NC)"
	@docker compose exec web python manage.py check --quiet && echo "$(GREEN)✅ Django$(NC)" || echo "$(RED)❌ Django$(NC)"

# Django commands
shell: ## Open Django shell
	docker compose exec web python manage.py shell

shell-bash: ## Open bash in web container
	docker compose exec web bash

migrate: ## Run database migrations
	docker compose exec web python manage.py migrate

makemigrations: ## Create new migrations
	docker compose exec web python manage.py makemigrations

collectstatic: ## Collect static files
	docker compose exec web python manage.py collectstatic --noinput

createsuperuser: ## Create Django superuser
	docker compose exec web python manage.py createsuperuser

# Database commands
dbshell: ## Open database shell
	docker compose exec db psql -U loura_user -d loura_db

backup: ## Create backup (database + media)
	@bash scripts/backup.sh

restore-db: ## Restore database from backup (Usage: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify FILE=path/to/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	@cat $(FILE) | docker compose exec -T db psql -U loura_user -d loura_db
	@echo "$(GREEN)✅ Database restored$(NC)"

# Development commands
dev: up logs-web ## Start services and follow web logs

fresh: down build up ## Fresh deployment (rebuild everything)

update: ## Update deployment (pull, rebuild, restart)
	@git pull origin main || echo "$(YELLOW)Not a git repo$(NC)"
	@docker compose build
	@docker compose down
	@docker compose up -d
	@docker compose exec web python manage.py migrate
	@docker compose exec web python manage.py collectstatic --noinput
	@echo "$(GREEN)✅ Update completed$(NC)"

# Celery commands
celery-shell: ## Open celery worker shell
	docker compose exec celery_worker bash

celery-active: ## Show active celery tasks
	docker compose exec celery_worker celery -A lourabackend inspect active

celery-scheduled: ## Show scheduled celery tasks
	docker compose exec celery_beat celery -A lourabackend inspect scheduled

celery-restart: ## Restart celery services
	docker compose restart celery_worker celery_beat
	@echo "$(GREEN)✅ Celery services restarted$(NC)"

# Cleanup commands
clean: ## Remove containers (keeps volumes)
	docker compose down
	@echo "$(GREEN)✅ Containers removed$(NC)"

clean-all: ## Remove containers and volumes (WARNING: deletes data)
	@echo "$(RED)⚠️  This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "$(GREEN)✅ Containers and volumes removed$(NC)"; \
	fi

prune: ## Clean Docker system (unused images, containers, networks)
	docker system prune -f
	@echo "$(GREEN)✅ Docker system cleaned$(NC)"

# Testing commands
test: ## Run tests
	docker compose exec web python manage.py test

check: ## Run Django checks
	docker compose exec web python manage.py check

check-deploy: ## Run Django deployment checks
	docker compose exec web python manage.py check --deploy

# Quick setup
setup: ## Initial setup (copy .env, build, start, migrate)
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(YELLOW)⚠️  Please edit .env before continuing!$(NC)"; \
		read -p "Press Enter when ready..."; \
	fi
	@$(MAKE) build
	@$(MAKE) up
	@sleep 10
	@$(MAKE) migrate
	@echo "$(GREEN)✅ Setup completed!$(NC)"
	@echo "Web: http://localhost:8000"
