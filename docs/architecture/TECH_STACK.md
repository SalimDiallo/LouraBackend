# Tech Stack - Loura Backend

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Stack Django](#stack-django)
3. [Base de données](#base-de-données)
4. [Cache et Queue](#cache-et-queue)
5. [Conteneurisation](#conteneurisation)
6. [Dépendances principales](#dépendances-principales)
7. [Dépendances IA](#dépendances-ia)
8. [Outils de développement](#outils-de-développement)

---

## Vue d'ensemble

Loura Backend est construit sur un stack Python/Django moderne avec PostgreSQL, Redis, et Celery pour les tâches asynchrones.

**Versions principales** :
- **Python** : 3.12+
- **Django** : 5.2.8
- **PostgreSQL** : 16
- **Redis** : 7
- **Node.js** : Non requis (backend only)

---

## Stack Django

### Framework principal

```python
Django==5.2.8
```

Django 5.2.8 est la version stable actuelle (LTS jusqu'en avril 2026).

**Raison du choix** :
- ✅ Batteries incluses (ORM, Admin, Auth, Migrations)
- ✅ Sécurité robuste (CSRF, XSS, SQL Injection)
- ✅ Communauté active et documentation exhaustive
- ✅ Scalabilité prouvée en production

**Configuration** : `app/lourabackend/settings.py`

---

### Django REST Framework

```python
djangorestframework==3.16.1
```

**Usage** :
- Sérialisation JSON
- ViewSets et Routers
- Permissions et authentification
- Pagination et filtrage
- Browsable API (développement)

**Configuration** :
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'lourabackend.authentication.MultiUserJWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'lourabackend.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 10,
}
```

**Voir** : `app/lourabackend/settings.py` (lignes 289-304)

---

### JWT Authentication

```python
djangorestframework-simplejwt==5.5.1
```

**Fonctionnalités** :
- Access token (15 minutes)
- Refresh token (7 jours)
- Token rotation automatique
- Blacklist après logout
- Cookies HttpOnly sécurisés

**Configuration JWT** :
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SAMESITE': 'Lax',
}
```

**Voir** : `app/lourabackend/settings.py` (lignes 341-380)

---

### Django Channels (WebSocket)

```python
channels==4.0.0
channels-redis==4.2.0
daphne==4.1.0
```

**Usage** :
- Notifications en temps réel
- WebSocket pour client connecté
- Channel Layer avec Redis comme backend

**Configuration ASGI** :
```python
ASGI_APPLICATION = "lourabackend.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": ["redis://localhost:6379/2"]},
    },
}
```

**Voir** : `app/lourabackend/settings.py` (lignes 384-394)

---

### Celery (Task Queue)

```python
celery==5.6.2
django-celery-beat==2.8.1
django-celery-results==2.6.0
```

**Usage** :
- Tâches asynchrones en arrière-plan
- Tâches périodiques (Celery Beat)
- Stockage des résultats dans PostgreSQL

**Configuration Celery** :
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
```

**Voir** : `app/lourabackend/celery.py`, `app/lourabackend/settings.py` (lignes 132-175)

---

### CORS et sécurité

```python
django-cors-headers==4.9.0
```

**Configuration CORS** :
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://frontend-loura.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True
```

**CSRF Protection** :
```python
CSRF_TRUSTED_ORIGINS = [
    'https://frontend-loura.vercel.app',
    'http://127.0.0.1:3000',
    'http://localhost:3000',
]
CSRF_COOKIE_HTTPONLY = False  # Pour SPAs
CSRF_COOKIE_SAMESITE = 'Lax'
```

**Voir** : `app/lourabackend/settings.py` (lignes 76-99, 306-337)

---

### Django Extensions

```python
django-extensions==4.1
django-filter==25.2
django-timezone-field==7.2.1
```

**django-extensions** :
- `shell_plus` : Shell amélioré avec imports automatiques
- `runserver_plus` : Serveur de développement amélioré
- `show_urls` : Liste toutes les URLs

**django-filter** :
- Filtrage avancé dans les API ViewSets
- Filtres par date, range, icontains, etc.

**django-timezone-field** :
- Champ timezone pour utilisateurs (Africa/Conakry, etc.)

---

## Base de données

### PostgreSQL 16 (Production)

```python
# requirements.txt (implicite via Django)
psycopg2-binary==2.9.9  # Driver PostgreSQL
```

**Configuration production** :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'loura_db'),
        'USER': os.getenv('DB_USER', 'loura_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connexions persistantes
    }
}
```

**Voir** : `app/lourabackend/settings.py` (lignes 215-229)

---

### SQLite (Développement)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Utilisé par défaut en développement local.

**Voir** : `app/lourabackend/settings.py` (lignes 231-237)

---

## Cache et Queue

### Redis 7

```python
redis==7.1.0
```

**Usages multiples** :
1. **Celery Broker** : `redis://localhost:6379/0`
2. **Channel Layer** : `redis://localhost:6379/2`
3. **Cache Django** (optionnel) : `redis://localhost:6379/1`

**Installation Redis** :
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Configuration** : Voir `app/lourabackend/settings.py` (lignes 132-138, 386-394)

---

## Conteneurisation

### Docker Compose

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine

  redis:
    image: redis:7-alpine

  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application

  celery:
    build: .
    command: celery -A lourabackend worker -l info

  celery-beat:
    build: .
    command: celery -A lourabackend beat -l info
```

**Voir** : `docker-compose.yml`

---

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "lourabackend.asgi:application"]
```

**Voir** : `Dockerfile`

---

## Dépendances principales

### Communication réseau

```python
requests==2.32.5           # HTTP client
urllib3==2.5.0             # HTTP library (dépendance de requests)
certifi==2025.11.12        # Certificats SSL
websockets==15.0.1         # Client WebSocket
httpx==0.28.1              # HTTP client async (pour OpenAI/Anthropic)
httpcore==1.0.9
h11==0.16.0
```

---

### Parsing et sérialisation

```python
ujson==5.11.0              # JSON ultra-rapide
cbor2==5.8.0               # CBOR encoding (Channels)
msgpack==1.1.2             # MessagePack (Celery)
```

---

### Date et temps

```python
python-dateutil==2.9.0.post0  # Parsing de dates
tzdata==2025.3                 # Timezones
tzlocal==5.3.1                 # Timezone locale
cron_descriptor==2.0.6         # Description crontab lisible
```

---

### Cryptographie et sécurité

```python
PyJWT==2.10.1              # JWT encoding/decoding
cryptography==46.0.4       # Cryptographie
pyOpenSSL==25.3.0          # SSL/TLS
```

---

### Génération de documents

```python
reportlab==4.4.5           # Génération PDF
pillow==12.0.0             # Traitement d'images
```

Usage : Génération de factures PDF, fiches de paie, reçus.

---

### Google APIs

```python
google-genai==1.56.0
google-ai-generativelanguage==0.6.15
google-api-core==2.28.1
google-api-python-client==2.187.0
google-auth==2.45.0
google-auth-httplib2==0.3.0
googleapis-common-protos==1.72.0
```

Usage : Intégration Google Gemini (AI Assistant).

---

### Autres

```python
python-dotenv==1.2.1       # Variables d'environnement (.env)
tqdm==4.67.1               # Barres de progression (scripts)
packaging==26.0            # Version parsing
distro==1.9.0              # Détection OS Linux
```

---

## Dépendances IA

### Anthropic (Claude)

```python
anthropic>=0.34.0
```

**Usage** :
- Assistant IA conversationnel
- Analyse de données métier
- Génération de rapports

**Configuration** :
```python
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

**Exemple d'utilisation** :
```python
from anthropic import Anthropic

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)
```

**Voir** : `app/ai/views.py`

---

### OpenAI (GPT)

```python
openai>=1.40.0
```

**Usage** :
- Alternative à Claude
- Modèles GPT-4, GPT-3.5
- Embeddings pour recherche sémantique (futur)

**Configuration** :
```python
# .env
OPENAI_API_KEY=sk-...
```

---

### Ollama (Local LLMs)

```python
ollama==0.6.1
```

**Usage** :
- LLMs locaux pour tests et développement
- Alternative gratuite sans API key
- Modèles : Llama 3, Mistral, etc.

**Installation Ollama** :
```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Lancer un modèle
ollama run llama3
```

**Configuration** :
```python
# .env
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Outils de développement

### Outils inclus (optionnels)

```bash
# Shell Django amélioré
python manage.py shell_plus

# Lister toutes les URLs
python manage.py show_urls

# Générer un diagramme de modèles
python manage.py graph_models -a -o models.png

# Serveur de développement amélioré
python manage.py runserver_plus
```

---

### Outils recommandés (non inclus)

**Debugging** :
```python
# requirements-dev.txt (à créer)
django-debug-toolbar==4.3.0
ipython==8.20.0
ipdb==0.13.13
```

**Testing** :
```python
pytest==7.4.4
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
```

**Linting** :
```python
black==24.2.0
flake8==7.0.0
isort==5.13.2
mypy==1.8.0
```

---

## Installation complète

### 1. Clone le projet

```bash
git clone https://github.com/your-org/loura-backend.git
cd loura-backend
```

---

### 2. Créer un environnement virtuel

```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

---

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

### 4. Configuration .env

```bash
cp .env.example .env
# Éditer .env avec vos configurations
```

**Variables essentielles** :
```bash
SECRET_KEY=django-secret-key-here
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3  # ou postgresql
CELERY_BROKER_URL=redis://localhost:6379/0
CHANNEL_LAYERS_BACKEND=channels_redis.core.RedisChannelLayer
```

---

### 5. Migrations

```bash
python app/manage.py migrate
```

---

### 6. Créer un superuser

```bash
python app/manage.py createsuperuser
```

---

### 7. Lancer le serveur

```bash
# HTTP + WebSocket (ASGI)
python app/manage.py runserver

# ou avec Daphne (production)
daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application
```

---

### 8. Lancer Celery (optionnel)

```bash
# Worker + Beat
celery -A lourabackend worker --beat -l info

# ou séparément
celery -A lourabackend worker -l info
celery -A lourabackend beat -l info
```

---

## Dépendances complètes (requirements.txt)

```txt
# Core Django
Django==5.2.8
djangorestframework==3.16.1
djangorestframework-simplejwt==5.5.1

# Extensions Django
django-cors-headers==4.9.0
django-extensions==4.1
django-filter==25.2
django-timezone-field==7.2.1

# Channels (WebSocket)
channels==4.0.0
channels-redis==4.2.0
daphne==4.1.0

# Celery (Task Queue)
celery==5.6.2
django-celery-beat==2.8.1
django_celery_results==2.6.0

# Redis
redis==7.1.0

# Database
# psycopg2-binary==2.9.9  # Décommenter pour PostgreSQL

# Auth & Security
PyJWT==2.10.1
cryptography==46.0.4
pyOpenSSL==25.3.0

# HTTP & Network
requests==2.32.5
urllib3==2.5.0
httpx==0.28.1
websockets==15.0.1

# AI/LLM
anthropic>=0.34.0
openai>=1.40.0
ollama==0.6.1

# Google APIs
google-genai==1.56.0
google-api-python-client==2.187.0

# Documents & Files
reportlab==4.4.5
pillow==12.0.0

# Utilities
python-dotenv==1.2.1
python-dateutil==2.9.0.post0
tqdm==4.67.1

# Autres dépendances (voir requirements.txt complet)
```

**Voir** : `/home/salim/Projets/loura/stack/backend/requirements.txt`

---

## Versions Python supportées

- **Python 3.12** ✅ (Recommandé)
- **Python 3.11** ✅
- **Python 3.10** ⚠️ (Minimum)
- **Python 3.9** ❌ (Non supporté par Django 5.2)

---

## Compatibilité OS

- **Linux** : ✅ Ubuntu 22.04+, Debian 11+
- **macOS** : ✅ macOS 12+
- **Windows** : ✅ Windows 10/11 (WSL2 recommandé)
- **Docker** : ✅ Toutes plateformes

---

## Références

- **Django** : https://docs.djangoproject.com/en/5.2/
- **DRF** : https://www.django-rest-framework.org/
- **Celery** : https://docs.celeryproject.org/
- **Channels** : https://channels.readthedocs.io/
- **Redis** : https://redis.io/docs/

---

**Dernière mise à jour** : 2025-01-15
**Version** : 1.0.0
