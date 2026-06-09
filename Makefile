# HR-Pro Makefile
# Common commands for development and deployment

.PHONY: help dev prod build up down logs shell migrate test backup restore clean

# Default target
help:
	@echo "HR-Pro Management Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start development server (local)"
	@echo "  make dev-docker - Start development with Docker"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make migrate    - Run migrations"
	@echo "  make shell      - Open Django shell"
	@echo ""
	@echo "Production:"
	@echo "  make prod       - Start production containers"
	@echo "  make deploy     - Full deployment"
	@echo "  make backup     - Backup database"
	@echo "  make restore    - Restore database"
	@echo "  make logs       - View container logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make superuser  - Create superuser"
	@echo "  make init-data  - Initialize default data"

# ===========================================
# DEVELOPMENT
# ===========================================

dev:
	python manage.py runserver --settings=config.settings.local

dev-docker:
	docker-compose up -d
	docker-compose logs -f web

test:
	python manage.py test --settings=config.settings.local

lint:
	ruff check apps/
	ruff format --check apps/

format:
	ruff format apps/
	ruff check --fix apps/

migrate:
	python manage.py migrate --settings=config.settings.local

makemigrations:
	python manage.py makemigrations --settings=config.settings.local

shell:
	python manage.py shell --settings=config.settings.local

superuser:
	python manage.py createsuperuser --settings=config.settings.local

init-data:
	python manage.py init_hr_data --settings=config.settings.local
	python manage.py init_payroll_data --settings=config.settings.local

# ===========================================
# PRODUCTION
# ===========================================

prod:
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.prod.yml build --no-cache

prod-down:
	docker-compose -f docker-compose.prod.yml down

deploy:
	./scripts/deploy.sh production

backup:
	./scripts/backup.sh manual

backup-daily:
	./scripts/backup.sh daily

backup-weekly:
	./scripts/backup.sh weekly

restore:
	@echo "Usage: ./scripts/restore.sh <backup_file>"
	@ls -lh docker/postgres/backups/*.sql.gz 2>/dev/null || echo "No backups found"

logs:
	docker-compose -f docker-compose.prod.yml logs -f

logs-web:
	docker-compose -f docker-compose.prod.yml logs -f web

logs-nginx:
	docker-compose -f docker-compose.prod.yml logs -f nginx

# ===========================================
# UTILITIES
# ===========================================

clean:
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans
	docker-compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status:
	docker-compose -f docker-compose.prod.yml ps

collectstatic:
	docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

prod-shell:
	docker-compose -f docker-compose.prod.yml exec web python manage.py shell

prod-migrate:
	docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
