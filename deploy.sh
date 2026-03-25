#!/bin/bash

# ========================================
# Loura Backend Deployment Script
# ========================================
# This script handles the complete deployment workflow

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"

    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"

    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        if [ -f ".env.example" ]; then
            print_info "Creating .env from .env.example..."
            cp .env.example .env
            print_warning "Please edit .env file with your configuration before continuing"
            read -p "Press Enter when ready to continue..."
        else
            print_error ".env.example not found. Cannot proceed."
            exit 1
        fi
    else
        print_success ".env file exists"
    fi
}

# Show deployment mode selection
select_mode() {
    print_header "Deployment Mode"
    echo "Select deployment mode:"
    echo "1) Fresh deployment (build & start)"
    echo "2) Update deployment (rebuild & restart)"
    echo "3) Start existing containers"
    echo "4) Stop containers"
    echo "5) View logs"
    echo "6) Run migrations only"
    echo "7) Create backup"
    echo "8) Cleanup (remove containers & volumes)"
    echo "9) Status check"
    echo "0) Exit"
    echo ""
    read -p "Enter your choice [0-9]: " DEPLOY_CHOICE
    echo ""
}

# Fresh deployment
fresh_deployment() {
    print_header "Fresh Deployment"

    print_info "Building Docker images..."
    docker compose build || {
        print_error "Failed to build images"
        exit 1
    }
    print_success "Images built successfully"

    print_info "Starting containers..."
    docker compose up -d || {
        print_error "Failed to start containers"
        exit 1
    }
    print_success "Containers started"

    print_info "Waiting for services to be ready..."
    sleep 10

    print_info "Checking container status..."
    docker compose ps

    print_success "Deployment completed!"
    print_info "Application is running at: http://localhost:8000"
}

# Update deployment
update_deployment() {
    print_header "Update Deployment"

    print_info "Pulling latest changes..."
    git pull origin main 2>/dev/null || print_warning "Not a git repository or no remote configured"

    print_info "Rebuilding Docker images..."
    docker compose build --no-cache || {
        print_error "Failed to rebuild images"
        exit 1
    }
    print_success "Images rebuilt"

    print_info "Stopping containers..."
    docker compose down

    print_info "Starting updated containers..."
    docker compose up -d || {
        print_error "Failed to start containers"
        exit 1
    }
    print_success "Containers restarted"

    print_info "Waiting for services..."
    sleep 10

    print_info "Running migrations..."
    docker compose exec web python manage.py migrate

    print_info "Collecting static files..."
    docker compose exec web python manage.py collectstatic --noinput

    print_success "Update completed!"
}

# Start containers
start_containers() {
    print_header "Starting Containers"
    docker compose up -d
    print_success "Containers started"
    docker compose ps
}

# Stop containers
stop_containers() {
    print_header "Stopping Containers"
    docker compose down
    print_success "Containers stopped"
}

# View logs
view_logs() {
    print_header "Container Logs"
    echo "Select service to view logs:"
    echo "1) All services"
    echo "2) Web (Django)"
    echo "3) Celery Worker"
    echo "4) Celery Beat"
    echo "5) PostgreSQL"
    echo "6) Redis"
    read -p "Enter your choice [1-6]: " log_choice

    case $log_choice in
        1) docker compose logs -f ;;
        2) docker compose logs -f web ;;
        3) docker compose logs -f celery_worker ;;
        4) docker compose logs -f celery_beat ;;
        5) docker compose logs -f db ;;
        6) docker compose logs -f redis ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Run migrations
run_migrations() {
    print_header "Running Migrations"
    docker compose exec web python manage.py migrate || {
        print_error "Failed to run migrations"
        exit 1
    }
    print_success "Migrations completed"
}

# Create backup
create_backup() {
    print_header "Creating Backup"

    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    print_info "Backing up database..."
    docker compose exec db pg_dump -U loura_user loura_db | gzip > "$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"
    print_success "Database backup created: $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

    print_info "Backing up media files..."
    docker run --rm -v backend_media_volume:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf "/backup/media_backup_$TIMESTAMP.tar.gz" -C /data . 2>/dev/null || print_warning "Media backup failed or no media files"

    print_success "Backup completed!"
    ls -lh "$BACKUP_DIR"
}

# Cleanup
cleanup() {
    print_header "Cleanup"
    print_warning "This will remove all containers and volumes (data will be lost!)"
    read -p "Are you sure? Type 'yes' to continue: " confirm

    if [ "$confirm" == "yes" ]; then
        print_info "Stopping and removing containers..."
        docker compose down -v
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Status check
status_check() {
    print_header "Status Check"

    print_info "Container Status:"
    docker compose ps

    echo ""
    print_info "Service Health:"

    # Check PostgreSQL
    if docker compose exec db pg_isready -U loura_user &>/dev/null; then
        print_success "PostgreSQL: Healthy"
    else
        print_error "PostgreSQL: Unhealthy"
    fi

    # Check Redis
    if docker compose exec redis redis-cli ping &>/dev/null; then
        print_success "Redis: Healthy"
    else
        print_error "Redis: Unhealthy"
    fi

    # Check Web
    if docker compose exec web python manage.py check &>/dev/null; then
        print_success "Django: Healthy"
    else
        print_error "Django: Unhealthy"
    fi

    echo ""
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Main menu
main_menu() {
    while true; do
        select_mode

        case $DEPLOY_CHOICE in
            1) fresh_deployment ;;
            2) update_deployment ;;
            3) start_containers ;;
            4) stop_containers ;;
            5) view_logs ;;
            6) run_migrations ;;
            7) create_backup ;;
            8) cleanup ;;
            9) status_check ;;
            0) print_info "Exiting..."; exit 0 ;;
            *) print_error "Invalid choice" ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
    done
}

# Script entry point
print_header "🚀 Loura Backend Deployment Manager"
check_prerequisites
main_menu
