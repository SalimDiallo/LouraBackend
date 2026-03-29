# RAPPORT ARCHITECTURAL COMPLET - Loura Backend

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Stack technique](#stack-technique)
3. [Architecture globale](#architecture-globale)
4. [Applications Django](#applications-django)
5. [Modèles de données](#modèles-de-données)
6. [Authentification et autorisation](#authentification-et-autorisation)
7. [Configuration Docker](#configuration-docker)
8. [Tâches asynchrones](#tâches-asynchrones)
9. [WebSockets et notifications](#websockets-et-notifications)
10. [Intégration IA](#intégration-ia)
11. [Points d'attention](#points-dattention)

---

## Vue d'ensemble

**Projet**: Loura - Système de gestion d'entreprise avec IA intégrée  
**Type**: Backend REST API + WebSockets (Django 5.2.8)  
**Déploiement**: Docker Compose avec PostgreSQL, Redis  
**Frontend**: Next.js (Vercel) - Multi-tenant SaaS  
**Architecture**: Multi-tenant avec organisations  

### Objectifs
- Gestion complète des RH (employés, congés, paie, présence)
- Gestion des stocks et ventes (inventaire, commandes, factures)
- Module de services modulables (location, travaux, voyage, etc.)
- Assistant IA intégré avec function calling (Claude prioritaire, OpenAI fallback)
- Notifications en temps réel via WebSockets
- Système de permissions granulaire

---

## Stack technique

### Framework et Core
| Composant | Version | Rôle |
|-----------|---------|------|
| Django | 5.2.8 | Framework web principal |
| Django REST Framework | 3.16.1 | REST API |
| Daphne | 4.1.0 | Serveur ASGI avec WebSocket |
| Django Channels | 4.0.0 | Support WebSocket |

### Base de données et Cache
| Composant | Version | Rôle |
|-----------|---------|------|
| PostgreSQL | 16-alpine | Base de données principale |
| Redis | 7-alpine | Cache, broker Celery, channel layer |
| Django ORM | Built-in | ORM abstraction |

### Tâches asynchrones
| Composant | Version | Rôle |
|-----------|---------|------|
| Celery | 5.6.2 | Worker asynchrone |
| Django-Celery-Beat | 2.8.1 | Scheduler périodique |
| Django-Celery-Results | 2.6.0 | Stockage des résultats |

### Authentification
| Composant | Version | Rôle |
|-----------|---------|------|
| djangorestframework-simplejwt | 5.5.1 | JWT tokens (access/refresh) |
| rest-framework-simplejwt | 5.5.1 | Token blacklist |

### IA et LLM
| Composant | Version | Rôle |
|-----------|---------|------|
| Anthropic | ≥0.34.0 | Claude API (prioritaire) |
| OpenAI | ≥1.40.0 | OpenAI API (fallback) |
| Google-GenAI | 1.56.0 | Google Gemini (optionnel) |
| Ollama | 0.6.1 | LLM local (optionnel) |

### Utilitaires et Librairies principales
| Composant | Utilisation |
|-----------|-------------|
| Pillow | 12.0.0 - Traitement images |
| ReportLab | 4.4.5 - Génération PDF |
| Django-Filter | 25.2 - Filtrage avancé |
| Pydantic | 2.12.5 - Validation données |
| CORS Headers | 4.9.0 - Support CORS |

---

## Architecture globale

### Schéma des services Docker

```
┌──────────────────────────────────────────────────┐
│          Docker Compose Network                  │
│          (loura_network - bridge)                │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ Web Service (Daphne ASGI)                │   │
│  │ - Port: 8000                             │   │
│  │ - Serveur: daphne -b 0.0.0.0 -p 8000    │   │
│  │ - Supporte: HTTP + WebSocket             │   │
│  └─────────────┬──────────────────────────┘   │
│               │                                │
│  ┌────────────▼──────────────────────────┐   │
│  │ PostgreSQL (loura_postgres)           │   │
│  │ - Port: 5432                          │   │
│  │ - DB: loura_db                        │   │
│  │ - Healthcheck: enabled                │   │
│  └──────────────────────────────────────┘   │
│               │                                │
│  ┌────────────▼──────────────────────────┐   │
│  │ Redis (loura_redis)                   │   │
│  │ - Port: 6379                          │   │
│  │ - Slots: [0] Celery broker            │   │
│  │         [1] Celery result backend     │   │
│  │         [2] Channel layer             │   │
│  │ - Persistance: RDB + AOF              │   │
│  └──────────────────────────────────────┘   │
│                                                  │
│  [Celery Worker & Beat - DÉSACTIVÉS en dev]   │
│   (mode synchrone: CELERY_TASK_ALWAYS_EAGER) │
│                                                  │
└──────────────────────────────────────────────────┘

Volumes persistants:
  - postgres_data
  - redis_data
  - static_volume
  - media_volume
```

### Flux requêtes HTTP

```
Client (Next.js) 
    ↓
JWT Token (Bearer header ou cookie)
    ↓
Nginx/Reverse Proxy (HTTPS/SSL)
    ↓
Daphne ASGI (0.0.0.0:8000)
    ↓
Permission Chain:
  Token → Authentication → Organization → Permission Check
```

---

## Applications Django

Loura possède **7 applications Django** principales:

### 1. **core** - Module principal
**Chemin**: `/app/core/`

**Modèles**:
- BaseUser (abstract parent)
- AdminUser (multi-table inheritance)
- Organization (tenant)
- OrganizationSettings
- Role, Permission
- Module, OrganizationModule

**ViewSets**: OrganizationViewSet, ModuleViewSet, etc.

**Endpoints**:
```
GET  /api/core/organizations/
POST /api/core/organizations/
GET  /api/core/modules/
```

---

### 2. **authentication** - Authentification unifiée
**Chemin**: `/app/authentication/`

**Views**: LoginView, RegisterAdminView, LogoutView, RefreshTokenView, CurrentUserView

**JWT Config**:
- Access token: 15 min
- Refresh token: 7 days
- HTTP-only cookies
- Token rotation & blacklist

**Endpoints**:
```
POST /api/auth/login/
POST /api/auth/register/
POST /api/auth/logout/
POST /api/auth/refresh/
GET  /api/auth/me/
```

---

### 3. **hr** - Gestion des RH
**Chemin**: `/app/hr/`

**Modèles**:
- Employee (inherits BaseUser)
- Department, Position
- Contract
- LeaveRequest
- Attendance
- Payroll

**ViewSets**: EmployeeViewSet, LeaveRequestViewSet, AttendanceViewSet, PayrollViewSet

**Endpoints**:
```
GET  /api/hr/employees/
POST /api/hr/leave-requests/
POST /api/hr/attendance/check-in/
GET  /api/hr/payroll/
```

---

### 4. **inventory** - Gestion des stocks et ventes
**Chemin**: `/app/inventory/`
**Taille**: 1622 lignes

**Modèles** (60+):
- Category, Warehouse, Supplier
- Product, Stock, Movement
- Order, OrderItem
- StockCount, StockCountItem
- Customer, Sale, SaleItem, Payment
- CreditSale, Alert
- ProformaInvoice, PurchaseOrder, DeliveryNote

**ViewSets** (19): ProductViewSet, SaleViewSet, OrderViewSet, etc.

**Tâches Celery**:
- check_credit_sale_deadlines()
- update_overdue_credit_sales()

**Génération PDF**: Factures, reçus, bons (ReportLab)

**Endpoints**:
```
GET  /api/inventory/products/
POST /api/inventory/sales/
GET  /api/inventory/credit-sales/
POST /api/inventory/orders/
GET  /api/inventory/stats/
```

---

### 5. **ai** - Assistant IA intégré
**Chemin**: `/app/ai/`

**Modèles**:
- Conversation
- Message
- AIToolExecution

**Configuration**:
- Multi-provider (Claude prioritaire, OpenAI fallback)
- Function calling natif
- Tools registry

**Outils disponibles**:
- HR tools (employees, leave, payroll)
- Inventory tools (products, sales, stock)

**Endpoints**:
```
GET  /api/ai/conversations/
POST /api/ai/conversations/{id}/message/
GET  /api/ai/tools/
```

---

### 6. **notifications** - Notifications temps réel
**Chemin**: `/app/notifications/`

**Modèles**:
- Notification (alert|system|user)
- NotificationPreference

**WebSocket**:
- Route: `ws://api/ws/notifications/`
- Auth: JWT token (query param)
- Groups: `notifications_{user_id}`

**Tâche Celery**:
- purge_old_notifications_task() - Lundi 2h UTC

**Endpoints**:
```
GET  /api/notifications/
POST /api/notifications/{id}/read/
GET  /api/notifications/preferences/
```

---

### 7. **services** - Module modulable
**Chemin**: `/app/services/`

**Modèles**:
- BusinessProfile (secteur)
- ServiceType
- ServiceField (champs dynamiques)
- ServiceStatus
- Service
- ServiceStatusHistory, ServiceActivity, ServiceComment
- ServiceTemplate

**Caractéristiques**:
- Services imbriqués
- Champs dynamiques configurables
- Workflow statuts personnalisable
- Templates pré-configurés

**Endpoints**:
```
GET  /api/services/
POST /api/services/
POST /api/services/{id}/change-status/
```

---

## Modèles de données - Synthèse

### Hiérarchie polymorphe
```
AbstractBaseUser (Django)
  ↓
BaseUser (core)
  ├─ AdminUser
  └─ Employee (hr)

ForeignKey(BaseUser) → référence both types
```

### Multi-tenancy
```
Chaque modèle métier a:
  organization: ForeignKey(Organization)

Isolation garantie par queryset filtering
```

### Timestamps
```
TimeStampedModel:
  created_at: DateTimeField(auto_now_add=True)
  updated_at: DateTimeField(auto_now=True)
```

**Total modèles**: 80+
**Total endpoints**: 150+

---

## Authentification et autorisation

### Chaîne JWT
```
1. Bearer header: Authorization: Bearer <token>
2. Cookie HTTP-only: access_token
3. Query param: ?token=... (WebSocket)
   ↓
4. MultiUserJWTAuthentication.get_user()
   - Décode & valide token
   - Retourne Employee OU AdminUser
   ↓
5. Permission check
   - IsAuthenticated
   - Custom permissions (Role + Permission)
```

### Système permissions
```
Permission (code, name, category)
  ↓
Role (groupes)
  ├─ permissions: ManyToMany
  ├─ organization: nullable
  └─ is_system_role: Boolean
  ↓
Employee
  ├─ assigned_role
  └─ custom_permissions (override)

Vérification:
  employee.has_permission('hr.view_employees')
```

### Middleware
- **JWTAuthCookieMiddleware**: Cookie → Header
- **TokenFromQueryParamMiddleware**: Query → Header

---

## Configuration Docker

### Services
```yaml
db:
  image: postgres:16-alpine
  volumes: postgres_data
  
redis:
  image: redis:7-alpine
  volumes: redis_data
  
web:
  build: Dockerfile
  command: daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application
  depends_on: [db, redis]
  ports: 127.0.0.1:8000:8000

# celery_worker, celery_beat: DÉSACTIVÉS
```

### Environment variables
```
DEBUG=False
SECRET_KEY=...
ALLOWED_HOSTS=...
DB_NAME=loura_db
DB_USER=loura_user
CHANNEL_LAYERS_HOST=redis://redis:6379/2
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
```

### Volumes
```
postgres_data, redis_data, static_volume, media_volume
```

---

## Tâches asynchrones

### Configuration
```python
CELERY_BROKER_URL = 'memory://'  # Dev mode
CELERY_TASK_ALWAYS_EAGER = True  # Sync execution

# Production:
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_TASK_ALWAYS_EAGER = False
```

### Schedule (Celery Beat)
```python
CELERY_BEAT_SCHEDULE = {
  'check-credit-sale-deadlines': {
    'task': 'inventory.tasks.check_credit_sale_deadlines',
    'schedule': crontab(hour=8, minute=0),
  },
  'update-overdue-credit-sales': {
    'schedule': crontab(hour=9, minute=0),
  },
  'purge-old-notifications': {
    'schedule': crontab(hour=2, minute=0, day_of_week=1),
  },
}
```

---

## WebSockets et notifications

### Django Channels
```python
ASGI_APPLICATION = "lourabackend.asgi.application"

ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(URLRouter(...))
})
```

### Consumer
```python
class NotificationConsumer(AsyncWebsocketConsumer):
  - route: ws://api/ws/notifications/
  - auth: JWT token (query param)
  - join: group notifications_{user_id}
```

### Channel Groups
```
notifications_{user_id} → Broadcast per user
```

---

## Intégration IA

### Multi-provider
```python
AIConfig:
  ├─ ANTHROPIC_API_KEY (prioritaire)
  └─ OPENAI_API_KEY (fallback)

Provider auto-détecté par clés disponibles
```

### LouraAIAgent
```python
class LouraAIAgent:
  - Function calling natif (Claude Tool Use / OpenAI Functions)
  - System prompt contextualisé
  - Tools registry dynamique
  - Error handling & retries
```

### Tools
```
HR:
  get_employees_list()
  get_leave_requests()
  create_employee()
  submit_leave_request()
  get_payroll_summary()

Inventory:
  get_products_list()
  get_stock_levels()
  get_sales_summary()
  create_sale()
  create_order()
```

---

## Points d'attention

### Sécurité
✓ JWT tokens (short-lived access, long-lived refresh)  
✓ HTTP-only cookies  
✓ CSRF protection (Lax SameSite)  
✓ Tenant isolation (organization filtering)  
✓ Role-based permissions  
⚠ .env file never committed (use .env.example)  
⚠ SECRET_KEY must be unique in production  

### Performance
✓ Database indexes sur organization, recipient, created_at  
✓ Pagination (10 items par défaut)  
✓ Select/prefetch_related utilisés  
⚠ Redis fallback à in-memory (channel layer)  
⚠ Celery en mode synchrone (production: worker séparé)  

### Limitations actuelles
⚠ Celery désactivé en Docker (mode sync)  
⚠ Tâches périodiques non exécutées en dev  
⚠ IA nécessite API keys valides  
⚠ Pas de rate limiting  
⚠ Pas d'APM/monitoring centralisé  

### À améliorer
- [ ] OpenAPI/Swagger documentation
- [ ] Coverage tests > 20%
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Sentry/Datadog integration
- [ ] Pre-commit hooks (black, flake8)
- [ ] Requirements.txt version pinning

---

## Résumé chiffres

| Métrique | Valeur |
|----------|--------|
| Applications Django | 7 |
| Modèles | 80+ |
| ViewSets | 30+ |
| Endpoints | 150+ |
| Tâches Celery | 3 |
| Dépendances | 96 |
| Lignes inventory | 1622 |

---

## Déploiement

### Local (sans Docker)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd app && python manage.py migrate
python manage.py runserver
```

### Docker
```bash
docker compose up -d
# Database: postgres:5432
# Redis: redis:6379
# API: http://localhost:8000
```

### Production
```bash
# Use Nginx/Caddy reverse proxy
# Enable HTTPS/SSL
# Configure backups
# Set up monitoring
```

---

**Version**: Django 5.2.8 | PostgreSQL 16 | Python 3.12  
**Rapport généré**: 2026-03-28  
**Projet**: Loura Stack Backend  
**Frontend**: Next.js on Vercel
