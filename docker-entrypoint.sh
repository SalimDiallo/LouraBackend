#!/bin/bash
set -e

echo "🔍 Waiting for PostgreSQL to be ready..."

# Attendre que PostgreSQL soit prêt
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
  echo "⏳ PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "✅ PostgreSQL is up - continuing..."

# Se déplacer dans le dossier de l'application Django
cd /app/app

# Collecter les fichiers statiques
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Appliquer les migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput

# Créer un superuser si les variables d'environnement sont définies
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "👤 Creating superuser..."
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('✅ Superuser created successfully')
else:
    print('ℹ️  Superuser already exists')
END
fi

echo "🚀 Starting application..."

# Exécuter la commande passée au conteneur
exec "$@"
