# Loura Backend

Backend Django pour l'application Loura - Système de gestion d'entreprise avec IA intégrée.

## Stack Technique

- **Framework**: Django 5.2.8 + Django REST Framework
- **Serveur ASGI**: Daphne (support WebSocket)
- **Base de données**: PostgreSQL 16 (production) / SQLite (dev)
- **Cache & Broker**: Redis 7
- **Tâches asynchrones**: Celery + Celery Beat
- **WebSocket**: Django Channels
- **IA**: OpenAI GPT, Google Gemini, Ollama
- **Conteneurisation**: Docker + Docker Compose

## Démarrage Rapide

### Prérequis

- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### Installation en 2 minutes

```bash
# 1. Cloner le projet
cd /home/salim/Projets/loura/stack/backend

# 2. Lancer le script de déploiement
./deploy.sh

# Ou avec Make
make setup
```

L'application sera accessible sur : **http://localhost:8000**

## Commandes Principales

### Avec Makefile (recommandé)

```bash
make help          # Voir toutes les commandes disponibles
make up            # Démarrer les services
make down          # Arrêter les services
make logs          # Voir les logs
make status        # Vérifier l'état des services
make migrate       # Exécuter les migrations
make shell         # Ouvrir le shell Django
make backup        # Créer un backup
```

### Avec Docker Compose

```bash
docker compose up -d              # Démarrer
docker compose down               # Arrêter
docker compose logs -f web        # Logs
docker compose ps                 # Status
```

### Avec le script de déploiement

```bash
./deploy.sh                       # Menu interactif
```

## Configuration

### Variables d'environnement (.env)

Copier `.env.example` vers `.env` et configurer :

```bash
# Django
SECRET_KEY=votre-cle-secrete-tres-longue
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_NAME=loura_db
DB_USER=loura_user
DB_PASSWORD=votre-mot-de-passe

# OpenAI (optionnel)
OPENAI_API_KEY=sk-proj-your-key
```

Voir `.env.example` pour la configuration complète.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Docker Compose Stack              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐ │
│  │ Django  │  │  Celery  │  │  Celery   │ │
│  │  Web    │  │  Worker  │  │   Beat    │ │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘ │
│       │            │               │        │
│  ┌────▼────────────▼───────────────▼─────┐ │
│  │        PostgreSQL + Redis             │ │
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

## Modules

- **Core**: Utilisateurs, organisations, permissions
- **HR**: Gestion des employés et présences
- **Inventory**: Gestion des stocks et ventes
- **AI**: Assistant IA intégré
- **Authentication**: Système d'authentification JWT
- **Notifications**: Notifications en temps réel

## Scripts Utiles

### Backup automatique

```bash
./scripts/backup.sh              # Créer un backup
make backup                      # Avec Make
```

Les backups sont stockés dans `./backups/` avec rotation automatique (7 jours).

### Commandes rapides

```bash
./scripts/quick-commands.sh      # Afficher toutes les commandes utiles
```

## Développement

### Structure du projet

```
backend/
├── app/                        # Code Django
│   ├── lourabackend/          # Configuration principale
│   ├── core/                  # Module core
│   ├── hr/                    # Module RH
│   ├── inventory/             # Module inventaire
│   ├── ai/                    # Module IA
│   └── manage.py
├── docker-compose.yml         # Configuration Docker
├── Dockerfile                 # Image Docker
├── docker-entrypoint.sh       # Script de démarrage
├── deploy.sh                  # Script de déploiement
├── Makefile                   # Commandes Make
├── scripts/                   # Scripts utilitaires
├── .env.example              # Configuration exemple
└── requirements.txt          # Dépendances Python
```

### Développement local (sans Docker)

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer la base de données
cd app
python manage.py migrate

# Lancer le serveur de développement
python manage.py runserver
```

### Tests

```bash
make test                      # Avec Docker
python manage.py test          # Sans Docker
```

## Production

### Checklist de sécurité

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` unique et fort
- [ ] `ALLOWED_HOSTS` configuré
- [ ] PostgreSQL avec mot de passe fort
- [ ] HTTPS/SSL configuré
- [ ] Backups automatiques configurés
- [ ] Monitoring en place

### Reverse Proxy

Utiliser Nginx ou Caddy en production pour :

- HTTPS/SSL
- Servir les fichiers statiques
- Load balancing
- WebSocket proxy

Voir [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) pour plus de détails.

## Monitoring

### Vérifier la santé des services

```bash
make status                    # Avec Make
docker compose ps              # Status des conteneurs
```

### Logs

```bash
make logs                      # Tous les services
make logs-web                  # Service web uniquement
docker compose logs -f celery_worker  # Celery
```

### Métriques

```bash
docker stats                   # Utilisation CPU/RAM
```

## Troubleshooting

### Le service web ne démarre pas

```bash
docker compose logs web        # Voir les logs
docker compose restart web     # Redémarrer
```

### Erreur de connexion PostgreSQL

```bash
# Vérifier que PostgreSQL est prêt
docker compose exec db pg_isready -U loura_user
```

### Celery ne traite pas les tâches

```bash
docker compose logs celery_worker
docker compose restart celery_worker celery_beat
```

Voir [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) pour le guide complet.

## Documentation

- [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md) - Guide complet de déploiement Docker
- [scripts/quick-commands.sh](./scripts/quick-commands.sh) - Liste de commandes utiles

## Licence

Propriétaire - Loura

## Support

Pour des questions ou problèmes :

1. Consulter la documentation
2. Vérifier les logs : `make logs`
3. Vérifier le status : `make status`

---

**Dernière mise à jour**: 2026-03-25

On va utiliser Caddy + un hostname gratuit qui pointe sur ton IP: 72-60-92-105.sslip.io

# → backend final: **https://72-60-92-105.sslip.io**
