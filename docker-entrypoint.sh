#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Loura Backend Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=0

    echo -e "${YELLOW}🔍 Waiting for ${service} to be ready...${NC}"

    while ! nc -z "$host" "$port"; do
        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}❌ ${service} is not available after ${max_attempts} attempts${NC}"
            exit 1
        fi
        echo -e "${YELLOW}⏳ ${service} is unavailable - attempt ${attempt}/${max_attempts}${NC}"
        sleep 2
    done

    echo -e "${GREEN}✅ ${service} is up and ready!${NC}"
}

# Wait for PostgreSQL
wait_for_service "${DB_HOST:-db}" "${DB_PORT:-5432}" "PostgreSQL"

# Wait for Redis if configured
if [ -n "$CELERY_BROKER_URL" ] && [[ "$CELERY_BROKER_URL" == redis* ]]; then
    REDIS_HOST=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://([^:]+):.*|\1|')
    REDIS_PORT=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://[^:]+:([0-9]+).*|\1|')
    wait_for_service "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

# Change to Django application directory
cd /app/app

# Collect static files
echo -e "${YELLOW}📦 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear || {
    echo -e "${RED}❌ Failed to collect static files${NC}"
    exit 1
}
echo -e "${GREEN}✅ Static files collected${NC}"

# Apply database migrations
echo -e "${YELLOW}🔄 Applying database migrations...${NC}"
python manage.py migrate --noinput || {
    echo -e "${RED}❌ Failed to apply migrations${NC}"
    exit 1
}
echo -e "${GREEN}✅ Migrations applied${NC}"

# Sync permissions
echo -e "${YELLOW}🔐 Syncing permissions...${NC}"
python manage.py sync_permissions || {
    echo -e "${YELLOW}⚠️  sync_permissions command not found or failed${NC}"
}

# Initialize modules
echo -e "${YELLOW}📦 Initializing modules...${NC}"
python manage.py initialize_modules || {
    echo -e "${YELLOW}⚠️  initialize_modules command not found or failed${NC}"
}

# Create sample categories
echo -e "${YELLOW}🗂️  Creating sample categories...${NC}"
python manage.py create_sample_categories --with-modules || {
    echo -e "${YELLOW}⚠️  create_sample_categories command not found or failed${NC}"
}

# Create a superuser if environment variables are set
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo -e "${YELLOW}👤 Creating superuser...${NC}"

    # Detect primary field of user for login (username or email)
    python manage.py shell << 'END'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

# Try detecting if the User model uses "username" or "email" as the unique login field
if hasattr(User, 'USERNAME_FIELD'):
    login_field = User.USERNAME_FIELD
else:
    login_field = 'username'

exists_kwarg = {login_field: email if login_field == 'email' else username}
if not User.objects.filter(**exists_kwarg).exists():
    try:
        if login_field == 'email':
            # user model logs in with email (common in custom user models)
            # Signature: create_superuser(email, password, **extra_fields)
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name=username.capitalize(),
                last_name='User'
            )
        else:
            # user model logs in with username
            # Signature: create_superuser(username, email, password, **extra_fields)
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
        print(f'✅ Superuser created successfully with {login_field}: {email if login_field == "email" else username}')
    except Exception as e:
        print(f'❌ Failed to create superuser: {e}')
        import traceback
        traceback.print_exc()
else:
    print(f'ℹ️  Superuser already exists with {login_field}: {email if login_field == "email" else username}')
END
    echo -e "${GREEN}✅ Superuser setup completed${NC}"
else
    echo -e "${YELLOW}ℹ️  Skipping superuser creation (credentials not provided)${NC}"
fi

# Verify Django setup
echo -e "${YELLOW}🔍 Verifying Django setup...${NC}"
python manage.py check --deploy 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Django deployment check found some warnings${NC}"
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Starting application...${NC}"
echo -e "${GREEN}========================================${NC}"

# Execute the CMD passed to the container
exec "$@"
