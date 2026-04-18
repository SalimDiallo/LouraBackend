# Architecture Guidelines - Loura Backend

**Version**: 1.0  
**Last updated**: Avril 2026  
**Based on**: ARCHITECTURE_AUDIT.md

---

## For Developers: Rules to follow when adding new code

### Rule 1: No circular imports

**Before importing**, ask:
- Does module A import from module B?
- If yes, does module B import from module A?
- If yes → STOP, use dependency injection or abstraction

**Example of BAD**:
```python
# authentication/services.py
from hr.models import Employee  # ❌ auth depends on hr
# If hr/models.py ever imports from auth, we have a cycle
```

**Example of GOOD**:
```python
# authentication/services.py
class AuthenticationService:
    def __init__(self, employee_repo):  # ✓ Inject dependency
        self.employee_repo = employee_repo
    
    def authenticate_user(self, email, password):
        employee = self.employee_repo.get_by_email(email)
```

### Rule 2: ViewSets should be < 500 LOC

**If a ViewSet is > 500 LOC**:
1. Move business logic to a Service class
2. Move custom queries to Repository class
3. Keep ViewSet lean (just routing + permissions)

**Current violations**:
- hr/views.py: 3768 LOC (will be split)
- inventory/views.py: 4831 LOC (will be split)

### Rule 3: Never import models directly from other modules

**BAD**:
```python
# ai/tools/hr_tools.py
from hr.models import Employee  # ❌ Direct model access
def list_employees(org):
    return Employee.objects.filter(memberships__organization=org)
```

**GOOD**:
```python
# ai/tools/hr_tools.py
from hr.services import EmployeeService  # ✓ Via service
def list_employees(org):
    return EmployeeService.get_employees_for_organization(org)
```

### Rule 4: Use services for business logic

**Layers**:
```
Request
    ↓
ViewSet (routing + authentication)
    ↓
Service (business logic)
    ↓
Model (data)
```

**Never put business logic in ViewSet**:
```python
# ❌ BAD - Business logic in view
class LeaveRequestViewSet(viewsets.ModelViewSet):
    def approve(self, request, pk):
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.approved_at = timezone.now()
        leave.save()  # ← Business logic here
        
        # Send notification
        novu_service.trigger_workflow(...)  # ← Business logic here
        return Response(...)

# ✓ GOOD - Business logic in service
from hr.services import LeaveService

class LeaveRequestViewSet(viewsets.ModelViewSet):
    def approve(self, request, pk):
        leave = self.get_object()
        LeaveService.approve_leave_request(leave, request.user)
        return Response(...)
```

### Rule 5: Don't trigger notifications directly

**BAD**:
```python
# hr/views.py
novu_service.trigger_workflow('employee-created', ...)  # Direct call
```

**GOOD** (when implemented):
```python
# hr/views.py
from notifications.dispatcher import EventDispatcher
from notifications.events import EmployeeCreatedEvent

employee = Employee.objects.create(...)
EventDispatcher.dispatch(EmployeeCreatedEvent(employee))  # ✓ Decoupled
```

### Rule 6: Models should be < 500 LOC

**If models.py > 500 LOC**:
1. Split by domain: employees.py, leaves.py, payroll.py, etc.
2. Use abstract base classes if shared
3. Import with `from .employees import Employee`

**Current violations**:
- hr/models.py: 1470 LOC
- inventory/models.py: 1622 LOC

### Rule 7: Serializers should be < 1000 LOC

**If serializers.py > 1000 LOC**:
1. Group by entity: employee_serializers.py, leave_serializers.py
2. Use inheritance for common fields
3. Use SerializerMethodField for complex logic

**Current violations**:
- hr/serializers.py: 1796 LOC
- inventory/serializers.py: 1286 LOC

### Rule 8: Tests before implementation

**When adding a feature**:
1. Write test first (TDD)
2. Test imports the service/repository
3. Ensure coverage > 80%

```python
# Tests should NOT test views directly
# Tests should test services

def test_leave_service_approve_leave_request():
    # Arrange
    employee = create_employee()
    leave = create_leave_request(employee)
    approver = create_manager()
    
    # Act
    LeaveService.approve_leave_request(leave, approver)
    
    # Assert
    assert leave.status == 'approved'
    assert leave.approved_by == approver
```

### Rule 9: Use mixins for common patterns

**DO** reuse mixins:
```python
# core/mixins.py
class BaseOrganizationViewSetMixin:
    def get_organization_from_request(self):
        ...

class OrganizationQuerySetMixin:
    def get_queryset(self):
        ...
```

**DON'T** repeat code:
```python
# ❌ BAD - duplicating get_queryset logic
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        org = self.get_organization_from_request()
        return Employee.objects.filter(organization=org)

class DepartmentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        org = self.get_organization_from_request()
        return Department.objects.filter(organization=org)

# ✓ GOOD - use mixin
class EmployeeViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    pass

class DepartmentViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    pass
```

### Rule 10: Document public APIs

**Every service method must have docstring**:
```python
class EmployeeService:
    @staticmethod
    def create_employee(organization, email, password, first_name, last_name, **kwargs):
        """
        Crée un nouvel employé.
        
        Args:
            organization (Organization): L'organisation
            email (str): Email unique par organisation
            password (str): Mot de passe en clair (sera hashé)
            first_name (str): Prénom
            last_name (str): Nom
            **kwargs: Autres champs (department, position, etc.)
        
        Returns:
            Employee: L'employé créé
        
        Raises:
            ValidationError: Si email existe déjà pour cette organisation
        
        Example:
            employee = EmployeeService.create_employee(
                organization=org,
                email='john@example.com',
                password='secure_password',
                first_name='John',
                last_name='Doe',
                department=dept
            )
        """
        ...
```

---

## Code Review Checklist

**Before approving a PR**, check:

### Structure
- [ ] ViewSets < 500 LOC each
- [ ] Models < 500 LOC
- [ ] Serializers < 1000 LOC
- [ ] Services used for business logic (not views)
- [ ] No direct model imports from other modules

### Dependencies
- [ ] No new circular imports introduced
- [ ] No hardcoded model imports (use services)
- [ ] No direct novu_service calls (use EventDispatcher)
- [ ] Only core, own module, and services imported

### Quality
- [ ] All tests passing (pytest)
- [ ] Coverage maintained (≥ 80%)
- [ ] No linting errors (flake8)
- [ ] Type hints present for public methods
- [ ] Docstrings for services/utils

### Non-regression
- [ ] API contracts unchanged
- [ ] Database migrations in place
- [ ] No breaking changes to permissions
- [ ] Multi-tenant isolation maintained

### Git
- [ ] Meaningful commit messages
- [ ] Related issues linked
- [ ] No merge conflict markers
- [ ] Rebased on main branch

---

## Module dependency rules

### Allowed imports

```
auth     → core ✓
hr       → core, auth, services ✓
inventory → core, services ✓
ai       → core, services ✓
notif    → core ✓
services → core ✓
```

### Forbidden imports

```
auth ← hr ✗
auth ← inventory ✗
auth ← ai ✗
auth ← notif ✗

hr ← inventory ✗ (except core.mixins)
hr ← ai ✗
hr ← notif ✗ (use EventDispatcher)

inventory ← ai ✗
inventory ← notif ✗ (use EventDispatcher)

ai ← notif ✗

notif ← hr ✗ (use EventDispatcher)
notif ← inventory ✗ (use EventDispatcher)
notif ← ai ✗
```

### How to check

```bash
# List imports from other modules
grep -r "from [auth|hr|inventory|ai|notif]\." app/[module]/ | grep -v __pycache__

# If adding new import, verify it's allowed
```

---

## Service Layer Pattern

### When to create a Service

**Signals**:
- Multiple ViewSets doing same operation
- Business logic > 3 lines
- External API calls (novu, stripe, etc.)
- Database transactions
- Complex queries

### Service structure

```python
# hr/services/employee_service.py
class EmployeeService:
    """Service for employee-related operations"""
    
    @staticmethod
    def create_employee(organization, **kwargs):
        """Create a new employee"""
        # Validation
        # Database operations
        # Event dispatch
        # Return result
        pass
    
    @staticmethod
    def activate_employee(employee):
        """Activate an employee"""
        pass
    
    @staticmethod
    def get_subordinates(employee):
        """Get direct reports"""
        pass
```

### ViewSet using Service

```python
# hr/views/employee.py
class EmployeeViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Delegate to service
        employee = EmployeeService.create_employee(
            organization=self.get_organization_from_request(),
            **serializer.validated_data
        )
        
        return Response(
            EmployeeSerializer(employee).data,
            status=status.HTTP_201_CREATED
        )
```

---

## Event Bus Pattern (when implemented)

### Define an event

```python
# notifications/events.py
class Event(ABC):
    pass

class EmployeeCreatedEvent(Event):
    def __init__(self, employee):
        self.employee = employee
```

### Dispatch event

```python
# hr/services/employee_service.py
from notifications.dispatcher import EventDispatcher
from notifications.events import EmployeeCreatedEvent

class EmployeeService:
    @staticmethod
    def create_employee(organization, **kwargs):
        employee = Employee.objects.create(...)
        EventDispatcher.dispatch(EmployeeCreatedEvent(employee))  # ← Dispatch
        return employee
```

### Handle event

```python
# notifications/handlers.py
from notifications.dispatcher import EventDispatcher
from notifications.events import EmployeeCreatedEvent
from .novu_service import novu_service

def on_employee_created(event: EmployeeCreatedEvent):
    novu_service.trigger_workflow(
        'employee-welcome',
        subscriber_id=str(event.employee.id),
        payload={'name': event.employee.full_name}
    )

# Subscribe
EventDispatcher.subscribe(EmployeeCreatedEvent, on_employee_created)
```

---

## File organization template

### For a new module `newapp`

```
newapp/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── entity1.py     (< 300 LOC)
│   ├── entity2.py     (< 300 LOC)
│   └── entity3.py     (< 300 LOC)
├── serializers/
│   ├── __init__.py
│   ├── entity1_serializers.py
│   ├── entity2_serializers.py
│   └── entity3_serializers.py
├── services/
│   ├── __init__.py
│   ├── entity1_service.py
│   ├── entity2_service.py
│   └── entity3_service.py
├── views/
│   ├── __init__.py
│   ├── entity1.py     (EmployeeViewSet, DepartmentViewSet)
│   ├── entity2.py     (PayrollViewSet)
│   └── entity3.py     (AttendanceViewSet)
├── repositories.py    (optional, if complex queries)
├── permissions.py     (< 200 LOC)
├── urls.py
├── admin.py
└── tests/
    ├── __init__.py
    ├── test_entity1.py
    ├── test_entity2.py
    ├── test_entity3.py
    └── test_services.py
```

---

## Common mistakes to avoid

### ❌ Mistake 1: Business logic in ViewSet

```python
# hr/views.py
class PayslipViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Calculate gross salary ← WRONG
        gross = request.data['base_salary'] * 12
        # Calculate taxes ← WRONG
        taxes = gross * 0.25
        # Create payslip ← WRONG
        payslip = Payslip.objects.create(gross=gross, taxes=taxes)
```

### ✓ Solution: Use Service

```python
# hr/services/payroll_service.py
class PayrollService:
    @staticmethod
    def create_payslip(employee, period):
        gross = PayrollService._calculate_gross(employee, period)
        taxes = PayrollService._calculate_taxes(gross)
        return Payslip.objects.create(gross=gross, taxes=taxes)

# hr/views/payroll.py
class PayslipViewSet:
    def create(self, request):
        payslip = PayrollService.create_payslip(...)
        return Response(...)
```

### ❌ Mistake 2: N+1 queries

```python
# hr/views.py
employees = Employee.objects.all()
for emp in employees:
    print(emp.department.name)  # ← N+1: query for each employee!
```

### ✓ Solution: Use select_related/prefetch_related

```python
# hr/views.py or hr/services/employee_service.py
employees = Employee.objects.select_related('department')  # 1 query
for emp in employees:
    print(emp.department.name)  # No extra queries
```

### ❌ Mistake 3: Hardcoded config

```python
# hr/tasks.py
def process_payroll():
    TAX_RATE = 0.25  # ❌ Hardcoded
    TAX_BRACKETS = {...}  # ❌ Hardcoded
```

### ✓ Solution: Use settings

```python
# lourabackend/settings.py
PAYROLL_CONFIG = {
    'TAX_RATE': 0.25,
    'TAX_BRACKETS': {...}
}

# hr/tasks.py
from django.conf import settings

def process_payroll():
    TAX_RATE = settings.PAYROLL_CONFIG['TAX_RATE']
```

### ❌ Mistake 4: No error handling

```python
# ai/tools/hr_tools.py
def list_employees(organization):
    employees = Employee.objects.filter(...)
    return [{'name': e.full_name, ...} for e in employees]  # What if error?
```

### ✓ Solution: Add error handling

```python
# ai/tools/hr_tools.py
def list_employees(organization):
    try:
        employees = Employee.objects.filter(...)
        return {
            'status': 'success',
            'employees': [...]
        }
    except Exception as e:
        logger.error(f"Error listing employees: {e}")
        return {
            'status': 'error',
            'message': 'Could not list employees'
        }
```

---

## Testing guidelines

### Unit tests (test services)

```python
# hr/tests/test_employee_service.py
class EmployeeServiceTests(TestCase):
    def test_create_employee_success(self):
        org = create_organization()
        employee = EmployeeService.create_employee(
            organization=org,
            email='test@example.com',
            password='secure',
            first_name='John',
            last_name='Doe'
        )
        assert employee.email == 'test@example.com'
        assert employee.organization == org
    
    def test_create_employee_duplicate_email(self):
        org = create_organization()
        create_employee(org, email='test@example.com')
        
        with pytest.raises(ValidationError):
            EmployeeService.create_employee(
                organization=org,
                email='test@example.com',
                ...
            )
```

### Integration tests (test viewsets)

```python
# hr/tests/test_employee_views.py
class EmployeeViewSetTests(APITestCase):
    def test_create_employee_endpoint(self):
        org = create_organization()
        client = APIClient()
        client.force_authenticate(user=create_admin(org))
        
        response = client.post('/api/hr/employees/', {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'secure'
        })
        
        assert response.status_code == 201
        assert Employee.objects.filter(email='test@example.com').exists()
```

---

## Documentation

Every service should have:

```python
class EmployeeService:
    """
    Service pour les opérations métier sur les employés.
    
    Responsabilités:
    - Création et suppression d'employés
    - Activation/déactivation
    - Attribution de rôles et permissions
    - Statistiques sur les employés
    
    Utilisé par:
    - hr/views/employee.py (ViewSet)
    - ai/tools/hr_tools.py (AI tools) - quand implémenté
    - hr/tasks.py (Celery tasks)
    - Tests
    
    Example:
        employee = EmployeeService.create_employee(
            organization=org,
            email='john@example.com',
            password='secure',
            first_name='John',
            last_name='Doe'
        )
    """
    pass
```

---

## Refactoring roadmap

### ✅ Phase 1 (Week 1)
- [ ] Split hr/views.py into 8 files
- [ ] Move PDFGeneratorMixin to core

### ⏳ Phase 2 (Week 2-3)
- [ ] Decouple auth from hr
- [ ] Create service wrappers for AI tools

### ⏳ Phase 3 (Week 4-5)
- [ ] Implement Event Bus
- [ ] Consolidate Permission/Role

### ⏳ Phase 4 (Week 6+)
- [ ] Full service layer integration
- [ ] Split inventory/views.py

---

## Quick reference

### Allowed imports by module

```python
# In authentication/
from core import models, mixins, permissions  ✓
from authentication import services, views    ✓
from django_packages import ...                ✓

# In hr/
from core import models, mixins, permissions  ✓
from hr import models, services, views         ✓
from authentication import services            ✓

# In inventory/
from core import models, mixins, permissions  ✓
from inventory import models, services, views  ✓

# In ai/
from core import models, mixins                ✓
from hr.services import EmployeeService       ✓ (not models!)
from inventory.services import ...            ✓ (not models!)

# In notifications/
from core import models                       ✓
from django.db.models.signals import ...      ✓
```

---

**Last updated**: Avril 2026  
**Maintainer**: Architecture Team  
**Questions?**: See ARCHITECTURE_AUDIT.md for detailed analysis
