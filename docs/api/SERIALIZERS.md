# Serializers - Loura Backend

## Introduction

Les serializers DRF transforment les modèles Django en JSON et vice-versa.

**Localisation** : `app/*/serializers.py`

---

## Authentication Serializers

**Fichier** : `app/authentication/serializers.py`

### UnifiedLoginSerializer
```python
{
  "email": "admin@example.com",
  "password": "password123"
}
```

### AdminRegistrationSerializer
```python
{
  "email": "admin@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "organization": {
    "name": "My Company",
    "subdomain": "mycompany"
  }
}
```

### AdminUserResponseSerializer / EmployeeUserResponseSerializer
```python
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "admin",
  "phone": "+1234567890",
  "avatar_url": "https://...",
  "organization": {...},  # Pour Employee
  "organizations": [...],  # Pour Admin
  "permissions": ["hr.view_employees", ...],
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

---

## Core Serializers

**Fichier** : `app/core/serializers.py`

### OrganizationSerializer
```python
{
  "id": "uuid",
  "name": "My Company",
  "subdomain": "mycompany",
  "logo_url": "https://...",
  "category": {
    "id": "uuid",
    "name": "Retail"
  },
  "admin": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John"
  },
  "is_active": true,
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

### RoleSerializer
```python
{
  "id": "uuid",
  "organization": "uuid",
  "code": "hr_manager",
  "name": "HR Manager",
  "description": "Manages HR operations",
  "permissions": [
    {"id": "uuid", "code": "hr.view_employees", "name": "View Employees"},
    {"id": "uuid", "code": "hr.create_employees", "name": "Create Employees"}
  ],
  "is_system_role": false,
  "is_active": true
}
```

### PermissionSerializer
```python
{
  "id": "uuid",
  "code": "hr.view_employees",
  "name": "View Employees",
  "category": "hr",
  "description": "Permission to view employee list"
}
```

---

## HR Serializers

**Fichier** : `app/hr/serializers.py`

### EmployeeSerializer
```python
{
  "id": "uuid",
  "email": "employee@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1234567890",
  "avatar_url": null,
  "user_type": "employee",
  "employee_id": "EMP-001",
  "date_of_birth": "1990-05-15",
  "gender": "female",
  "address": "123 Main St",
  "city": "New York",
  "country": "USA",
  "organization": {
    "id": "uuid",
    "name": "My Company"
  },
  "department": {
    "id": "uuid",
    "name": "IT"
  },
  "position": {
    "id": "uuid",
    "title": "Developer"
  },
  "contract": {
    "id": "uuid",
    "contract_type": "permanent",
    "base_salary": 5000.00
  },
  "assigned_role": {
    "id": "uuid",
    "name": "Employee"
  },
  "hire_date": "2023-01-15",
  "employment_status": "active",
  "is_active": true
}
```

### ContractSerializer
```python
{
  "id": "uuid",
  "employee": {
    "id": "uuid",
    "first_name": "Jane",
    "last_name": "Smith"
  },
  "contract_type": "permanent",
  "start_date": "2023-01-15",
  "end_date": null,
  "base_salary": 5000.00,
  "currency": "USD",
  "salary_period": "monthly",
  "hours_per_week": 40,
  "is_active": true
}
```

### LeaveRequestSerializer
```python
{
  "id": "uuid",
  "employee": {...},
  "leave_type": {
    "id": "uuid",
    "name": "Annual Leave",
    "is_paid": true
  },
  "title": "Summer Vacation",
  "start_date": "2025-07-01",
  "end_date": "2025-07-15",
  "start_half_day": false,
  "end_half_day": false,
  "total_days": 10,
  "reason": "Family vacation",
  "status": "pending",
  "approver": null,
  "approval_date": null
}
```

### PayslipSerializer
```python
{
  "id": "uuid",
  "employee": {...},
  "payroll_period": {
    "id": "uuid",
    "name": "January 2025"
  },
  "description": "Paie Janvier 2025",
  "base_salary": 5000.00,
  "gross_salary": 5200.00,
  "total_deductions": 700.00,
  "net_salary": 4500.00,
  "currency": "USD",
  "items": [
    {
      "id": "uuid",
      "name": "Transport Allowance",
      "amount": 200.00,
      "is_deduction": false
    },
    {
      "id": "uuid",
      "name": "Tax",
      "amount": 700.00,
      "is_deduction": true
    }
  ],
  "status": "approved",
  "payment_date": "2025-02-01"
}
```

### AttendanceSerializer
```python
{
  "id": "uuid",
  "user": {...},
  "organization": {...},
  "date": "2025-01-15",
  "check_in": "2025-01-15T08:30:00Z",
  "check_in_location": "Office",
  "check_out": "2025-01-15T17:45:00Z",
  "check_out_location": "Office",
  "breaks": [
    {
      "id": "uuid",
      "start_time": "2025-01-15T12:00:00Z",
      "end_time": "2025-01-15T13:00:00Z",
      "duration_minutes": 60
    }
  ],
  "total_hours": 8.25,
  "break_duration": 1.00,
  "status": "present",
  "approval_status": "approved",
  "is_overtime": true,
  "overtime_hours": 0.25
}
```

---

## Inventory Serializers

**Fichier** : `app/inventory/serializers.py`

### ProductSerializer
```python
{
  "id": "uuid",
  "organization": "uuid",
  "category": {
    "id": "uuid",
    "name": "Electronics"
  },
  "name": "Laptop HP",
  "sku": "LAP-HP-001",
  "description": "HP Laptop 15.6 inch",
  "purchase_price": 500.00,
  "selling_price": 750.00,
  "unit": "unit",
  "min_stock_level": 5,
  "max_stock_level": 50,
  "barcode": "1234567890123",
  "image_url": "https://...",
  "is_active": true,
  "total_stock": 25  # Calculé
}
```

### StockSerializer
```python
{
  "id": "uuid",
  "product": {...},
  "warehouse": {
    "id": "uuid",
    "name": "Main Warehouse",
    "code": "WH-01"
  },
  "quantity": 25,
  "location": "A-12-03"
}
```

### SaleSerializer
```python
{
  "id": "uuid",
  "organization": "uuid",
  "customer": {
    "id": "uuid",
    "name": "John Doe",
    "code": "CUST-001"
  },
  "warehouse": {...},
  "sale_number": "SALE-2025-001",
  "sale_date": "2025-01-15T14:30:00Z",
  "subtotal": 1500.00,
  "discount_type": "percentage",
  "discount_value": 10,
  "discount_amount": 150.00,
  "tax_rate": 18,
  "tax_amount": 243.00,
  "total_amount": 1593.00,
  "paid_amount": 1593.00,
  "payment_status": "paid",
  "payment_method": "cash",
  "items": [
    {
      "id": "uuid",
      "product": {...},
      "quantity": 2,
      "unit_price": 750.00,
      "discount_type": "fixed",
      "discount_value": 0,
      "discount_amount": 0,
      "total": 1500.00
    }
  ],
  "is_credit_sale": false
}
```

### OrderSerializer (Purchase)
```python
{
  "id": "uuid",
  "organization": "uuid",
  "supplier": {
    "id": "uuid",
    "name": "Tech Supplies Inc",
    "code": "SUP-001"
  },
  "warehouse": {...},
  "order_number": "PO-2025-001",
  "order_date": "2025-01-10",
  "expected_delivery_date": "2025-01-20",
  "actual_delivery_date": null,
  "status": "pending",
  "total_amount": 5000.00,
  "items": [
    {
      "id": "uuid",
      "product": {...},
      "quantity": 10,
      "unit_price": 500.00,
      "received_quantity": 0
    }
  ],
  "transport_mode": "routier",
  "transport_company": "DHL",
  "tracking_number": "DHL123456789",
  "transport_cost": 100.00
}
```

### CustomerSerializer
```python
{
  "id": "uuid",
  "organization": "uuid",
  "name": "John Doe",
  "code": "CUST-001",
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "country": "USA",
  "credit_limit": 10000.00,
  "is_active": true,
  "total_debt": 2500.00  # Calculé
}
```

### CreditSaleSerializer
```python
{
  "id": "uuid",
  "organization": "uuid",
  "sale": {...},
  "customer": {...},
  "total_amount": 1500.00,
  "paid_amount": 500.00,
  "remaining_amount": 1000.00,
  "due_date": "2025-02-15",
  "grace_period_days": 7,
  "status": "partial",
  "last_reminder_date": "2025-01-10",
  "reminder_count": 2
}
```

---

## Validation Rules

### Common Validators

- **Email** : Format RFC 5322
- **Phone** : Non validé (libre)
- **Dates** : Format ISO 8601 (YYYY-MM-DD)
- **Decimals** : Max 2 décimales
- **UUID** : Format UUID4
- **Prices** : >= 0

### Custom Validators

```python
# Exemple dans SaleSerializer
def validate(self, data):
    # Vérifier stock disponible
    for item in data['items']:
        stock = Stock.objects.get(
            product=item['product'],
            warehouse=data['warehouse']
        )
        if stock.quantity < item['quantity']:
            raise ValidationError(
                f"Stock insuffisant pour {item['product'].name}"
            )
    return data
```

---

## Nested Serializers

### Read-only nested

```python
class EmployeeSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
```

### Write avec PrimaryKeyRelatedField

```python
class EmployeeSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all()
    )
```

---

## Références

- **DRF Serializers** : https://www.django-rest-framework.org/api-guide/serializers/
- **Field Types** : https://www.django-rest-framework.org/api-guide/fields/
