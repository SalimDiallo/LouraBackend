#!/bin/bash
# ========================================
# Quick Commands for Development
# ========================================
# Collection of useful one-liner commands

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Loura Backend - Quick Commands${NC}\n"

echo -e "${YELLOW}🐳 Docker Commands:${NC}"
echo "  docker compose up -d              # Start all services"
echo "  docker compose down               # Stop all services"
echo "  docker compose ps                 # Check status"
echo "  docker compose logs -f web        # View web logs"
echo "  docker compose restart web        # Restart web service"
echo ""

echo -e "${YELLOW}🗄️  Database Commands:${NC}"
echo "  docker compose exec web python manage.py migrate"
echo "  docker compose exec web python manage.py makemigrations"
echo "  docker compose exec web python manage.py dbshell"
echo "  docker compose exec db psql -U loura_user -d loura_db"
echo ""

echo -e "${YELLOW}👤 User Management:${NC}"
echo "  docker compose exec web python manage.py createsuperuser"
echo "  docker compose exec web python manage.py changepassword <username>"
echo ""

echo -e "${YELLOW}📦 Static & Media:${NC}"
echo "  docker compose exec web python manage.py collectstatic"
echo "  docker compose exec web python manage.py collectstatic --clear --noinput"
echo ""

echo -e "${YELLOW}🔧 Django Management:${NC}"
echo "  docker compose exec web python manage.py shell"
echo "  docker compose exec web python manage.py check"
echo "  docker compose exec web python manage.py check --deploy"
echo "  docker compose exec web python manage.py showmigrations"
echo ""

echo -e "${YELLOW}🔄 Celery Commands:${NC}"
echo "  docker compose logs -f celery_worker"
echo "  docker compose restart celery_worker celery_beat"
echo "  docker compose exec celery_worker celery -A lourabackend inspect active"
echo "  docker compose exec celery_worker celery -A lourabackend inspect scheduled"
echo ""

echo -e "${YELLOW}💾 Backup & Restore:${NC}"
echo "  # Backup database"
echo "  docker compose exec db pg_dump -U loura_user loura_db > backup.sql"
echo ""
echo "  # Restore database"
echo "  cat backup.sql | docker compose exec -T db psql -U loura_user -d loura_db"
echo ""

echo -e "${YELLOW}🔍 Debugging:${NC}"
echo "  docker compose exec web bash           # Enter web container"
echo "  docker compose exec db bash            # Enter database container"
echo "  docker stats                           # Resource usage"
echo "  docker compose logs --tail=100 web     # Last 100 log lines"
echo ""

echo -e "${YELLOW}🧹 Cleanup:${NC}"
echo "  docker compose down -v                 # Remove containers & volumes"
echo "  docker system prune -a                 # Clean unused Docker data"
echo ""
