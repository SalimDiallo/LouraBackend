# Utiliser une image Python officielle (3.12 car le projet semble être en 3.12)
FROM python:3.12-slim

# Empêcher Python de générer des fichiers .pyc et assurer que l'affichage est direct
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le dossier de travail principal dans le conteneur
WORKDIR /app

# Installer les dépendances système nécessaires pour les packages Python (Pillow, reportlab, PostgreSQL, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN addgroup --system django && adduser --system --group django

# Mettre à jour pip et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psycopg2-binary

# Copier le reste du code source
COPY --chown=django:django . .

# Créer les répertoires nécessaires pour les fichiers statiques et média avec les bonnes permissions
RUN mkdir -p /app/staticfiles /app/media /app/app/static /app/app/media && \
    chown -R django:django /app

# Copier le script d'entrée
COPY --chown=django:django docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Passer à l'utilisateur non-root
USER django

# Se déplacer dans le dossier contenant manage.py
WORKDIR /app/app

# Variables d'environnement Django (peuvent être surchargées au runtime)
ENV DJANGO_SETTINGS_MODULE=lourabackend.settings
ENV PORT=8000

# Exposer le port par défaut
EXPOSE 8000

# Utiliser le script d'entrée
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Commande par défaut: lancer Daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "lourabackend.asgi:application"]
