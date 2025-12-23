# Architecture Microservices et Design Patterns

## Vue d'ensemble

Cette architecture applique les principes suivants :
- **Microservices** : Chaque app Django est un microservice indépendant
- **Single Responsibility Principle (SRP)** : Chaque classe/module a une seule responsabilité
- **Service Layer Pattern** : Logique métier séparée des vues
- **Mixin Pattern** : Code réutilisable entre ViewSets
- **Strategy Pattern** : Comportement différent selon le type d'utilisateur
- **Template Method Pattern** : Structure commune avec points d'extension

## Structure des Apps

```
app/
├── authentication/          # 🔐 Microservice Authentication
│   ├── __init__.py         # Documentation et configuration
│   ├── permissions.py      # Permissions de base (IsAdminUser, IsEmployee, etc.)
│   ├── utils.py            # Utilitaires centralisés (JWT cookies, tokens)
│   ├── views.py            # Vues d'authentification
│   └── serializers.py      # Serializers de login
│
├── core/                   # 🏢 Microservice Core (Organizations)
│   ├── mixins.py           # Mixins réutilisables par toutes les apps
│   ├── services/           # Service Layer
│   │   ├── __init__.py
│   │   └── organization_service.py
│   ├── models.py           # AdminUser, Organization, Category
│   └── views.py            # ViewSets Core
│
├── hr/                     # 👥 Microservice RH
│   ├── mixins.py           # Mixins spécifiques HR
│   ├── services/           # Service Layer HR
│   │   ├── __init__.py
│   │   ├── employee_service.py
│   │   ├── leave_service.py
│   │   └── payroll_service.py
│   ├── views.py            # ViewSets existants
│   ├── views_refactored.py # ViewSets refactorés (exemples)
│   └── permissions.py      # Permissions HR
│
└── lourabackend/           # Configuration Django
```

## Design Patterns Implémentés

### 1. Service Layer Pattern

**Objectif** : Séparer la logique métier des vues pour :
- Réutilisabilité (Celery tasks, management commands, tests)
- Testabilité (tests unitaires sans HTTP)
- Maintenabilité (changements isolés)

**Utilisation** :
```python
# Dans une vue
from hr.services import EmployeeService

class EmployeeViewSet(viewsets.ModelViewSet):
    @action(detail=False)
    def stats(self, request):
        stats = EmployeeService.get_employee_stats(organization)
        return Response(stats)

# Dans une tâche Celery
from hr.services import LeaveService

@celery_app.task
def send_leave_reminders():
    for org in Organization.objects.all():
        pending = LeaveService.get_pending_requests_for_organization(org)
        # ...

# Dans un test
from hr.services import EmployeeService

def test_create_employee():
    employee = EmployeeService.create_employee(
        organization=org,
        email='test@test.com',
        password='testpass',
        first_name='Test',
        last_name='User'
    )
    assert employee.is_active
```

### 2. Mixin Pattern (BaseOrganizationViewSetMixin)

**Objectif** : Éliminer le code dupliqué dans les ViewSets.

**Avant** (code dupliqué dans chaque ViewSet) :
```python
class DepartmentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        if isinstance(user, AdminUser):
            org_subdomain = self.request.query_params.get('organization_subdomain')
            if org_subdomain:
                try:
                    organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                    # ... 30+ lignes de code répétées
```

**Après** (utilisation du mixin) :
```python
from core.mixins import BaseOrganizationViewSetMixin

class DepartmentViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    
    # Configuration simple
    organization_field = 'organization'
    view_permission = 'can_view_department'
    create_permission = 'can_create_department'
```

### 3. Strategy Pattern (Résolution d'Organisation)

**Objectif** : Comportement différent selon le type d'utilisateur.

```python
class OrganizationResolverMixin:
    def get_organization_from_request(self):
        if isinstance(user, AdminUser):
            # Stratégie Admin : lit depuis query params ou data
            return self._resolve_organization_for_admin(user)
        elif isinstance(user, Employee):
            # Stratégie Employee : utilise son organisation
            return self._resolve_organization_for_employee(user)
```

### 4. Template Method Pattern

**Objectif** : Structure commune avec points d'extension.

```python
class OrganizationQuerySetMixin:
    def get_queryset(self):  # Template Method
        base_queryset = self.get_base_queryset()  # Point d'extension
        return self._filter_by_organization(base_queryset)
    
    def get_base_queryset(self):  # Hook pour les sous-classes
        return super().get_queryset()
```

## Guide de Migration

### Étape 1 : Migrer vers les Services

1. Identifier la logique métier dans les vues
2. Créer les méthodes correspondantes dans le service
3. Remplacer le code dans les vues par des appels au service

**Exemple** :
```python
# Avant (dans la vue)
def approve(self, request, pk=None):
    leave_request = self.get_object()
    leave_request.status = 'approved'
    leave_request.approval_date = timezone.now()
    # ... logique de mise à jour du solde
    leave_request.save()

# Après (dans la vue)
def approve(self, request, pk=None):
    leave_request = self.get_object()
    LeaveService.approve_leave_request(leave_request, request.user)
    return Response({'message': 'Approuvé'})
```

### Étape 2 : Utiliser les Mixins

1. Identifier les ViewSets avec get_queryset/perform_create répétitifs
2. Hériter de `BaseOrganizationViewSetMixin`
3. Configurer via les attributs de classe

**Exemple** :
```python
# Avant
class PositionViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        user = self.request.user
        # ... 20 lignes de code

# Après
class PositionViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    queryset = Position.objects.all()
    view_permission = 'can_view_position'
```

### Étape 3 : Tester

```python
# tests/test_services/test_employee_service.py
from hr.services import EmployeeService

class TestEmployeeService:
    def test_create_employee(self):
        employee = EmployeeService.create_employee(
            organization=self.org,
            email='new@test.com',
            password='password',
            first_name='New',
            last_name='Employee'
        )
        assert employee.email == 'new@test.com'
        assert employee.organization == self.org
```

## Indépendance des Microservices

### Règles d'Import

1. **authentication** → N'importe de personne
2. **core** → N'importe que de authentication
3. **hr** → Importe de core et authentication

```python
# ✅ Correct
# hr/services/employee_service.py
from core.models import Organization

# ❌ Incorrect
# core/services/organization_service.py
from hr.models import Employee  # Dépendance circulaire!
```

### Communication Inter-Services

Pour les besoins de communication, utiliser :
1. **Lazy imports** : `from hr.models import Employee` dans les méthodes
2. **Interfaces/Protocols** : (pour Python 3.8+)
3. **Events/Signals** : Pour notifications découpées

## Avantages de cette Architecture

| Aspect | Avant | Après |
|--------|-------|-------|
| Lignes de code par ViewSet | ~150-200 | ~50-80 |
| Code dupliqué | ~40% | ~5% |
| Testabilité | Difficile | Facile |
| Réutilisabilité | Faible | Élevée |
| Évolutivité | Complexe | Simple |

## Fichiers Clés

| Fichier | Responsabilité |
|---------|----------------|
| `core/mixins.py` | Mixins de base réutilisables |
| `core/services/organization_service.py` | Logique métier organisations |
| `hr/mixins.py` | Mixins spécifiques HR |
| `hr/services/employee_service.py` | Logique métier employés |
| `hr/services/leave_service.py` | Logique métier congés |
| `hr/services/payroll_service.py` | Logique métier paie |
| `hr/views_refactored.py` | Exemples de ViewSets refactorés |

## Prochaines Étapes

1. **Migration progressive** : Remplacer les ViewSets un par un
2. **Tests unitaires** : Ajouter des tests pour les services
3. **Documentation API** : Mettre à jour la documentation
4. **Monitoring** : Ajouter des métriques par service
