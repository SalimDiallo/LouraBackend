# Documentation Projet Loura Backend

Bienvenue dans la documentation complète du backend Loura - une plateforme ERP multi-tenant avec IA intégrée.

## Vue d'ensemble rapide

**Loura** est une plateforme backend Django sophistiquée offrant :
- Gestion multi-tenant (Organizations)
- Modules RH, Inventaire, Ventes
- Assistant IA intégré (Claude + OpenAI)
- APIs REST complètes (150+ endpoints)
- Notifications temps réel (WebSockets)
- Authentification JWT sécurisée

## Architecture

- **Framework** : Django 5.2.8 + Django REST Framework
- **Base de données** : PostgreSQL 16
- **Cache/Queue** : Redis 7
- **Async Tasks** : Celery + Beat
- **WebSocket** : Django Channels
- **Déploiement** : Docker Compose
- **IA** : Anthropic Claude + OpenAI

## Structure de la documentation

### 📋 Démarrage rapide
- [README principal](../README.md) - Installation et premiers pas
- [Déploiement Docker](../DOCKER_DEPLOYMENT.md) - Guide de déploiement complet
- [Index de documentation](../DOCUMENTATION_INDEX.md) - Navigation centrale

### 🏗️ Architecture
- [Architecture complète](./architecture/ARCHITECTURE_OVERVIEW.md) - Vue d'ensemble système
- [Modèles de données](./architecture/DATA_MODELS.md) - Tous les modèles Django
- [Stack technique](./architecture/TECH_STACK.md) - Technologies et versions
- [Sécurité](./architecture/SECURITY.md) - JWT, permissions, multi-tenant

### 📱 Applications Django

Le projet est organisé en 7 applications principales :

1. **[Core](./applications/CORE.md)** - Infrastructure centrale
   - Users, Organizations, Permissions
   - Multi-tenancy
   - 14 modèles de données

2. **[Authentication](./applications/AUTHENTICATION.md)** - Système d'authentification
   - JWT avec HttpOnly cookies
   - Login/Logout/Refresh
   - Sessions, tokens, password reset

3. **[HR (Ressources Humaines)](./applications/HR.md)** - Gestion RH
   - Employés, contrats, congés
   - Départements, postes
   - 20+ modèles de données

4. **[Inventory](./applications/INVENTORY.md)** - Gestion stocks & ventes
   - Produits, catégories, stocks
   - Ventes, commandes, clients
   - 30+ modèles de données
   - Application la plus volumineuse (1622 lignes)

5. **[AI (Intelligence Artificielle)](./applications/AI.md)** - Assistant IA
   - Conversations avec Claude/OpenAI
   - Contexts, prompts, templates
   - RAG (Retrieval Augmented Generation)
   - 8 modèles de données

6. **[Notifications](./applications/NOTIFICATIONS.md)** - Notifications temps réel
   - WebSocket (Django Channels)
   - Real-time updates
   - 3 modèles de données

7. **[Services](./applications/SERVICES.md)** - Module services modulable
   - Structure extensible
   - 6 modèles de données

### 📚 Guides pratiques
- [Guide API REST](./guides/API_GUIDE.md) - Utilisation des endpoints
- [Guide Celery](./guides/CELERY_GUIDE.md) - Tâches asynchrones
- [Guide WebSocket](./guides/WEBSOCKET_GUIDE.md) - Notifications temps réel
- [Guide Tests](./guides/TESTING_GUIDE.md) - Tests unitaires et intégration

### 🔧 Référence API
- [API Endpoints](./api/ENDPOINTS.md) - Liste complète des 150+ endpoints
- [Serializers](./api/SERIALIZERS.md) - Format de données
- [Permissions](./api/PERMISSIONS.md) - Système d'autorisation

## Statistiques du projet

```
Applications Django :        7
Modèles de données :        85+
ViewSets/Views :            45+
Endpoints API :            150+
Serializers :               60+
Lignes de code Python :  ~15,000
Dépendances :               96
Tests :                    ~20%
```

## Guide de lecture par profil

### 👨‍💻 Développeur Backend Django
1. [Architecture Overview](./architecture/ARCHITECTURE_OVERVIEW.md)
2. [Data Models](./architecture/DATA_MODELS.md)
3. Applications par priorité :
   - [Core](./applications/CORE.md) - Base du système
   - [Authentication](./applications/AUTHENTICATION.md) - Auth
   - [Inventory](./applications/INVENTORY.md) - Module principal
4. [API Guide](./guides/API_GUIDE.md)

### 🎨 Développeur Frontend
1. [API Endpoints](./api/ENDPOINTS.md) - Tous les endpoints
2. [Authentication](./applications/AUTHENTICATION.md) - JWT flow
3. [WebSocket Guide](./guides/WEBSOCKET_GUIDE.md) - Temps réel
4. [Serializers](./api/SERIALIZERS.md) - Format JSON

### 🚀 DevOps / Déploiement
1. [Docker Deployment](../DOCKER_DEPLOYMENT.md)
2. [Tech Stack](./architecture/TECH_STACK.md)
3. Variables d'environnement (.env)
4. [Celery Guide](./guides/CELERY_GUIDE.md)

### 📊 Chef de projet / Manager
1. [Executive Summary](../EXECUTIVE_SUMMARY.md)
2. [Project Statistics](../PROJECT_STATISTICS.md)
3. [Architecture Overview](./architecture/ARCHITECTURE_OVERVIEW.md)
4. Applications business :
   - [HR](./applications/HR.md)
   - [Inventory](./applications/INVENTORY.md)
   - [AI](./applications/AI.md)

### 🤖 Claude AI Assistant
1. Tout lire dans cet ordre :
   - [Architecture Overview](./architecture/ARCHITECTURE_OVERVIEW.md)
   - [Data Models](./architecture/DATA_MODELS.md)
   - Toutes les [Applications](./applications/)
2. Comprendre les patterns :
   - Multi-tenancy (Organization filtering)
   - JWT authentication flow
   - Permission system
   - Celery task patterns
3. Référencer pour le code :
   - [API Endpoints](./api/ENDPOINTS.md)
   - [Serializers](./api/SERIALIZERS.md)

## Commandes utiles

```bash
# Démarrer le projet
./deploy.sh

# Voir les logs
docker compose logs -f web

# Shell Django
docker compose exec web python manage.py shell

# Migrations
docker compose exec web python manage.py migrate

# Tests
docker compose exec web python manage.py test

# Créer superuser
docker compose exec web python manage.py createsuperuser
```

## Points d'attention

### ✅ Points forts
- Architecture multi-tenant solide
- IA intégrée sophistiquée
- API REST riche et cohérente
- Déploiement Docker production-ready
- Permissions granulaires
- Code bien structuré

### ⚠️ À améliorer
- Coverage tests faible (~20%)
- Celery désactivé en Docker
- Pas de Swagger/OpenAPI docs
- Pas de CI/CD configuré
- Monitoring à ajouter (Sentry)

## Support et contribution

Pour toute question ou contribution :
1. Consulter cette documentation
2. Vérifier [tasks/lessons.md](../tasks/lessons.md) pour leçons apprises
3. Consulter [tasks/todo.md](../tasks/todo.md) pour tâches en cours

## Mise à jour de la documentation

Cette documentation a été générée automatiquement le **2026-03-28**.

Pour la mettre à jour :
1. Modifier les fichiers sources dans `docs/`
2. Vérifier la cohérence avec le code source
3. Tester les exemples de code
4. Mettre à jour la date de génération

---

**Version** : 1.0
**Dernière mise à jour** : 2026-03-28
**Projet** : Loura Backend
**Stack** : Django 5.2.8 + DRF + PostgreSQL + Redis
