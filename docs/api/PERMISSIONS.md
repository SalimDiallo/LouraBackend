# Permissions - Loura Backend

## Système de permissions

Loura utilise un système de permissions granulaires avec 3 niveaux :
1. **Permissions Django** (système)
2. **Permissions custom** (modèle `Permission`)
3. **Rôles** (groupement de permissions)

**Voir** : `app/core/permissions.py`

---

## Classes de permission DRF

### IsAuthenticated

Vérifie que l'utilisateur est authentifié.

```python
from core.permissions import IsAuthenticated

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
```

---

### IsAdminUser

Vérifie que l'utilisateur est un AdminUser.

```python
from core.permissions import IsAdminUser

class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
```

---

### IsEmployeeUser

Vérifie que l'utilisateur est un Employee.

```python
from core.permissions import IsEmployeeUser

class AttendanceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsEmployeeUser]
```

---

### BaseCRUDPermission

Génère automatiquement les permissions CRUD selon l'action.

```python
from core.permissions import BaseCRUDPermission

class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [BaseCRUDPermission]
    permission_prefix = 'hr'
    permission_resource = 'employees'

    # Permissions générées :
    # - list/retrieve: hr.view_employees
    # - create: hr.create_employees
    # - update: hr.update_employees
    # - destroy: hr.delete_employees
```

---

### IsOrganizationMember

Vérifie que l'utilisateur appartient à l'organisation.

```python
from core.permissions import IsOrganizationMember

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOrganizationMember, BaseCRUDPermission]
```

---

## Permissions par application

### Core Permissions

| Code | Nom | Description |
|------|-----|-------------|
| `core.view_organizations` | View Organizations | Voir les organisations |
| `core.create_organizations` | Create Organizations | Créer organisations |
| `core.update_organizations` | Update Organizations | Modifier organisations |
| `core.delete_organizations` | Delete Organizations | Supprimer organisations |
| `core.view_roles` | View Roles | Voir les rôles |
| `core.create_roles` | Create Roles | Créer rôles |
| `core.update_roles` | Update Roles | Modifier rôles |
| `core.delete_roles` | Delete Roles | Supprimer rôles |
| `core.view_modules` | View Modules | Voir modules |
| `core.manage_modules` | Manage Modules | Gérer modules |

---

### HR Permissions

| Code | Nom | Description |
|------|-----|-------------|
| `hr.view_employees` | View Employees | Voir employés |
| `hr.create_employees` | Create Employees | Créer employés |
| `hr.update_employees` | Update Employees | Modifier employés |
| `hr.delete_employees` | Delete Employees | Supprimer employés |
| `hr.view_departments` | View Departments | Voir départements |
| `hr.create_departments` | Create Departments | Créer départements |
| `hr.update_departments` | Update Departments | Modifier départements |
| `hr.delete_departments` | Delete Departments | Supprimer départements |
| `hr.view_positions` | View Positions | Voir postes |
| `hr.create_positions` | Create Positions | Créer postes |
| `hr.update_positions` | Update Positions | Modifier postes |
| `hr.delete_positions` | Delete Positions | Supprimer postes |
| `hr.view_contracts` | View Contracts | Voir contrats |
| `hr.create_contracts` | Create Contracts | Créer contrats |
| `hr.update_contracts` | Update Contracts | Modifier contrats |
| `hr.delete_contracts` | Delete Contracts | Supprimer contrats |
| `hr.view_leave_requests` | View Leave Requests | Voir demandes de congé |
| `hr.create_leave_requests` | Create Leave Requests | Créer demandes |
| `hr.approve_leave_requests` | Approve Leave Requests | Approuver demandes |
| `hr.view_payroll` | View Payroll | Voir paie |
| `hr.create_payroll` | Create Payroll | Créer paie |
| `hr.update_payroll` | Update Payroll | Modifier paie |
| `hr.export_payroll` | Export Payroll | Exporter paie |
| `hr.view_attendance` | View Attendance | Voir pointages |
| `hr.view_all_attendance` | View All Attendance | Voir tous les pointages |
| `hr.create_attendance` | Create Attendance | Pointer |
| `hr.update_attendance` | Update Attendance | Modifier pointages |
| `hr.approve_attendance` | Approve Attendance | Approuver pointages |
| `hr.manual_checkin` | Manual Check-in | Pointer manuellement |
| `hr.create_qr_session` | Create QR Session | Créer session QR |

---

### Inventory Permissions

| Code | Nom | Description |
|------|-----|-------------|
| `inventory.view_products` | View Products | Voir produits |
| `inventory.create_products` | Create Products | Créer produits |
| `inventory.update_products` | Update Products | Modifier produits |
| `inventory.delete_products` | Delete Products | Supprimer produits |
| `inventory.view_stock` | View Stock | Voir stock |
| `inventory.update_stock` | Update Stock | Modifier stock |
| `inventory.view_movements` | View Movements | Voir mouvements |
| `inventory.create_movements` | Create Movements | Créer mouvements |
| `inventory.view_warehouses` | View Warehouses | Voir entrepôts |
| `inventory.create_warehouses` | Create Warehouses | Créer entrepôts |
| `inventory.update_warehouses` | Update Warehouses | Modifier entrepôts |
| `inventory.delete_warehouses` | Delete Warehouses | Supprimer entrepôts |
| `inventory.view_sales` | View Sales | Voir ventes |
| `inventory.create_sales` | Create Sales | Créer ventes |
| `inventory.update_sales` | Update Sales | Modifier ventes |
| `inventory.delete_sales` | Delete Sales | Supprimer ventes |
| `inventory.view_orders` | View Orders | Voir commandes |
| `inventory.create_orders` | Create Orders | Créer commandes |
| `inventory.update_orders` | Update Orders | Modifier commandes |
| `inventory.delete_orders` | Delete Orders | Supprimer commandes |
| `inventory.view_customers` | View Customers | Voir clients |
| `inventory.create_customers` | Create Customers | Créer clients |
| `inventory.update_customers` | Update Customers | Modifier clients |
| `inventory.delete_customers` | Delete Customers | Supprimer clients |
| `inventory.view_suppliers` | View Suppliers | Voir fournisseurs |
| `inventory.create_suppliers` | Create Suppliers | Créer fournisseurs |
| `inventory.update_suppliers` | Update Suppliers | Modifier fournisseurs |
| `inventory.delete_suppliers` | Delete Suppliers | Supprimer fournisseurs |
| `inventory.view_credit_sales` | View Credit Sales | Voir créances |
| `inventory.create_credit_sales` | Create Credit Sales | Créer créances |
| `inventory.update_credit_sales` | Update Credit Sales | Modifier créances |
| `inventory.view_payments` | View Payments | Voir paiements |
| `inventory.create_payments` | Create Payments | Créer paiements |
| `inventory.view_expenses` | View Expenses | Voir dépenses |
| `inventory.create_expenses` | Create Expenses | Créer dépenses |

---

## Matrice de permissions par endpoint

### HR Employees

| Endpoint | Méthode | Permission requise | AdminUser | Employee |
|----------|---------|-------------------|-----------|----------|
| `/hr/employees/` | GET | `hr.view_employees` | ✅ | ✅ (avec permission) |
| `/hr/employees/` | POST | `hr.create_employees` | ✅ | ✅ (avec permission) |
| `/hr/employees/{id}/` | PUT | `hr.update_employees` | ✅ | ✅ (avec permission) |
| `/hr/employees/{id}/` | DELETE | `hr.delete_employees` | ✅ | ✅ (avec permission) |

### Inventory Sales

| Endpoint | Méthode | Permission requise | AdminUser | Employee |
|----------|---------|-------------------|-----------|----------|
| `/inventory/sales/` | GET | `inventory.view_sales` | ✅ | ✅ (avec permission) |
| `/inventory/sales/` | POST | `inventory.create_sales` | ✅ | ✅ (avec permission) |
| `/inventory/sales/{id}/receipt-pdf/` | GET | `inventory.view_sales` | ✅ | ✅ (avec permission) |

---

## Rôles prédéfinis

### Super Admin

**Code** : `super_admin`

**Permissions** : TOUTES les permissions de l'organisation

---

### HR Manager

**Code** : `hr_manager`

**Permissions** :
- `hr.view_employees`
- `hr.create_employees`
- `hr.update_employees`
- `hr.view_departments`
- `hr.create_departments`
- `hr.view_leave_requests`
- `hr.approve_leave_requests`
- `hr.view_payroll`
- `hr.create_payroll`
- `hr.view_all_attendance`
- `hr.approve_attendance`

---

### Employee (Base)

**Code** : `employee`

**Permissions** :
- `hr.view_employees` (limité)
- `hr.view_leave_requests` (ses demandes)
- `hr.create_leave_requests`
- `hr.view_attendance` (ses pointages)
- `hr.create_attendance`

---

### Inventory Manager

**Code** : `inventory_manager`

**Permissions** :
- `inventory.view_products`
- `inventory.create_products`
- `inventory.update_products`
- `inventory.view_stock`
- `inventory.update_stock`
- `inventory.view_sales`
- `inventory.create_sales`
- `inventory.view_orders`
- `inventory.create_orders`

---

### Sales Agent

**Code** : `sales_agent`

**Permissions** :
- `inventory.view_products`
- `inventory.view_customers`
- `inventory.create_customers`
- `inventory.view_sales`
- `inventory.create_sales`

---

## Ajouter une nouvelle permission

### 1. Créer la permission en DB

```python
from core.models import Permission

Permission.objects.create(
    code='myapp.my_action',
    name='My Action',
    category='myapp',
    description='Permission to perform my action'
)
```

---

### 2. Utiliser dans une vue

```python
from core.permissions import BaseCRUDPermission

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [BaseCRUDPermission]
    permission_prefix = 'myapp'
    permission_resource = 'myresource'
```

---

### 3. Pour action custom

```python
from core.permissions import require_permission

@action(detail=True, methods=['post'])
@require_permission('myapp.my_action')
def my_custom_action(self, request, pk=None):
    # Code
    pass
```

---

## Vérifier une permission (code)

### AdminUser

```python
if request.user.user_type == 'admin':
    # Admin a toutes les permissions
    return True
```

---

### Employee

```python
if request.user.has_permission('hr.view_employees'):
    # Employee a la permission
    return True
```

---

## Références

- **Permissions System** : `app/core/models.py` (Permission, Role)
- **Permission Classes** : `app/core/permissions.py`
- **Employee.has_permission()** : `app/hr/models.py` (lignes 170-231)
