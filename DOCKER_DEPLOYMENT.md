# Loura Backend - Docker Deployment Guide

Guide complet pour déployer l'application Django avec PostgreSQL, Redis, Celery et Channels en utilisant Docker Compose.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Django     │  │   Celery     │  │   Celery     │      │
│  │     Web      │  │    Worker    │  │     Beat     │      │
│  │  (Daphne)    │  │              │  │  (Scheduler) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │              PostgreSQL 16                          │    │
│  │           (Persistent Database)                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Redis 7                                 │   │
│  │   (Celery Broker + Channels WebSocket Layer)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services

1. **PostgreSQL** - Base de données principale
2. **Redis** - Broker Celery + Channel Layer pour WebSockets
3. **Django Web (Daphne)** - Serveur ASGI pour HTTP/WebSocket
4. **Celery Worker** - Traitement des tâches asynchrones
5. **Celery Beat** - Planificateur de tâches périodiques

## Prérequis

- Docker (>= 20.10)
- Docker Compose (>= 2.0)
- 2GB RAM minimum
- 5GB espace disque

## Scripts de Déploiement

Le projet inclut plusieurs scripts pour faciliter le déploiement :

### 1. Script de déploiement interactif (`deploy.sh`)

Menu interactif avec toutes les opérations courantes :

```bash
./deploy.sh
```

Options disponibles :
- Fresh deployment (construction et démarrage)
- Update deployment (mise à jour)
- Start/Stop containers
- View logs
- Run migrations
- Create backup
- Status check

### 2. Makefile (commandes rapides)

Pour les développeurs familiers avec Make :

```bash
make help          # Voir toutes les commandes
make setup         # Installation initiale complète
make up            # Démarrer les services
make down          # Arrêter les services
make logs          # Voir les logs
make migrate       # Exécuter les migrations
make backup        # Créer un backup
```

### 3. Scripts utilitaires (`scripts/`)

- `scripts/backup.sh` - Backup automatisé avec rotation
- `scripts/quick-commands.sh` - Liste de commandes utiles

## Installation Rapide

### Méthode 1 : Avec le script de déploiement (Recommandé)

```bash
cd /home/salim/Projets/loura/stack/backend

# Utiliser le script de déploiement interactif
./deploy.sh
```

Le script va :
1. Vérifier les prérequis (Docker, Docker Compose)
2. Créer le fichier .env si nécessaire
3. Vous guider à travers le déploiement

### Méthode 2 : Avec Makefile

```bash
cd /home/salim/Projets/loura/stack/backend

# Installation complète en une commande
make setup
```

### Méthode 3 : Manuel (étape par étape)

```bash
cd /home/salim/Projets/loura/stack/backend

# Copier le fichier d'exemple
cp .env.example .env

# Éditer les variables d'environnement
nano .env  # ou vim, code, etc.
```

### 2. Configurer les variables d'environnement

**Variables obligatoires à modifier dans `.env` :**

```bash
# Django
SECRET_KEY=your-super-secret-key-min-50-chars
DEBUG=False

# Base de données
DB_PASSWORD=your-strong-database-password

# OpenAI (si vous utilisez l'IA)
OPENAI_API_KEY=sk-proj-your-actual-openai-key

# Superuser (optionnel, recommandé pour premier déploiement)
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password
```

**Pour la production, modifier aussi :**

```bash
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### 3. Construire et démarrer les conteneurs

```bash
# Construction des images
docker compose build

# Démarrage de tous les services
docker compose up -d

# Vérifier les logs
docker compose logs -f
```

### 4. Vérifier le déploiement

```bash
# Statut des services
docker compose ps

# Logs du service web
docker compose logs web

# Vérifier PostgreSQL
docker compose exec db psql -U loura_user -d loura_db -c '\l'

# Vérifier Redis
docker compose exec redis redis-cli ping
```

L'application est maintenant accessible sur : `http://localhost:8000`

## Commandes Utiles

### Gestion des conteneurs

```bash
# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Redémarrer un service spécifique
docker compose restart web

# Voir les logs en temps réel
docker compose logs -f web

# Voir les logs de tous les services
docker compose logs -f
```

### Gestion de la base de données

```bash
# Appliquer les migrations
docker compose exec web python manage.py migrate

# Créer un superuser manuellement
docker compose exec web python manage.py createsuperuser

# Accéder à la console Django
docker compose exec web python manage.py shell

# Accéder au shell PostgreSQL
docker compose exec db psql -U loura_user -d loura_db

# Backup de la base de données
docker compose exec db pg_dump -U loura_user loura_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurer un backup
cat backup.sql | docker compose exec -T db psql -U loura_user -d loura_db
```

### Gestion des fichiers statiques

```bash
# Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput

# Nettoyer les anciens fichiers statiques
docker compose exec web python manage.py collectstatic --noinput --clear
```

### Celery (Tâches asynchrones)

```bash
# Voir les workers actifs
docker compose exec celery_worker celery -A lourabackend inspect active

# Voir les tâches planifiées (Beat)
docker compose exec celery_beat celery -A lourabackend inspect scheduled

# Redémarrer le worker après changement de code
docker compose restart celery_worker celery_beat
```

### Debugging

```bash
# Entrer dans le conteneur web
docker compose exec web bash

# Exécuter des commandes Django
docker compose exec web python manage.py <command>

# Voir l'utilisation des ressources
docker stats

# Voir les logs d'erreur uniquement
docker compose logs web | grep ERROR
```

## Mise à jour de l'application

```bash
# 1. Pull les derniers changements
git pull origin main

# 2. Reconstruire les images
docker compose build

# 3. Redémarrer les services
docker compose down
docker compose up -d

# 4. Appliquer les migrations
docker compose exec web python manage.py migrate

# 5. Collecter les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput
```

## Production

### Checklist de sécurité

- [ ] `DEBUG=False` dans `.env`
- [ ] `SECRET_KEY` unique et fort (50+ caractères)
- [ ] `DB_PASSWORD` fort
- [ ] `ALLOWED_HOSTS` configuré avec votre domaine
- [ ] `CSRF_TRUSTED_ORIGINS` et `CORS_ALLOWED_ORIGINS` configurés
- [ ] Certificat SSL/TLS configuré (HTTPS)
- [ ] Sauvegardes régulières de la base de données
- [ ] Monitoring des logs et métriques
- [ ] Firewall configuré (uniquement ports 80, 443 ouverts)

### Reverse Proxy (Nginx/Caddy)

Pour la production, il est recommandé d'utiliser un reverse proxy :

**Exemple avec Nginx :**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

### Volumes et Persistance

Les données persistantes sont stockées dans des volumes Docker :

- `postgres_data` - Données PostgreSQL
- `redis_data` - Données Redis (snapshots)
- `static_volume` - Fichiers statiques Django
- `media_volume` - Fichiers uploadés

**Backup des volumes :**

```bash
# Backup PostgreSQL
docker compose exec db pg_dump -U loura_user loura_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup media files
docker run --rm -v backend_media_volume:/data -v $(pwd):/backup alpine tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz -C /data .
```

## Troubleshooting

### Le service web ne démarre pas

```bash
# Vérifier les logs
docker compose logs web

# Vérifier que PostgreSQL est prêt
docker compose exec db pg_isready -U loura_user

# Reconstruire l'image
docker compose build --no-cache web
docker compose up -d web
```

### Erreur de connexion à PostgreSQL

```bash
# Vérifier que le service db est en cours d'exécution
docker compose ps db

# Vérifier les credentials
docker compose exec db psql -U loura_user -d loura_db

# Vérifier les variables d'environnement
docker compose exec web env | grep DB_
```

### Celery ne traite pas les tâches

```bash
# Vérifier que Redis fonctionne
docker compose exec redis redis-cli ping

# Vérifier les workers
docker compose logs celery_worker

# Redémarrer les workers
docker compose restart celery_worker celery_beat
```

### Permissions sur les fichiers media/static

```bash
# Corriger les permissions
docker compose exec web chown -R django:django /app/media /app/staticfiles
```

## Performance

### Optimisation PostgreSQL

Ajouter dans `docker-compose.yml` sous le service `db` :

```yaml
command:
  - "postgres"
  - "-c"
  - "max_connections=200"
  - "-c"
  - "shared_buffers=256MB"
  - "-c"
  - "effective_cache_size=1GB"
```

### Scaling Celery Workers

```bash
# Démarrer plusieurs workers
docker compose up -d --scale celery_worker=3
```

## Monitoring

### Health Checks

Les services incluent des health checks :

```bash
# Vérifier la santé des services
docker compose ps
```

### Logs centralisés

```bash
# Envoyer les logs vers un service externe (ex: Sentry, LogDNA)
# Configurer dans settings.py
```

## Support

Pour plus d'informations :
- Documentation Django : https://docs.djangoproject.com/
- Documentation Docker : https://docs.docker.com/
- Documentation Celery : https://docs.celeryproject.org/

---

**Dernière mise à jour :** 2026-03-25
