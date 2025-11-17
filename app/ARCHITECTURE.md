# Architecture - Loura Backend

## Vue d'ensemble

Loura est une plateforme multi-tenant permettant à des administrateurs de créer et gérer des organisations, et (dans une phase future) aux employés de ces organisations de se connecter et travailler avec des permissions limitées.

## Architecture en phases

### Phase 1 - IMPLÉMENTÉE ✅

**AdminUser & Organization Management**

```
┌─────────────┐
│  AdminUser  │ (1 user can manage multiple organizations)
└──────┬──────┘
       │ manages (1:N)
       ▼
┌──────────────┐
│ Organization │ (each org has 1 admin owner)
└──────┬───────┘
       │ has (1:1)
       ▼
┌────────────────────────┐
│ OrganizationSettings   │ (currency, country, theme, etc.)
└────────────────────────┘
```

**Flux d'authentification actuel:**

1. **AdminUser s'inscrit** → Reçoit un token
2. **AdminUser se connecte** → Reçoit un token
3. **AdminUser crée des organisations** → Via API authentifiée
4. **AdminUser gère ses organisations** → CRUD complet

**Endpoints:**
- `/api/core/auth/register/` - Inscription AdminUser
- `/api/core/auth/login/` - Connexion AdminUser
- `/api/core/auth/logout/` - Déconnexion AdminUser
- `/api/core/auth/me/` - Profil AdminUser
- `/api/core/organizations/` - CRUD Organizations
- `/api/core/categories/` - Liste des catégories

### Phase 2 - PLANIFIÉE 🔜

**Employee Management & Multi-Authentication**

```
┌─────────────┐
│  AdminUser  │ (creates organizations & employees)
└──────┬──────┘
       │ owns (1:N)
       ▼
┌──────────────┐         ┌──────────────┐
│ Organization │◄────────┤   Employee   │ (N employees per org)
└──────┬───────┘ works   └──────────────┘
       │ for (N:1)              │
       │                        │ has (1:N)
       │                        ▼
       │                ┌──────────────────────┐
       │                │ EmployeePermission   │
       │                └──────────────────────┘
       │ has (1:1)
       ▼
┌────────────────────────┐
│ OrganizationSettings   │
└────────────────────────┘
```

**Flux d'authentification futur:**

**Pour AdminUser (existant):**
1. S'inscrit via `/api/core/auth/register/`
2. Se connecte via `/api/core/auth/login/`
3. Crée/gère ses organisations
4. **Crée des employés** pour ses organisations

**Pour Employee (à implémenter):**
1. **Créé par un AdminUser** (pas d'auto-inscription)
2. Se connecte via `/api/hr/auth/login/` avec:
   - Email
   - Password
   - **Organization subdomain** (pour scoping)
3. Accède uniquement aux données de son organisation
4. Permissions basées sur son rôle

**Nouveaux endpoints prévus:**
- `/api/hr/auth/login/` - Connexion Employee
- `/api/hr/auth/logout/` - Déconnexion Employee
- `/api/hr/auth/me/` - Profil Employee
- `/api/hr/employees/` - CRUD Employees (AdminUser only)
- `/api/hr/employees/{id}/permissions/` - Gestion permissions

## Modèles de données

### Phase 1 (Actuelle)

#### AdminUser
```python
class AdminUser(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = EmailField(unique=True)
    first_name = CharField
    last_name = CharField
    is_active = BooleanField
    is_staff = BooleanField

    # Authentification
    USERNAME_FIELD = 'email'
```

#### Organization
```python
class Organization(TimeStampedModel):
    name = CharField
    subdomain = SlugField(unique=True)
    logo_url = URLField
    category = ForeignKey(Category)
    admin = ForeignKey(AdminUser)  # Owner
    is_active = BooleanField
```

#### OrganizationSettings
```python
class OrganizationSettings(Model):
    organization = OneToOneField(Organization)
    country = CharField
    currency = CharField  # Default: MAD
    theme = CharField
    contact_email = EmailField
```

### Phase 2 (Planifiée)

#### Employee
```python
class Employee(BaseProfile, TimeStampedModel):
    organization = ForeignKey(Organization)  # Scoping obligatoire
    email = EmailField  # Unique per organization
    first_name = CharField
    last_name = CharField
    employee_id = CharField
    position = CharField
    department = CharField
    hire_date = DateField
    role = CharField(choices=['admin', 'manager', 'employee', 'readonly'])

    # Authentification
    USERNAME_FIELD = 'email'

    class Meta:
        unique_together = [['email', 'organization']]
```

#### EmployeePermission
```python
class EmployeePermission(TimeStampedModel):
    employee = ForeignKey(Employee)
    permission_code = CharField
    permission_name = CharField
```

## Authentification

### Système actuel (Token-based)

```
Client                    Backend                 Database
  │                         │                        │
  │──Register/Login────────>│                        │
  │                         │──Create/Get Token────>│
  │<─────Token──────────────│<──────────────────────│
  │                         │                        │
  │──API Request───────────>│                        │
  │  Header: Token          │                        │
  │                         │──Verify Token─────────>│
  │                         │<──User Info───────────│
  │                         │──Query Data───────────>│
  │<─────Response───────────│<──────────────────────│
```

### Système futur (Dual Authentication)

**AdminUser Flow:**
```
POST /api/core/auth/login/
{
  "email": "admin@example.com",
  "password": "xxx"
}
→ Returns: { token, user_type: "admin" }
```

**Employee Flow:**
```
POST /api/hr/auth/login/
{
  "email": "employee@example.com",
  "password": "xxx",
  "organization": "company-subdomain"  // Required!
}
→ Returns: { token, user_type: "employee", organization_id }
```

## Isolation des données (Multi-Tenancy)

### Règles d'isolation

1. **AdminUser**:
   - Peut créer plusieurs organizations
   - Ne voit QUE ses propres organizations
   - Accès complet aux données de ses organizations

2. **Employee** (futur):
   - Appartient à UNE SEULE organization
   - Ne peut accéder QU'AUX données de son organization
   - Permissions limitées selon son rôle

### Implémentation

**Actuelle (AdminUser):**
```python
class OrganizationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Filter by current admin user
        return Organization.objects.filter(admin=self.request.user)
```

**Future (Employee):**
```python
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Filter by employee's organization
        return Employee.objects.filter(
            organization=self.request.user.organization
        )
```

## Permissions

### Actuelles

- **AllowAny**: Endpoints publics (register, login)
- **IsAuthenticated**: Endpoints protégés (organizations, etc.)

### Futures

**Custom permissions à implémenter:**

```python
class IsAdminUser(BasePermission):
    """Check if user is an AdminUser (not Employee)"""
    def has_permission(self, request, view):
        return isinstance(request.user, AdminUser)

class IsEmployeeOfOrganization(BasePermission):
    """Check if employee belongs to the organization"""
    def has_object_permission(self, request, view, obj):
        return (
            isinstance(request.user, Employee) and
            obj.organization == request.user.organization
        )

class CanManageEmployees(BasePermission):
    """Check if user can manage employees (AdminUser or Employee with admin role)"""
    def has_permission(self, request, view):
        if isinstance(request.user, AdminUser):
            return True
        if isinstance(request.user, Employee):
            return request.user.role == 'admin'
        return False
```

## Base de données

### Schema actuel

```sql
-- AdminUsers
admin_users (
    id UUID PK,
    email VARCHAR UNIQUE,
    password VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    is_active BOOLEAN,
    is_staff BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP NULL
)

-- Organizations
organizations (
    id UUID PK,
    name VARCHAR,
    subdomain VARCHAR UNIQUE,
    logo_url VARCHAR,
    category_id FK,
    admin_id FK -> admin_users,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP NULL
)

-- OrganizationSettings
organization_settings (
    id INTEGER PK,
    organization_id FK UNIQUE -> organizations,
    country VARCHAR,
    currency VARCHAR,
    theme VARCHAR,
    contact_email VARCHAR
)

-- Categories
categories (
    id INTEGER PK,
    name VARCHAR UNIQUE,
    description TEXT
)
```

### Schema futur

```sql
-- Employees (à ajouter)
employees (
    id UUID PK,
    organization_id FK -> organizations,
    email VARCHAR,
    password VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    employee_id VARCHAR,
    position VARCHAR,
    department VARCHAR,
    hire_date DATE,
    role VARCHAR,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    UNIQUE(email, organization_id)
)

-- EmployeePermissions
employee_permissions (
    id UUID PK,
    employee_id FK -> employees,
    permission_code VARCHAR,
    permission_name VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(employee_id, permission_code)
)
```

## Considérations de sécurité

### Actuelles

1. ✅ Passwords hashés (Django)
2. ✅ Token authentication
3. ✅ CORS configuré
4. ✅ CSRF protection
5. ✅ QuerySet filtering par user

### Futures

1. 🔜 Scoping obligatoire par organization pour employees
2. 🔜 Rate limiting sur endpoints d'auth
3. 🔜 Token expiration
4. 🔜 Refresh tokens
5. 🔜 Audit logging (qui a fait quoi, quand)
6. 🔜 2FA optionnel
7. 🔜 IP whitelisting par organization

## Migration vers Phase 2

### Checklist d'implémentation

Quand il sera temps d'implémenter les employés:

1. **Modèles** (`hr/models.py`)
   - [ ] Décommenter et adapter Employee model
   - [ ] Créer EmployeeManager
   - [ ] Créer EmployeePermission model
   - [ ] Migrations

2. **Serializers** (`hr/serializers.py`)
   - [ ] EmployeeSerializer
   - [ ] EmployeeLoginSerializer
   - [ ] EmployeeRegisterSerializer (utilisé par AdminUser)
   - [ ] EmployeePermissionSerializer

3. **Views** (`hr/views.py`)
   - [ ] EmployeeLoginView
   - [ ] EmployeeLogoutView
   - [ ] EmployeeMeView
   - [ ] EmployeeViewSet (CRUD, AdminUser only)

4. **Permissions** (`hr/permissions.py`)
   - [ ] IsAdminUser
   - [ ] IsEmployeeOfOrganization
   - [ ] CanManageEmployees

5. **URLs** (`hr/urls.py`)
   - [ ] /api/hr/auth/* endpoints
   - [ ] /api/hr/employees/* endpoints

6. **Tests**
   - [ ] Employee authentication tests
   - [ ] Organization scoping tests
   - [ ] Permission tests

7. **Documentation**
   - [ ] Mettre à jour API_DOCUMENTATION.md
   - [ ] Exemples d'utilisation
   - [ ] Guide de migration

## Notes importantes

1. **Ne pas utiliser le même modèle User**: AdminUser et Employee sont des entités distinctes avec des besoins différents
2. **Scoping obligatoire**: Toujours filtrer par organization pour les employees
3. **Endpoints séparés**: `/api/core/auth/` pour admins, `/api/hr/auth/` pour employees
4. **Email unique par organization**: Un même email peut exister dans plusieurs organizations
5. **Création d'employees**: Seulement par AdminUser, pas d'auto-inscription
