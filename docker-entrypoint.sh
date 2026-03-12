#!/bin/bash
set -e

echo "🔍 Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be ready
while ! nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "✅ PostgreSQL is up - continuing..."

# Change to Django application directory
cd /app/app

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Apply database migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput

# Create a superuser if environment variables are set
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "👤 Creating superuser..."

    # Detect primary field of user for login (username or email)
    python manage.py shell << 'END'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

# Try detecting if the User model uses "username" or "email" as the unique login field
if hasattr(User, 'USERNAME_FIELD'):
    login_field = User.USERNAME_FIELD
else:
    login_field = 'username'

exists_kwarg = {login_field: username if login_field != 'email' else email}
if not User.objects.filter(**exists_kwarg).exists():
    try:
        if login_field == 'email':
            # user model logs in with email (common in custom user models)
            User.objects.create_superuser(email, email, password)
        else:
            # user model logs in with username
            User.objects.create_superuser(username, email, password)
        print('✅ Superuser created successfully')
    except Exception as e:
        print(f'❌ Failed to create superuser: {e}')
else:
    print('ℹ️  Superuser already exists')
END
fi

echo "🚀 Starting application..."

# Execute the CMD passed to the container
exec "$@"
