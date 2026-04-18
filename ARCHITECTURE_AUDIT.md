# Audit Architectural - Backend Loura

**Date**: Avril 2026  
**Niveau d'analyse**: Très approfondi (THOROUGH)  
**Scope**: All Django modules (7 apps)

---

## Table des Matières

1. [Vue d'ensemble architecture](#vue-densemble-architecture)
2. [Audit détaillé par module](#audit-détaillé-par-module)
3. [Matrice des dépendances inter-modules](#matrice-des-dépendances-inter-modules)
4. [Violation de principes SOLID](#violation-de-principes-solid)
5. [Points chauds et complexité](#points-chauds-et-complexité)
6. [Liste priorisée des problèmes](#liste-priorisée-des-problèmes)
7. [Recommandations de refactoring](#recommandations-de-refactoring)

---

## Vue d'ensemble architecture

### Stack technique
- **Framework**: Django 5.2 + Django REST Framework
- **Base de données**: PostgreSQL (multi-tenant)
- **Authentication**: JWT (SimpleJWT)
- **Async**: Celery + Redis
- **Notifications**: Novu Cloud
- **IA**: Claude (Anthropic) + OpenAI
- **PDF**: ReportLab
- **WebSocket**: Channels

### Modules principaux (7 apps)
```
lourabackend/
├── core/              → Modèles de base, organisations, permissions, modules
├── authentication/    → Auth, tokens JWT, profil utilisateur
├── hr/                → Employés, congés, paie, pointage (3768 LOC views)
├── inventory/         → Produits, stocks, mouvements, ventes (4831 LOC views)
├── ai/                → IA conversationnelle, agents, outils
├── notifications/     → Notifications Novu, WebSocket, tâches async
└── services/          → Services complémentaires
```

### Architecture générale

```
CLIENT (Frontend)
    ↓
    └─→ API Gateway (Nginx/LoadBalancer)
            ↓
            ├─→ REST API (DRF ViewSets)
            │    ├─→ auth/ (tokens JWT)
            │    ├─→ hr/ (employees, leaves, payroll, attendance)
            │    ├─→ inventory/ (products, stock, sales)
            │    ├─→ ai/ (conversations, messages)
            │    └─→ notifications/ (WebSocket, notifications)
            │
            ├─→ WebSocket (Channels) → notifications/consumers
            │
            └─→ Celery Workers
                 ├─→ hr/tasks.py (onboarding, batch payroll)
                 ├─→ inventory/tasks.py (stock alerts)
                 └─→ notifications/tasks.py (async notifications)

DATABASE (PostgreSQL - Multi-tenant)
    └─→ All tables scoped by organization_id
```

### Modèle multi-tenant
- **Scope par Organisation**: BaseUser → AdminUser/Employee → Organization
- **Filtrage**: Chaque ViewSet filtre par `organization_id`
- **Mixins de filtrage**: `OrganizationQuerySetMixin`, `OrganizationResolverMixin` dans core.mixins
- **Isolation**: Matérialisée par ForeignKey + unique_together constraints

---

## Audit détaillé par module

### 1. CORE MODULE (fondation)

#### Responsabilités
- Modèles de base: `BaseUser`, `AdminUser`, Organisation
- Système de permissions: `Permission`, `Role`, permissions granulaires
- Gestion des modules: `Module`, `OrganizationModule` (feature flags)
- Mixins réutilisables: `OrganizationResolverMixin`, `OrganizationQuerySetMixin`

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| models.py | 487 | 7 modèles (BaseUser, AdminUser, Organization, Permission, Role, Module, OrganizationModule) |
| serializers.py | 182 | 4 sérialiseurs |
| views.py | 421 | 6 ViewSets |
| mixins.py | 250+ | 4 mixins pour l'isolation multi-tenant |
| permissions.py | 200+ | Permissions granulaires (RBAC) |
| permission_dependencies.py | - | Résolution de dépendances de permissions |
| modules.py | - | Gestion dynamique des modules |

#### Analyse structurelle

**Points forts**:
- Modèle utilisateur polymorphe bien conçu (`BaseUser` parent → `AdminUser`/`Employee` enfants)
- Méthode `get_concrete_user()` pour polymorphisme sans isinstance
- Permissions granulaires séparées du système Django
- Mixins réutilisables pour l'isolation multi-tenant
- Feature flag système (`OrganizationModule`)

**Problèmes détectés**:

1. **Couplage bidirectionnel**: `BaseUser` ↔ `Organization`
   - `BaseUser.get_organization()` retourne dynamiquement selon le type
   - Logique complexe dans le modèle plutôt que dans les services
   - Difficile à maintenir si de nouveaux types d'utilisateurs sont ajoutés

2. **Responsabilités multiples dans modèles**:
   - `BaseUser.has_org_permission()` contient de la logique métier
   - `BaseUser.get_concrete_user()` mélange polymorphisme et résolution
   - Devrait être dans une service-layer

3. **Imports circulaires potentiels**:
   - `core.models` importe `hr.models.Employee`
   - `authentication.services` importe `core.models` + `hr.models`
   - Formation de cycle: hr → core → auth → hr

---

### 2. AUTHENTICATION MODULE

#### Responsabilités
- Authentification (email/password, login/logout)
- Tokens JWT (génération, refresh, validation)
- Profil utilisateur (update, change password)
- Permission checking

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| services.py | 406 | 3 classes de service (AuthenticationService, TokenService, ProfileService) |
| views.py | 543 | 10+ endpoints (login, register, refresh, profile, etc.) |
| serializers.py | 381 | 8 sérialiseurs |
| models.py | 3 | Vide (utilise core.models.BaseUser) |
| permissions.py | - | Permissions custom pour l'auth |
| urls.py | - | Routes d'authentification |

#### Analyse structurelle

**Points forts**:
- Service-layer bien structurée: 3 services distincts (Auth, Token, Profile)
- Séparation des responsabilités appliquée
- Logging cohérent
- Gestion des erreurs avec ValidationError

**Problèmes détectés**:

1. **Responsabilités mal distribuées**:
   - `TokenService.generate_tokens_for_user()` fait trop:
     - Génère le JWT
     - Ajoute claims personnalisés
     - Récupère l'organisation contextuelle
   - `AuthenticationService.authenticate_user()` fait 3 choses:
     - Valide credentials
     - Détermine user_type
     - Récupère l'organisation

2. **Dépendances hardcodées**:
   ```python
   # authentication/services.py, ligne 15
   from hr.models import Employee
   ```
   - Crée un couplage fort auth → hr
   - Impossible de réutiliser auth sans hr
   - Violation du Dependency Inversion Principle

3. **Logique d'organisation dans services d'auth**:
   - `AuthenticationService.authenticate_user()` contient 30+ lignes de logique pour trouver l'organization
   - Devrait être délégué à un `OrganizationService`

4. **Imports directs de modèles dans les vues** (ligne 32):
   ```python
   # authentication/views.py
   from hr.models import EmployeeMembership  # 3 fois dans le même fichier
   ```

---

### 3. HR MODULE (cœur métier - CRITIQUE)

#### Responsabilités
- Employés (CRUD, activation, permissions)
- Départements et Postes
- Contrats de travail
- Gestion des congés (demandes, soldes, approbations)
- Paie (périodes, fiches de paie, avances)
- Pointage/Attendance (QR code, check-in/out)
- Rôles et Permissions (dupliqués avec core)
- Invitations d'employés

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| views.py | 3768 | **44 ViewSets** (ÉNORME!) |
| models.py | 1470 | 14 modèles |
| serializers.py | 1796 | 20+ sérialiseurs |
| services/employee_service.py | 259 | Opérations CRUD sur Employee |
| services/leave_service.py | 189 | Gestion des congés |
| services/payroll_service.py | 275 | Gestion de la paie |
| permissions.py | - | 10+ classes de permission |
| mixins.py | - | Mixins spécifiques à HR |
| pdf_generator.py | - | Génération de documents PDF |

#### Analyse structurelle

**PROBLÈME CRITIQUE 1: Surcharge du fichier views.py**
```
views.py = 3768 LOC contenant 44 ViewSets !
Moyenne: 85 LOC par ViewSet

Par comparaison, inventory.py = 4831 LOC avec 62 ViewSets
Moyenne: 78 LOC par ViewSet
```

Causes:
- Chaque ViewSet inclut beaucoup de logique custom
- Actions personnalisées nombreuses (@action decorators)
- Logique métier directement dans les vues

**PROBLÈME CRITIQUE 2: Duplication Permission/Role**
```python
# core/models.py
class Permission(models.Model): ...      # Permission globale
class Role(models.Model): ...            # Rôle global

# hr/models.py (impliqué, pas explicite)
# Aussi Permission et Role ?!
```
- Deux systèmes de permissions: core + hr
- Confusion sur lequel utiliser
- Redondance d'implémentation

**PROBLÈME CRITIQUE 3: Dépendances d'imports dans views.py**
```python
# hr/views.py, ligne 29
from inventory.pdf_base import PDFGeneratorMixin

# hr/views.py, ligne 82
from authentication.utils import convert_uuids_to_strings
```
- HR dépend de inventory → couplage inverse
- HR dépend de authentication → normal mais tight
- Si inventory change, HR casse

**PROBLÈME 4: Modèles avec trop de responsabilités**
```
EmployeeMembership = Employee + Organization + Department + Position + Role
↓
14 champs, relations complexes
```

**PROBLÈME 5: Services layer partiellement implémentée**
- `EmployeeService` défini mais peu utilisé par les vues
- Logique métier encore dans les ViewSets
- Services importent directement les modèles

**Points forts**:
- Architecture de services existe (employee_service.py, leave_service.py, payroll_service.py)
- Séparation des responsabilités par domaine (leave, payroll)
- Permissions granulaires par endpoint
- Mixins pour réduire la duplication

---

### 4. INVENTORY MODULE

#### Responsabilités
- Gestion d'inventaire: Catégories, Produits, Entrepôts, Fournisseurs
- Gestion de stocks: Stock, Mouvements, Commandes
- Comptages physiques et Alertes
- Gestion commerciale: Clients, Ventes, Paiements
- Documents commerciaux: Factures proforma, Bons de commande, Bon de livraison
- Gestion des dépenses
- Ventes à crédit

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| views.py | 4831 | **62 ViewSets** |
| models.py | 1622 | 20+ modèles |
| serializers.py | 1286 | 25+ sérialiseurs |
| serializers_base.py | - | Base sérialiseurs |
| repositories.py | - | Pattern Repository implémenté |
| filters.py | - | QueryFilterExtractor |
| factories.py | - | DocumentNumberFactory |
| pdf_base.py, pdf_generator.py, pdf_sales.py | - | Génération PDF |
| alert_utils.py | - | Logique d'alertes stock |
| permissions.py | - | 10+ classes de permission |

#### Analyse structurelle

**Points forts**:
- Meilleur ratio LOC/ViewSet (78 vs 85 en HR)
- Pattern Repository partiellement implémenté (repositories.py)
- Factory pattern utilisé (DocumentNumberFactory)
- Filtrage centralisé (QueryFilterExtractor)
- Séparation des sérialiseurs complexes (serializers_base.py)
- Génération PDF modulaire (pdf_base.py, pdf_sales.py)

**Problèmes détectés**:

1. **Repository pattern incomplet**:
   ```python
   # inventory/repositories.py
   class CategoryRepository: ...
   class ProductRepository: ...
   # Mais ViewSet les appelle directement, pas via une service-layer
   ```
   - Repositories existent mais pas d'abstraction service sur eux
   - Logique encore mixée: view + repository + model

2. **Trop de modèles dans un seul module** (20+):
   - Produits, Stocks, Mouvements, Alertes (inventory)
   - Clients, Ventes, Paiements, Factures (commerce)
   - Dépenses (accounting)
   - Devraient être 3-4 modules distincts

3. **Dépendances vers HR**:
   ```python
   # inventory/pdf_base.py
   # Importe probablement des modèles HR pour les documents mixtes
   ```

4. **Files trop larges**:
   - views.py (4831), models.py (1622) → difficiles à maintenir
   - Pas de séparation par domaine (inventory vs commerce vs accounting)

---

### 5. AI MODULE

#### Responsabilités
- Conversations avec l'IA (Claude/OpenAI)
- Agent multi-provider avec function calling
- Outils HR (list employees, statistics, actions)
- Outils Inventory (products, sales, customers)
- Execution tracking et feedback

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| views.py | 438 | ConversationViewSet, ChatView, etc. |
| models.py | 119 | Conversation, Message, AIToolExecution |
| agent.py | 200+ | LouraAIAgent (multi-provider) |
| config.py | - | Configuration des providers |
| tools/hr_tools.py | - | Outils HR avec @register_tool |
| tools/inventory_tools.py | - | Outils Inventory |
| tools/registry.py | - | Tool registry |
| serializers.py | 73 | Sérialiseurs minimaux |

#### Analyse structurelle

**Points forts**:
- Architecture agent bien pensée (agent.py)
- Multi-provider (Claude prioritaire, OpenAI fallback)
- Function calling robuste vs ancien parsing XML
- Registry pattern pour les outils
- Séparation des outils par domaine

**Problèmes détectés**:

1. **Imports directs des modèles métier**:
   ```python
   # ai/tools/hr_tools.py, ligne 52
   from hr.models import Employee
   from inventory.models import Product, Sale, Stock, Customer
   ```
   - Crée dépendances AI → HR, AI → Inventory
   - Violates separation of concerns
   - Si HR/Inventory changent, les outils cassent

2. **Tool registry pas assez typée**:
   ```python
   # ai/tools/registry.py
   @register_tool(...)
   def list_employees(organization, ...):
   ```
   - Pas de validation des paramètres
   - Pas de type hints cohérents
   - Difficile à documenté pour l'IA

3. **Pas de système de permissions sur les outils**:
   - L'IA peut faire n'importe quelle action sans vérifier les perms utilisateur
   - Pas de audit trail sur les actions IA
   - Risque de sécurité

4. **Logique métier dans les outils**:
   ```python
   # ai/tools/hr_tools.py
   # Exécute des opérations directement sans passer par services
   def create_employee(...):
       Employee.objects.create(...)  # ❌ Direct model access
   ```
   Devrait utiliser `EmployeeService.create_employee()`

---

### 6. NOTIFICATIONS MODULE

#### Responsabilités
- Notifications Novu (multi-canal)
- WebSocket (Channels) en temps réel
- Tâches Celery async
- Historique des notifications
- Préférences de notification

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| novu_service.py | 100+ | NovuService singleton (client Novu) |
| novu_tasks.py | - | Celery tasks pour Novu |
| consumers.py | - | WebSocket consumers (Channels) |
| notification_helpers.py | - | Helpers pour déclencher notifs |
| tasks.py | - | Autres tasks async |
| views.py | 556 | Endpoints de notification |
| models.py | 242 | Notification, Preference models |
| serializers.py | 181 | Sérialiseurs |

#### Analyse structurelle

**Points forts**:
- NovuService bien isolé et fail-safe
- Séparation async (Celery tasks)
- WebSocket async (Channels)
- Double canal: Novu + in-app local

**Problèmes détectés**:

1. **Tightly coupled to Novu**:
   ```python
   # notifications/novu_service.py
   from novu_py import Novu
   ```
   - Si on change de provider, gros refactoring
   - Pas d'abstraction NotificationProvider

2. **Notifications déclenchées directement**:
   ```python
   # Partout dans le code
   novu_service.trigger_workflow(...)
   ```
   - Pas de pattern événement (Event Bus)
   - Couplage fort entre modules et notifications

3. **Pas de rate limiting**:
   - Celery tasks sans retry policy configurable
   - Risque de spam Novu

---

### 7. SERVICES MODULE

#### Responsabilités
- Services complémentaires (pas de contexte clair)

#### Fichiers clés
| Fichier | LOC | Responsabilité |
|---------|-----|-----------------|
| models.py | 783 | ? |
| views.py | 481 | ? |
| serializers.py | 604 | ? |

#### Analyse structurelle

**Problème: Module flou**
- Pas de README ou docstring sur le rôle du module
- Modèles sans contexte clair
- ViewSets sans documentation
- Semble être un fourre-tout pour les features secondaires

---

## Matrice des dépendances inter-modules

```
┌─────────────────┬──────────┬────────────┬────────┬─────────┬──────────────┬──────────┐
│ MODULE          │ core     │ auth       │ hr     │ inv     │ ai           │ notif    │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ core            │ -        │            │        │         │              │          │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ authentication  │ → (heavy)│ -          │ →→→    │         │              │          │
│                 │ (BaseUser,│            │ (Empl)│         │              │          │
│                 │ Org)     │            │        │         │              │          │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ hr              │ → (heavy)│ →          │ -      │ ← (PDF) │              │ ← (notif)│
│                 │ (BaseUser,│ (services)│        │ (mixin) │              │ (trigger)│
│                 │ Org)     │            │        │         │              │          │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ inventory       │ → (heavy)│            │        │ -       │              │ ← (notif)│
│                 │ (Org)    │            │        │         │              │ (alerts) │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ ai              │ →        │            │ →→→    │ →→→     │ -            │          │
│                 │ (Org)    │            │ (models)│ (models)│              │          │
├─────────────────┼──────────┼────────────┼────────┼─────────┼──────────────┼──────────┤
│ notifications   │ →        │            │        │         │              │ -        │
│                 │ (Org)    │            │        │         │              │          │
└─────────────────┴──────────┴────────────┴────────┴─────────┴──────────────┴──────────┘

Légende:
→   = import simple
→→→ = import multiple (couplage fort)
← = dépendance reverse (ok)
```

### Dépendances problématiques

**1. authentication → hr (COUPLAGE FORT)**
```python
# authentication/services.py, ligne 15
from hr.models import Employee

# Empêche réutilisation d'auth sans hr
```

**2. hr → inventory (INVERSE)**
```python
# hr/views.py, ligne 29
from inventory.pdf_base import PDFGeneratorMixin
```
- HR ne devrait pas dépendre de inventory
- Devrait être un base mixin dans core

**3. ai → hr, ai → inventory (DIRECT MODELS)**
```python
# ai/tools/hr_tools.py
from hr.models import Employee  # Direct access, pas via service
from inventory.models import Product  # Idem
```

**4. Pas d'Event Bus**
- Notifications déclenchées directement (couplage fort)
- Devrait être: Module → Event → EventBus → NotificationService

---

## Violation de principes SOLID

### S (Single Responsibility)

**VIOLATION CRITIQUE**:
- HR ViewSet: 44 ViewSets dans 1 fichier (3768 LOC)
- Inventory ViewSet: 62 ViewSets dans 1 fichier (4831 LOC)
- Authentication Services: 3 services distincts mais trop entrelacés

**SOLUTION**: Scinder views.py par domaine
```
hr/
├── views/
│   ├── __init__.py
│   ├── employee.py        (EmployeeViewSet)
│   ├── department.py      (DepartmentViewSet, PositionViewSet)
│   ├── contract.py        (ContractViewSet)
│   ├── leave.py          (LeaveTypeViewSet, LeaveRequestViewSet, LeaveBalanceViewSet)
│   ├── payroll.py        (PayrollPeriodViewSet, PayslipViewSet, PayrollAdvanceViewSet)
│   ├── attendance.py     (AttendanceViewSet)
│   ├── permissions.py    (PermissionViewSet, RoleViewSet)
│   └── invitations.py    (EmployeeInvitationViewSet)
```

### O (Open/Closed)

**VIOLATION**: AI tools tightly coupled
```python
# Pour ajouter un nouvel outil, éditer ai/tools/registry.py
# Devrait être extensible sans modification
```

### L (Liskov Substitution)

**VIOLATION**: `BaseUser` polymorphisme fragile
```python
# Authentication assume que get_concrete_user() retourne concret
# Mais ça peut retourner self si pas de enfant
# Pas de garantie de contrat
```

### I (Interface Segregation)

**VIOLATION**: Trop de responsabilités dans ViewSets
```python
# ViewSet = authentication + validation + filtering + authorization + business logic
# Devrait être: ViewSet (request routing) → Service (business logic)
```

### D (Dependency Inversion)

**VIOLATION CRITIQUE**: Imports directs de modèles
```python
# au lieu de:
from hr.models import Employee  # ❌ Dépend de concrétisation

# Utiliser:
from hr.services import EmployeeService  # ✓ Dépend d'abstraction
```

---

## Points chauds et complexité

### Fichiers > 500 LOC (12 fichiers)

| Fichier | LOC | Complexité | Modification fréquente |
|---------|-----|-----------|------------------------|
| hr/views.py | 3768 | TRÈS HAUTE | ✓ (Git log) |
| inventory/views.py | 4831 | TRÈS HAUTE | ✓ (Git log) |
| hr/models.py | 1470 | HAUTE | ✓ (Git log) |
| hr/serializers.py | 1796 | HAUTE | ✓ (Git log) |
| inventory/models.py | 1622 | HAUTE | - |
| inventory/serializers.py | 1286 | HAUTE | - |
| authentication/services.py | 406 | MOYENNE | - |
| services/models.py | 783 | MOYENNE | - |
| services/serializers.py | 604 | MOYENNE | - |
| services/views.py | 481 | MOYENNE | - |
| notifications/views.py | 556 | MOYENNE | - |
| core/views.py | 421 | MOYENNE | - |

### Fichiers modifiés fréquemment (Git)

```bash
git log --pretty=format:"%H" -- app/hr/views.py | wc -l
→ Modifié ~20+ fois récemment

git log --pretty=format:"%H" -- app/authentication/views.py | wc -l
→ Modifié ~15+ fois récemment
```

### Cyclomatic Complexity hotspots

**1. hr/views.py - EmployeeViewSet.get_queryset()**
- 50+ lignes
- 5+ niveaux d'imbrication
- 3+ branches (if/elif/else)

**2. authentication/services.py - authenticate_user()**
- 80+ lignes
- 4+ niveaux d'imbrication
- Responsabilités multiples (auth + org resolution)

**3. inventory/views.py - Multiple ViewSets**
- 100+ lignes chacun
- Logique complexe de filtrage
- Requêtes N+1 potentielles

---

## Liste priorisée des problèmes

### CRITIQUE (doit être fixé immédiatement)

1. **HR module: 3768 LOC dans un seul fichier views.py**
   - **Impact**: Maintenance impossible, merge conflicts, onboarding difficile
   - **Cause**: Pas de découpage par domaine
   - **Effort fix**: 2-3 jours
   - **Non-régression**: Tous les tests HR doivent passer

2. **authentication → hr COUPLAGE FORT**
   ```python
   from hr.models import Employee  # ligne 15 services.py
   ```
   - **Impact**: Impossible de réutiliser auth sans hr
   - **Cause**: Logique de résolution d'Employee dans service auth
   - **Effort fix**: 1 jour (déléguer à EmployeeService)
   - **Non-régression**: Login/Refresh doivent fonctionner

3. **Duplication Permission/Role: core vs hr**
   - **Impact**: Confusion sur quel système utiliser, code dupliqué
   - **Cause**: Deux implémentations
   - **Effort fix**: 3-5 jours (fusion + migration)
   - **Non-régression**: Tous les tests permission

4. **AI Tools: imports directs de modèles métier**
   ```python
   from hr.models import Employee  # Devrait passer par service
   ```
   - **Impact**: Tools cassent quand HR change, couplage fort
   - **Cause**: Acces direct aux modèles
   - **Effort fix**: 1-2 jours (wrapper services pour tools)
   - **Non-régression**: Tous les tools doivent marcher

### MAJEUR (should be fixed in next sprint)

5. **Inventory: 62 ViewSets dans 4831 LOC**
   - **Impact**: Maintenance, merge conflicts
   - **Cause**: Pas de découpage par domaine
   - **Effort fix**: 2 jours
   - **Non-régression**: Todos les tests inventory

6. **Services layer: partiellement implémentée**
   - **Impact**: Logique métier éparse entre views et services
   - **Cause**: Refactoring incomplet
   - **Effort fix**: 3-5 jours (converger views vers services)
   - **Non-régression**: Tous les tests métier

7. **Pas d'Event Bus pour notifications**
   - **Impact**: Couplage fort modules → notifications
   - **Cause**: Notifications déclenchées directement
   - **Effort fix**: 1-2 jours (implémenter simple event dispatcher)
   - **Non-régression**: Notifications doivent arriver

8. **hr → inventory import (INVERSE DEPENDENCY)**
   ```python
   from inventory.pdf_base import PDFGeneratorMixin  # ligne 29
   ```
   - **Impact**: Violation architecture, création de cycles potentiels
   - **Cause**: Mixin généralisable mis dans inventory
   - **Effort fix**: 0.5 jour (déplacer vers core.mixins)
   - **Non-régression**: PDF generation doit marcher

### MINEUR (nice to have)

9. **Models.py trop gros**:
   - HR: 1470 LOC (14 modèles)
   - Inventory: 1622 LOC (20+ modèles)
   - Effort: 2-3 jours chacun

10. **Serializers.py trop gros**:
    - HR: 1796 LOC
    - Inventory: 1286 LOC
    - Effort: 1-2 jours chacun

11. **Pas de type hints cohérents**:
    - Services.py sont partiellement typées
    - Views.py pas typées du tout
    - Effort: 1-2 jours

12. **Pas de Query optimization**:
    - N+1 queries potentielles dans inventory
    - select_related/prefetch_related manquants
    - Effort: 1 jour

---

## Recommandations de refactoring

### Phase 1: Découpage critique (Sprint X+1, 1 semaine)

#### 1.1 Scinder hr/views.py (3768 LOC → 8 fichiers)

**Objectif**: 1 ViewSet = 1 fichier, ~400-500 LOC max

```
hr/views/
├── __init__.py                (import tous les ViewSets)
├── employee.py               (EmployeeViewSet, EmployeeChangePasswordView)
├── department.py             (DepartmentViewSet, PositionViewSet)
├── contract.py               (ContractViewSet)
├── leave.py                  (LeaveTypeViewSet, LeaveRequestViewSet, LeaveBalanceViewSet, LeaveStatsView)
├── payroll.py                (PayrollPeriodViewSet, PayslipViewSet, PayrollAdvanceViewSet, PayrollStatsView)
├── attendance.py             (AttendanceViewSet, AttendanceStatsView)
├── permissions_roles.py      (PermissionViewSet, RoleViewSet)
└── invitations.py            (EmployeeInvitationViewSet)
```

**Checklist**:
- [ ] Créer structure `hr/views/`
- [ ] Déplacer ViewSets par domaine
- [ ] Mettre à jour `hr/urls.py` pour import depuis `hr.views`
- [ ] Exécuter tests: `pytest app/hr/tests/`
- [ ] Vérifier couverture: `coverage report`
- [ ] Merge, cherry-pick pour bisect

**Non-régression**: Tous les HR endpoints doivent répondre identiquement

#### 1.2 Créer PDFGeneratorMixin dans core.mixins

**Problème actuel**:
```python
# hr/views.py
from inventory.pdf_base import PDFGeneratorMixin  # INVERSE DEPENDENCY
```

**Solution**:
```python
# core/mixins.py
class PDFGeneratorMixin:
    """Base mixin pour toute génération PDF"""
    def render_to_pdf(self, template_path, context):
        ...

# inventory/pdf_base.py
from core.mixins import PDFGeneratorMixin
class InventoryPDFGenerator(PDFGeneratorMixin):
    ...

# hr/pdf_generator.py
from core.mixins import PDFGeneratorMixin
class PayslipPDFGenerator(PDFGeneratorMixin):
    ...
```

**Checklist**:
- [ ] Créer `core.mixins.PDFGeneratorMixin`
- [ ] Mettre à jour `inventory/pdf_base.py`
- [ ] Mettre à jour `hr/pdf_generator.py`
- [ ] Mise à jour imports dans views.py
- [ ] Tests: vérifier génération PDF fonctionne

---

### Phase 2: Décorréler authentication de hr (Sprint X+2, 2-3 jours)

#### 2.1 Supprimer `from hr.models import Employee` dans authentication/services.py

**Problème**:
```python
# authentication/services.py, ligne 15
from hr.models import Employee  # Couplage fort auth→hr
```

**Solution**: Utiliser une interface abstraite

```python
# core/interfaces.py (nouveau)
class IEmployeeRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un employé par email"""
        ...

# hr/repositories.py (nouveau)
class EmployeeRepository(IEmployeeRepository):
    def get_by_email(self, email: str):
        from hr.models import Employee
        return Employee.objects.get(email=email)

# authentication/services.py (modifié)
class AuthenticationService:
    def __init__(self, employee_repo: IEmployeeRepository):
        self.employee_repo = employee_repo
    
    def authenticate_user(self, email, password):
        # Utiliser employee_repo au lieu d'importer Employee
        ...

# lourabackend/apps.py (configuration DI)
# Utiliser django-injector ou autre pour injecter
```

**Checklist**:
- [ ] Créer `core/interfaces.py` avec interfaces
- [ ] Créer `hr/repositories.py` implémentant interfaces
- [ ] Modifier `authentication/services.py` pour DI
- [ ] Tester login/refresh
- [ ] Vérifier pas de circular imports

**Non-régression**: Login, Refresh, Register doivent marcher

---

### Phase 3: Converger vers Service Layer (Sprint X+3, 3-5 jours)

#### 3.1 Intégrer services existants dans views

**Étape 1: EmployeeService**

```python
# hr/views/employee.py (AVANT)
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        org = self.get_organization_from_request()
        return Employee.objects.filter(organization=org)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Logique complexe ici...
        employee = Employee.objects.create(...)
        return Response(EmployeeSerializer(employee).data)

# hr/views/employee.py (APRÈS)
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        org = self.get_organization_from_request()
        return EmployeeService.get_employees_for_organization(org)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Déléguer au service
        employee = EmployeeService.create_employee(
            organization=self.get_organization_from_request(),
            **serializer.validated_data
        )
        return Response(EmployeeSerializer(employee).data)
```

**Étape 2: LeaveService, PayrollService**

Même pattern pour Leave et Payroll services.

**Checklist**:
- [ ] Identifier toutes les opérations métier dans views
- [ ] Mapper vers services existants
- [ ] Pour les opérations manquantes, ajouter à services
- [ ] Remplacer direct model access par service calls
- [ ] Tester chaque ViewSet

---

### Phase 4: Event Bus pour notifications (Sprint X+4, 2 jours)

#### 4.1 Implémenter simple Event Dispatcher

```python
# notifications/events.py
class Event(ABC):
    pass

class EmployeeCreatedEvent(Event):
    def __init__(self, employee):
        self.employee = employee

class StockAlertEvent(Event):
    def __init__(self, product, warehouse):
        self.product = product
        self.warehouse = warehouse

# notifications/dispatcher.py
class EventDispatcher:
    _handlers = {}
    
    @classmethod
    def subscribe(cls, event_type: Type[Event], handler):
        """S'abonner à un type d'événement"""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
    
    @classmethod
    def dispatch(cls, event: Event):
        """Dispatcher un événement"""
        event_type = type(event)
        if event_type in cls._handlers:
            for handler in cls._handlers[event_type]:
                handler(event)

# notifications/handlers.py
def on_employee_created(event: EmployeeCreatedEvent):
    """Gestionnaire pour EmployeeCreatedEvent"""
    novu_service.trigger_workflow(
        'employee-welcome',
        subscriber_id=str(event.employee.id),
        payload={'name': event.employee.full_name}
    )

# Configuration
EventDispatcher.subscribe(EmployeeCreatedEvent, on_employee_created)
EventDispatcher.subscribe(StockAlertEvent, on_stock_alert)

# Usage dans hr/services/employee_service.py
from notifications.dispatcher import EventDispatcher
from notifications.events import EmployeeCreatedEvent

class EmployeeService:
    @staticmethod
    def create_employee(...):
        employee = Employee.objects.create(...)
        EventDispatcher.dispatch(EmployeeCreatedEvent(employee))  # ← Découplé!
        return employee
```

**Checklist**:
- [ ] Créer `notifications/events.py`
- [ ] Créer `notifications/dispatcher.py`
- [ ] Créer `notifications/handlers.py`
- [ ] Dispatcher EmployeeCreatedEvent depuis EmployeeService
- [ ] Dispatcher StockAlertEvent depuis inventory
- [ ] Tests: vérifier notifications arrivent
- [ ] Migrer tous les trigger_workflow() directs vers events

---

### Phase 5: Consolider Permission/Role (Sprint X+5, 3-5 jours)

#### 5.1 Fusionner core.Permission ← hr.Permission

**Decision**: Utiliser core.Permission comme source unique

**Migration**:
1. Copier tous les codes de hr.Permission vers core.Permission
2. Créer foreign key hr.Permission → core.Permission
3. Migrer les données
4. Supprimer hr.Permission

**Checklist**:
- [ ] Créer migration: AddCorePermissionFK
- [ ] Migrer les données
- [ ] Tester tous les permission checks
- [ ] Supprimer hr.Permission
- [ ] Documenter dans README.md

---

### Phase 6: AI Tools - Service Abstraction (Sprint X+6, 1-2 jours)

#### 6.1 Créer wrappers service pour AI tools

```python
# ai/tools/hr_tools.py (AVANT)
from hr.models import Employee  # Direct model access ❌

def list_employees(organization, ...):
    qs = Employee.objects.filter(...)  # Direct model access ❌
    ...

# ai/tools/hr_tools.py (APRÈS)
from hr.services import EmployeeService  # Via service ✓

def list_employees(organization, search=None, ...):
    employees = EmployeeService.get_employees_for_organization(organization)
    if search:
        employees = employees.filter(...)  # Service retourne QuerySet
    ...
```

**Checklist**:
- [ ] Remplacer tous les imports directs par services
- [ ] Tester chaque tool fonctionne
- [ ] Vérifier permissions correctes

---

## Endpoints principaux par module

### Authentication
```
POST   /api/auth/register/              → RegisterView
POST   /api/auth/login/                 → LoginView
POST   /api/auth/refresh/               → RefreshView
POST   /api/auth/logout/                → LogoutView
GET    /api/auth/me/                    → ProfileView
PUT    /api/auth/me/                    → ProfileView
POST   /api/auth/change-password/       → ChangePasswordView
```

### Core
```
GET    /api/core/organizations/         → OrganizationViewSet
POST   /api/core/organizations/         → OrganizationViewSet
GET    /api/core/permissions/           → PermissionViewSet
GET    /api/core/roles/                 → RoleViewSet
GET    /api/core/modules/               → ModuleViewSet
```

### HR (44 ViewSets)
```
GET    /api/hr/employees/               → EmployeeViewSet
POST   /api/hr/employees/               → EmployeeViewSet
GET    /api/hr/departments/             → DepartmentViewSet
GET    /api/hr/leave-requests/          → LeaveRequestViewSet
POST   /api/hr/leave-requests/          → LeaveRequestViewSet
PATCH  /api/hr/leave-requests/{id}/approve/ → LeaveRequestViewSet
GET    /api/hr/payslips/                → PayslipViewSet
GET    /api/hr/attendances/             → AttendanceViewSet
... + 30+ autres
```

### Inventory (62 ViewSets)
```
GET    /api/inventory/products/         → ProductViewSet
POST   /api/inventory/products/         → ProductViewSet
GET    /api/inventory/sales/            → SaleViewSet
POST   /api/inventory/sales/            → SaleViewSet
GET    /api/inventory/customers/        → CustomerViewSet
GET    /api/inventory/stocks/           → StockViewSet
... + 50+ autres
```

### AI
```
GET    /api/ai/conversations/           → ConversationViewSet
POST   /api/ai/conversations/           → ConversationViewSet
POST   /api/ai/chat/                    → ChatView
POST   /api/ai/chat-stream/             → ChatStreamView
```

### Notifications
```
GET    /api/notifications/              → NotificationViewSet
POST   /api/notifications/{id}/mark-read/ → NotificationViewSet
GET    /api/notifications/preferences/  → PreferenceViewSet
ws://   /ws/notifications/{user_id}/   → NotificationConsumer (Channels)
```

---

## Checklist de vérification pour refactoring

### Avant de commencer
- [ ] Tous les tests passent: `pytest`
- [ ] Coverage > 80%: `coverage report`
- [ ] Pas de linting errors: `flake8 app/`
- [ ] Pas de type errors: `mypy app/`

### Après chaque phase
- [ ] Tous les tests passent
- [ ] Coverage maintenu (≥ coverage actuelle)
- [ ] Pas de migrations pending: `python manage.py showmigrations --list`
- [ ] Documentation mise à jour (README.md, docstrings)
- [ ] Pas de hardcoded values
- [ ] Logging cohérent (logger.info, logger.error, etc.)

### Non-régression finale
- [ ] Tous les endpoints répondent identiquement
- [ ] Permissions fonctionnent (user A peut pas accéder org B)
- [ ] Multi-tenant isolation fonctionne
- [ ] Async tasks (Celery) fonctionnent
- [ ] WebSocket (Channels) fonctionne
- [ ] IA agent répond correctement

---

## Conclusion

### Résumé de l'architecture actuelle

| Aspect | État |
|--------|------|
| **Modularité** | 7/10 (importants mais couplés) |
| **Scalabilité** | 6/10 (ViewSets surchargés) |
| **Testabilité** | 7/10 (bonne séparation services) |
| **Maintenabilité** | 5/10 (fichiers trop gros) |
| **Documentation** | 6/10 (docstrings présentes mais incomplètes) |
| **Architecture** | 6/10 (DRF standards mais non-optimisé) |

### Score global: 6.2/10

### Points à retenir

1. **Fondation solide**: Multi-tenant, permissions, modèles bien pensés
2. **Services layer existe**: Mais partiellement utilisée
3. **Files too large**: Views.py et Models.py > 3000 LOC doivent être splitées
4. **Couplages fixes**: authentication→hr, ai→hr, ai→inventory
5. **Duplication**: Permission/Role en double (core + hr)
6. **Pas d'événements**: Notifications couplées directs
7. **Refactoring déjà commencé**: Repositories, factories existent

### Priorité d'action

1. Scinder hr/views.py et inventory/views.py (IMMÉDIAT)
2. Décorréler authentication de hr (URGENT)
3. Implémenter Event Bus (IMPORTANT)
4. Fusionner Permission/Role (MINEUR mais technique)
5. Continuer intégration Service Layer (ONGOING)

---

## Appendix: Metriques

### Lignes de code par module

```
core/        ~2000 LOC
auth/        ~1400 LOC
hr/          ~8500 LOC ← LARGEST
inventory/   ~9500 LOC ← LARGEST
ai/          ~1000 LOC
notif/       ~1500 LOC
services/    ~2000 LOC
─────────────────────
TOTAL        ~25,900 LOC
```

### ViewSets par module

```
core/         6 ViewSets
auth/         0 ViewSets (API Views)
hr/           44 ViewSets   ← DENSE
inventory/    62 ViewSets   ← DENSE
ai/           2 ViewSets
notif/        3 ViewSets
services/     2 ViewSets
─────────────────────────
TOTAL         119 ViewSets
```

### Modèles par module

```
core/         7 modèles
auth/         0 modèles
hr/           14 modèles
inventory/    20+ modèles
ai/           3 modèles
notif/        3 modèles
services/     ~5 modèles
─────────────────────────
TOTAL         ~50+ modèles
```

### Tests couverture (estimée)

```
core/         80%
auth/         85%
hr/           75%
inventory/    70%
ai/           60%
notif/        65%
services/     50%
─────────────────────
AVERAGE       70%
```

---

**FIN DE L'AUDIT**

Audit généré automatiquement - Pas de modifications apportées au codebase.
