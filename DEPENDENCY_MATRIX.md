# Matrice détaillée des dépendances inter-modules

## Graph des dépendances (texte simplifié)

```
┌─────────────────────────────────────────────────────────────┐
│                       LOURA BACKEND                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLIENT (React Frontend)                                    │
│        │                                                    │
│        ├──→ REST API (DRF)                                 │
│        │     ├── GET /api/auth/me/                         │
│        │     ├── POST /api/hr/employees/                   │
│        │     ├── GET /api/inventory/products/              │
│        │     ├── POST /api/ai/chat/                        │
│        │     └── ...                                       │
│        │                                                    │
│        └──→ WebSocket (Channels)                            │
│              └── ws://api/notifications/                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    DJANGO APPS                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CORE (Foundation)                                       │
│     ├── Models: BaseUser, Organization, Permission, Role   │
│     ├── Mixins: OrganizationResolverMixin, ...             │
│     └── Permissions: RBAC system                            │
│                                                             │
│  2. AUTHENTICATION                                          │
│     ├── Login/Register                                      │
│     ├── TokenService (JWT)                                 │
│     ├── ProfileService                                     │
│     └── [DEPENDS ON] core, hr ← COUPLAGE FORT             │
│                                                             │
│  3. HR (44 ViewSets, 3768 LOC)                             │
│     ├── Employees, Departments, Positions                  │
│     ├── Leave Management (demandes, soldes)                │
│     ├── Payroll (fiches, avances)                          │
│     ├── Attendance (QR, check-in/out)                      │
│     ├── EmployeeService, LeaveService, PayrollService      │
│     ├── [DEPENDS ON] core, auth, inventory                 │
│     └── [IMPORTED BY] auth, ai, notifications              │
│                                                             │
│  4. INVENTORY (62 ViewSets, 4831 LOC)                       │
│     ├── Products, Categories, Warehouses, Suppliers        │
│     ├── Stocks, Movements, Orders, Alerts                  │
│     ├── Sales, Customers, Payments, Expenses               │
│     ├── PDF generation (PDFGeneratorMixin)                 │
│     ├── Repositories, Factories, Filters                   │
│     ├── [DEPENDS ON] core                                  │
│     └── [IMPORTED BY] hr (PDFGeneratorMixin), ai, notif   │
│                                                             │
│  5. AI (Agent + Tools)                                      │
│     ├── LouraAIAgent (Claude/OpenAI)                       │
│     ├── Tools (hr_tools, inventory_tools, registry)        │
│     ├── Conversations, Messages, Feedback                  │
│     ├── [DEPENDS ON] core, hr, inventory ← DIRECT MODELS   │
│     └── [PROBLEM] Imports Employee, Product, Sale directly │
│                                                             │
│  6. NOTIFICATIONS (Novu + Channels)                         │
│     ├── NovuService (singleton, fail-safe)                 │
│     ├── WebSocket consumers (Channels)                     │
│     ├── Event handlers (tasks, notification_helpers)       │
│     ├── [DEPENDS ON] core                                  │
│     └── [IMPORTED BY] hr, inventory (direct trigger)       │
│                                                             │
│  7. SERVICES (unknown purpose)                              │
│     └── [DEPENDS ON] core                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

DATABASE (PostgreSQL)
    ├── base_users (polymorphic)
    ├── admin_users
    ├── hr_employees
    ├── inventory_products
    ├── inventory_stocks
    └── ... (50+ tables)
```

## Dépendances explicites (grep results)

### Core exports
```
core/models.py exports:
  - BaseUser
  - AdminUser
  - Organization
  - Permission
  - Role
  - Module
  - OrganizationModule
  - Category
  - OrganizationSettings

core/mixins.py exports:
  - OrganizationResolverMixin (94 LOC)
  - OrganizationQuerySetMixin (150+ LOC)
  - OrganizationCreateMixin
  - BaseOrganizationViewSetMixin
```

### Authentication dependencies
```
authentication/services.py:
  ├─ from core.models import BaseUser, AdminUser, Organization ✓
  ├─ from hr.models import Employee ❌ COUPLAGE FORT
  │  └─ Used in: authenticate_user() ligne 73 (organization resolution)
  └─ Tightly coupled with hr

authentication/views.py:
  ├─ from core.models import Organization, AdminUser ✓
  ├─ from hr.models import EmployeeMembership (3 fois!) ❌
  │  └─ Used in: invite endpoint, accept endpoint
  └─ Direct model imports (tight coupling)

Problème: Authentication ne peut pas être réutilisée sans HR
```

### HR dependencies (CRITICAL)
```
hr/views.py (3768 LOC):
  ├─ from core.models import Organization, AdminUser ✓
  ├─ from core.mixins import OrganizationResolverMixin ✓
  ├─ from authentication.utils import convert_uuids_to_strings ✓
  ├─ from inventory.pdf_base import PDFGeneratorMixin ❌ INVERSE DEPENDENCY
  │  └─ Line 29: HR imports from inventory !
  └─ 50 imports internes (models, serializers, services, permissions)

hr/models.py (1470 LOC):
  ├─ from core.models import Organization, Role, Permission, BaseUser ✓
  └─ 14 modèles complexes

hr/services/:
  ├─ employee_service.py: imports hr.models (internal) ✓
  ├─ leave_service.py: imports hr.models (internal) ✓
  └─ payroll_service.py: imports hr.models (internal) ✓

Problème: HR dépend de Inventory pour PDF (inverse dependency)
Solution: PDFGeneratorMixin doit être dans core
```

### Inventory dependencies
```
inventory/views.py (4831 LOC):
  ├─ from core.models import Organization ✓
  ├─ from core.mixins import ... ✓
  ├─ from core.permissions import BaseHasPermission ✓
  ├─ from inventory.repositories import ... ✓ (internal)
  ├─ from inventory.filters import QueryFilterExtractor ✓ (internal)
  └─ Pas d'import problématique

inventory/pdf_base.py:
  ├─ Exporte PDFGeneratorMixin
  └─ Importé par hr (problème)

Problème: PDFGeneratorMixin trop générique, mis dans inventory
Solution: Déplacer vers core/mixins.py
```

### AI dependencies (PROBLÉMATIQUE)
```
ai/agent.py (200+ LOC):
  ├─ from .tools import registry ✓ (internal)
  └─ Pas d'imports problématiques directs

ai/tools/hr_tools.py:
  ├─ from hr.models import Employee ❌ DIRECT MODEL ACCESS
  │  └─ list_employees() line 52
  ├─ from hr.models import LeaveRequest ❌ DIRECT MODEL ACCESS
  │  └─ Used in multiple tools
  └─ Problème: Direct access, pas via service

ai/tools/inventory_tools.py:
  ├─ from inventory.models import Product ❌ DIRECT MODEL ACCESS
  ├─ from inventory.models import Stock ❌ DIRECT MODEL ACCESS
  ├─ from inventory.models import Sale ❌ DIRECT MODEL ACCESS
  ├─ from inventory.models import Customer ❌ DIRECT MODEL ACCESS
  └─ 4 imports directs de modèles

ai/tools/registry.py:
  └─ from inventory.models import Product (lazy import)

Problème: AI tightly coupled à HR et Inventory via modèles
Solution: Wrapper services pour les outils
  - list_employees(org) → EmployeeService.get_employees_for_organization(org)
  - get_products(org) → ProductRepository.get_filtered(org)
```

### Notifications dependencies
```
notifications/novu_service.py:
  ├─ from django.conf import settings ✓
  └─ Pas d'imports autres modules ✓ (bon isolement)

notifications/models.py:
  ├─ from core.models import Organization ✓
  └─ Pas de couplages

notifications/views.py:
  ├─ from core.models import Organization ✓
  └─ Pas de couplages directs

Problème: Notifications déclenchées directement des autres modules
  - hr/views.py: novu_service.trigger_workflow(...) (direct call)
  - inventory/tasks.py: novu_service.trigger_workflow(...) (direct call)
  
Solution: Event Bus pour découpler
  - Module → EventDispatcher.dispatch(Event)
  - Notifications subscribe aux événements
```

## Dépendances circulaires détectées

### Cycle potentiel 1: authentication ↔ hr

```
authentication/services.py
    │
    ├─→ from hr.models import Employee
    │   └─→ hr/models.py
    │       └─→ from core.models import BaseUser
    │           └─→ core/models.py
    │               └─→ BaseUser (parent de AdminUser/Employee)
    │
    └─→ core/models.py (direct import)
        └─→ BaseUser
```

**Risque**: Si hr/models.py importe quelque chose de authentication, cycle
**Status**: Actuellement OK (hr ne dépend pas de auth directement)
**Recommandation**: Surveiller les imports

### Pas de cycle détecté 2: hr ↔ inventory

```
hr/views.py
    └─→ from inventory.pdf_base import PDFGeneratorMixin

inventory/views.py
    └─→ Does NOT import from hr ✓
```

**Status**: Inverse dependency mais pas circulaire

## Impact des dépendances problématiques

### 1. authentication → hr COUPLAGE

**Impact si HR change**:
```
Scenario: Renommer Employee.email → Employee.email_address

Cascade:
  1. HR models change (1 file)
  2. HR serializers change (5 places)
  3. HR services change (2 places)
  4. Authentication services change ← BREAKS!
     └─ authenticate_user() expects employee.email
  5. Authentication views change ← BREAKS!
     └─ invite_employee() expects EmployeeMembership
```

**Effort to fix**: 2-3 hours × number of changes

**Recommendation**: Injecter dépendances au lieu d'importer

---

### 2. hr → inventory PDFGeneratorMixin

**Impact**:
```
If inventory/pdf_base.py changed:
  → hr/views.py breaks ✗

Inverse dependency violation:
  - Core → Auth → HR → Inventory
  - Should NEVER be: HR → Inventory
```

**Effort to fix**: 30 minutes (move mixin)

---

### 3. ai → hr, ai → inventory DIRECT MODELS

**Impact**:
```
If HR changes Employee model:
  → ai/tools/hr_tools.py breaks ✗
     └─ list_employees() can't fetch employees
     
If inventory changes Product model:
  → ai/tools/inventory_tools.py breaks ✗
     └─ list_products() can't fetch products
```

**Effort to fix**: 1-2 hours (create service wrappers)

---

### 4. Notifications: direct trigger_workflow() calls

**Impact**:
```
If Novu API changes:
  → All modules fail (no abstraction)
  
If switch to SendGrid/Twilio:
  → Need to change 10+ files across all modules
```

**Effort to fix**: 2 hours (implement Event Bus)

---

## Summary table

| Probleme | Modules affectés | Severity | Effort | Fix pattern |
|----------|------------------|----------|--------|------------|
| auth → hr | 2 (auth, hr) | HIGH | 2-3h | DI, Services |
| hr → inventory (PDF) | 2 (hr, inventory) | MEDIUM | 30min | Move mixin |
| ai → hr (direct models) | 2 (ai, hr) | HIGH | 1-2h | Service wrapper |
| ai → inventory (direct) | 2 (ai, inventory) | HIGH | 1-2h | Service wrapper |
| notif ← direct calls | 3+ (hr, inv, etc) | MEDIUM | 2h | Event Bus |
| Large views.py files | 2 (hr: 3768, inv: 4831) | MEDIUM | 2-3d | Split by domain |
| Duplicate Permission/Role | 2 (core, hr) | MEDIUM | 3-5d | Merge + migrate |

---

## Dependency import frequency

```
Import counts (grep -r 'from X import'):

Most imported modules:
  1. core.models          71 times → Expected (foundation)
  2. hr.models            15 times → Problematic if in auth/ai
  3. inventory.models     10 times → Problematic if in ai
  4. core.mixins          8 times  → Expected
  5. authentication.*     4 times  → Low (good)
  6. notifications.*      2 times  → Low (good, mostly singleton)

Most problematic imports:
  - from hr.models (in auth)     → COUPLAGE FORT
  - from inventory.pdf (in hr)   → INVERSE DEPENDENCY
  - from hr.models (in ai)       → DIRECT MODEL ACCESS
  - from inventory.models (in ai) → DIRECT MODEL ACCESS
```

---

**Generated**: Avril 2026 - No files modified
