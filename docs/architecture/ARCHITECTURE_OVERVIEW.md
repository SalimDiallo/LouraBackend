# Architecture Overview - Loura Backend

## Table des matières
1. [Vue d'ensemble du système](#vue-densemble-du-système)
2. [Architecture multi-tenant](#architecture-multi-tenant)
3. [Pattern MVT Django](#pattern-mvt-django)
4. [Architecture REST API](#architecture-rest-api)
5. [Architecture temps réel](#architecture-temps-réel)
6. [Architecture asynchrone](#architecture-asynchrone)
7. [Diagramme de l'architecture](#diagramme-de-larchitecture)
8. [Flux de données principaux](#flux-de-données-principaux)
9. [Relations entre applications](#relations-entre-applications)

---

## Vue d'ensemble du système

Loura est une plateforme ERP modulaire **multi-tenant** construite avec Django 5.2.8. Le système est conçu pour gérer plusieurs organisations indépendantes avec isolation complète des données.

### Caractéristiques principales

- **Multi-tenant** : Une seule instance sert plusieurs organisations
- **Modulaire** : Activation/désactivation de modules par organisation
- **API-First** : Architecture REST complète avec Django REST Framework
- **Temps réel** : WebSocket pour notifications instantanées
- **Asynchrone** : Tâches en arrière-plan avec Celery
- **Sécurisé** : JWT avec cookies HttpOnly, permissions granulaires

### Stack technique

```
Backend Framework : Django 5.2.8
API Framework     : Django REST Framework 3.16.1
Database          : PostgreSQL 16 (SQLite en dev)
Cache/Queue       : Redis 7
Task Queue        : Celery 5.6.2
WebSocket         : Django Channels 4.0.0
Authentication    : JWT (djangorestframework-simplejwt 5.5.1)
```

---

## Architecture multi-tenant

### Principe

Chaque organisation (`Organization`) est un tenant isolé avec :
- Ses propres employés, départements, produits, etc.
- Ses propres modules activés/désactivés
- Ses propres paramètres et préférences
- Isolation totale des données au niveau de la base de données

### Modèle de données central

```
Organization (Tenant)
├── AdminUser (Propriétaire/Admin)
├── Employees (Utilisateurs)
├── Modules activés (OrganizationModule)
├── Départements, Postes
├── Produits, Stock, Ventes
└── Paramètres (OrganizationSettings)
```

**Voir** : `app/core/models.py` (lignes 266-305)

### Isolation des données

Tous les modèles métier ont une `ForeignKey` vers `Organization` :
```python
organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    related_name='employees'
)
```

Les ViewSets filtrent automatiquement par organisation via :
- Permissions personnalisées (`IsOrganizationMember`)
- Filtres QuerySet dans les vues
- Middleware JWT qui injecte l'organisation dans le contexte

**Voir** : `app/core/permissions.py` (lignes 234-273)

---

## Pattern MVT Django

Loura suit le pattern **Model-View-Template** de Django, adapté pour une architecture API-first :

### Model (Modèle)

Les modèles définissent la structure de données et la logique métier.

**Structure des applications** :
```
app/
├── core/          # Modèles de base (Organization, BaseUser, Permissions)
├── hr/            # Gestion RH (Employee, Contract, Leave, Payroll)
├── inventory/     # Gestion stock (Product, Sale, Order, Movement)
├── notifications/ # Notifications internes
├── ai/            # Assistant IA
└── authentication/# Authentification unifiée
```

**Voir** : Chaque `app/*/models.py`

### View (Vue)

Les vues sont des **API ViewSets** (REST Framework) :
```python
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, BaseCRUDPermission]
```

**Voir** : `app/hr/views.py`, `app/inventory/views.py`

### Template (Serializer)

Au lieu de templates HTML, on utilise des **Serializers** pour la représentation JSON :
```python
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
```

**Voir** : `app/hr/serializers.py`, `app/inventory/serializers.py`

---

## Architecture REST API

### Principes

- **RESTful** : Ressources avec verbes HTTP (GET, POST, PUT, PATCH, DELETE)
- **Pagination** : 10 résultats par page par défaut
- **Filtrage** : django-filter pour filtres avancés
- **Permissions** : Système de permissions granulaires
- **Versioning** : Prêt pour versioning API (non implémenté actuellement)

### Structure des endpoints

```
/api/auth/         # Authentification (login, register, refresh)
/api/core/         # Organisation, Modules, Rôles
/api/hr/           # Employés, Congés, Paie, Pointage
/api/inventory/    # Produits, Ventes, Commandes, Stock
/api/notifications/# Notifications
/api/ai/           # Assistant IA
```

**Voir** : `app/lourabackend/urls.py` pour le routing principal

### Format des réponses

#### Succès (200, 201)
```json
{
  "id": "uuid",
  "name": "Product Name",
  "price": 1000.00,
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

#### Liste paginée
```json
{
  "count": 100,
  "next": "http://api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

#### Erreur (400, 403, 404)
```json
{
  "detail": "Message d'erreur",
  "error": "Description détaillée"
}
```

### Authentification

Le système utilise **JWT avec cookies HttpOnly** :

1. **Login** → JWT access (15 min) + refresh (7 jours)
2. **Cookies HttpOnly** : Sécurisé contre XSS
3. **Refresh automatique** : Avant expiration du token
4. **Blacklist** : Tokens révoqués au logout

**Flow JWT complet** : Voir `app/authentication/views.py` (lignes 38-80)

**Configuration JWT** : Voir `app/lourabackend/settings.py` (lignes 341-380)

---

## Architecture temps réel

### Django Channels (WebSocket)

Le système utilise **Django Channels 4.0.0** pour les communications temps réel.

### Cas d'usage actuel

**Notifications en temps réel** :
- Alertes de stock bas
- Notifications RH (congés, paie)
- Notifications de ventes à crédit
- Messages système

### Architecture WebSocket

```
Client (JavaScript)
    ↓ WebSocket Connection
    ws://localhost:8000/ws/notifications/?token=JWT&organization=SLUG
    ↓
NotificationConsumer (Channels)
    ↓
Channel Layer (Redis)
    ↓
Broadcast to all connected clients
```

**Voir** : `app/notifications/consumers.py`

### Consumer WebSocket

```python
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authentification via JWT dans query params
        # Vérification organisation
        # Rejoindre le groupe de notifications

    async def notification_message(self, event):
        # Envoyer notification au client
```

**Authentification WebSocket** : Voir lignes 22-66 dans `app/notifications/consumers.py`

### Configuration

```python
# Redis comme backend Channel Layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://localhost:6379/2"],
        },
    },
}
```

**Voir** : `app/lourabackend/settings.py` (lignes 386-394)

### Exemple client (JavaScript)

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/notifications/?token=${jwt_token}&organization=${org_slug}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'notification') {
    // Afficher la notification
  }
};
```

---

## Architecture asynchrone

### Celery (Task Queue)

Le système utilise **Celery 5.6.2** pour les tâches en arrière-plan.

### Tâches périodiques (Celery Beat)

#### 1. Vérification des échéances de crédit
```python
@shared_task
def check_credit_sale_deadlines():
    # Exécution : Tous les jours à 8h00 UTC
    # Notifications : 7, 3, 1 jours avant échéance
```

#### 2. Mise à jour des statuts overdue
```python
@shared_task
def update_overdue_credit_sales():
    # Exécution : Tous les jours à 9h00 UTC
    # Met à jour le statut des créances en retard
```

#### 3. Purge des notifications
```python
@shared_task
def purge_old_notifications_task(days=30):
    # Exécution : Tous les lundis à 2h00
    # Supprime les notifications lues de plus de 30 jours
```

**Voir** : `app/inventory/tasks.py`, `app/notifications/tasks.py`

### Configuration Celery

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
```

**Voir** : `app/lourabackend/settings.py` (lignes 132-175)

### Lancer Celery

```bash
# Worker + Beat (dev)
celery -A lourabackend worker --beat -l info

# Production (séparé)
celery -A lourabackend worker -l info
celery -A lourabackend beat -l info
```

**Voir** : `app/lourabackend/celery.py`

---

## Diagramme de l'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  (React/Next.js Frontend via Vercel)                           │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTP/S (REST API) + WebSocket
             │
┌────────────▼────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Django 5.2.8 (ASGI + WSGI)                                │ │
│  │  ├─ REST API (DRF 3.16.1)                                  │ │
│  │  ├─ WebSocket (Channels 4.0.0)                             │ │
│  │  └─ Authentication (JWT + Cookies HttpOnly)                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐ │
│  │   Core    │  │    HR    │  │ Inventory │  │ Notifications│ │
│  │ (Models,  │  │(Employee,│  │ (Product, │  │  (Alerts,    │ │
│  │  Perms)   │  │  Leave,  │  │   Sale,   │  │  Messages)   │ │
│  │           │  │  Payroll)│  │  Order)   │  │              │ │
│  └───────────┘  └──────────┘  └───────────┘  └──────────────┘ │
└────────────┬────────────────────────────────────────────────────┘
             │
             │
┌────────────▼────────────────────────────────────────────────────┐
│                     MIDDLEWARE LAYER                            │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐│
│  │  Celery 5.6.2        │  │  Redis 7                         ││
│  │  (Task Queue)        │  │  ├─ Cache                        ││
│  │  ├─ Worker           │  │  ├─ Channel Layer (WebSocket)   ││
│  │  └─ Beat (Scheduler) │  │  └─ Broker (Celery)             ││
│  └──────────────────────┘  └──────────────────────────────────┘│
└────────────┬────────────────────────────────────────────────────┘
             │
             │
┌────────────▼────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL 16 (Production) / SQLite (Dev)                 │ │
│  │  ├─ Organizations (Multi-tenant)                           │ │
│  │  ├─ Users (BaseUser → AdminUser / Employee)               │ │
│  │  ├─ HR (55+ tables)                                        │ │
│  │  ├─ Inventory (40+ tables)                                 │ │
│  │  └─ Notifications                                           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flux de données principaux

### 1. Flux d'authentification (JWT)

```
┌─────────┐                                    ┌─────────────────┐
│ Client  │                                    │  Django Backend │
└────┬────┘                                    └────────┬────────┘
     │                                                  │
     │  POST /api/auth/login/                          │
     │  { email, password }                            │
     │ ────────────────────────────────────────────────>│
     │                                                  │
     │                          ┌─ Vérification user   │
     │                          ├─ Génération JWT      │
     │                          └─ Set HttpOnly cookies│
     │                                                  │
     │  200 OK + Cookies (access_token, refresh_token) │
     │  { user, user_type, access, refresh }           │
     │<─────────────────────────────────────────────────│
     │                                                  │
     │  Requêtes suivantes avec Cookie automatique     │
     │  (ou Authorization: Bearer <token>)             │
     │ ────────────────────────────────────────────────>│
     │                                                  │
     │  ┌─ JWT Middleware extrait token                │
     │  ├─ Authentification user                       │
     │  └─ Vérification permissions                    │
     │                                                  │
     │  Response (données filtrées par organization)   │
     │<─────────────────────────────────────────────────│
     │                                                  │
```

**Voir** : `app/authentication/views.py` (LoginView, lignes 38-79)

### 2. Flux de création de vente

```
┌─────────┐                                    ┌─────────────────┐
│ Client  │                                    │  Django Backend │
└────┬────┘                                    └────────┬────────┘
     │                                                  │
     │  POST /api/inventory/sales/                     │
     │  { customer, items, warehouse, ... }            │
     │ ────────────────────────────────────────────────>│
     │                                                  │
     │                          ┌─ Permissions check   │
     │                          ├─ Stock check         │
     │                          ├─ Create Sale         │
     │                          ├─ Create SaleItems    │
     │                          ├─ Update Stock (-)    │
     │                          ├─ Create Movement     │
     │                          └─ Send Notification   │
     │                                                  │
     │  201 Created { sale object }                    │
     │<─────────────────────────────────────────────────│
     │                                                  │
     │  WebSocket: notification_message                │
     │<═════════════════════════════════════════════════│
     │  (notification en temps réel)                   │
     │                                                  │
```

**Voir** : `app/inventory/views.py` (SaleViewSet)

### 3. Flux de notification temps réel

```
┌─────────┐        ┌──────────────┐        ┌──────────┐
│ Backend │        │ Redis Channel│        │  Client  │
│  (Task) │        │    Layer     │        │  (WS)    │
└────┬────┘        └──────┬───────┘        └────┬─────┘
     │                    │                     │
     │ send_notification()│                     │
     │ ──────────────────>│                     │
     │                    │                     │
     │                    │ group_send()        │
     │                    │ ───────────────────>│
     │                    │                     │
     │                    │   WebSocket Message │
     │                    │   {type, notification}
     │                    │ ───────────────────>│
     │                    │                     │
     │                    │                 Display
     │                    │                 Notification
```

**Voir** : `app/notifications/consumers.py` (NotificationConsumer)

### 4. Flux de tâche asynchrone (Celery)

```
┌─────────────┐          ┌────────┐          ┌─────────────┐
│   Client    │          │ Django │          │   Celery    │
│  (Request)  │          │  View  │          │   Worker    │
└──────┬──────┘          └───┬────┘          └──────┬──────┘
       │                     │                      │
       │  POST /api/action/  │                      │
       │ ───────────────────>│                      │
       │                     │                      │
       │                     │ task.delay()         │
       │                     │ ────────────────────>│
       │                     │                      │
       │  202 Accepted       │                      │
       │  {task_id}          │              Execute
       │<────────────────────│              Task
       │                     │              (async)
       │                     │                      │
       │                     │                 Update DB
       │                     │                 Send Notif
       │                     │                      │
```

**Voir** : `app/inventory/tasks.py`

---

## Relations entre applications

### Dépendances principales

```
core (Base)
 │
 ├─> authentication (Login/JWT)
 │   └─> core.models (BaseUser, Organization)
 │
 ├─> hr (Gestion RH)
 │   ├─> core.models (Organization, Role, Permission)
 │   └─> core.BaseUser (Employee hérite de BaseUser)
 │
 ├─> inventory (Gestion stock)
 │   ├─> core.models (Organization)
 │   └─> hr.models (Employee pour tracking)
 │
 ├─> notifications (Système de notifications)
 │   ├─> core.models (Organization, BaseUser)
 │   ├─> hr.models (notifications RH)
 │   └─> inventory.models (alertes stock)
 │
 └─> ai (Assistant IA)
     └─> core.models (Organization, BaseUser)
```

### Modèles polymorphes

**BaseUser** est le modèle parent pour tous les utilisateurs :

```
BaseUser (Abstract Parent)
 │
 ├─> AdminUser (Propriétaire d'organisations)
 │   └─ Has: organizations (Many-to-Many via ForeignKey)
 │
 └─> Employee (Utilisateur dans une organisation)
     └─ Has: organization (ForeignKey)
            department, position, contract
            assigned_role, custom_permissions
```

**Voir** : `app/core/models.py` (lignes 46-149)

### Isolation multi-tenant

Chaque modèle métier DOIT avoir :
```python
organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
```

Les QuerySets sont filtrés automatiquement via :
- Permissions (`IsOrganizationMember`)
- Filtres dans les ViewSets
- Middleware d'organisation

---

## Points d'entrée de l'application

### ASGI Application (WebSocket + HTTP)

```python
# app/lourabackend/asgi.py
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(notifications.routing.websocket_urlpatterns)
    ),
})
```

### WSGI Application (HTTP uniquement)

```python
# app/lourabackend/wsgi.py
application = get_wsgi_application()
```

### Celery Application

```python
# app/lourabackend/celery.py
app = Celery('loura')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

---

## Prochaines étapes d'architecture

### Évolutions prévues

1. **Microservices** : Extraction de services indépendants (AI, Reporting)
2. **GraphQL** : API GraphQL en complément de REST
3. **Elasticsearch** : Recherche avancée full-text
4. **S3** : Stockage des fichiers (logos, documents)
5. **API Gateway** : Nginx/Kong pour rate limiting et caching
6. **Monitoring** : Sentry, Prometheus, Grafana

### Scalabilité

- **Horizontal** : Ajouter des workers Celery et serveurs Django
- **Vertical** : Augmenter les ressources PostgreSQL et Redis
- **Database Sharding** : Partitionnement par organization_id
- **CDN** : Pour les assets statiques

---

## Références

- **Django Documentation** : https://docs.djangoproject.com/en/5.2/
- **DRF Documentation** : https://www.django-rest-framework.org/
- **Channels Documentation** : https://channels.readthedocs.io/
- **Celery Documentation** : https://docs.celeryproject.org/

---

**Dernière mise à jour** : 2025-01-15
**Version** : 1.0.0
