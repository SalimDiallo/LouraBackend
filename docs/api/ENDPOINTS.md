# API Endpoints - Loura Backend

## Base URL

- **Development** : `http://localhost:8000/api/`
- **Production** : `https://your-domain.com/api/`

---

## Authentication Endpoints

**Base** : `/api/auth/`

| Méthode | URL | Description | Permission | Body |
|---------|-----|-------------|------------|------|
| POST | `/auth/login/` | Connexion (Admin/Employee) | AllowAny | `{email, password}` |
| POST | `/auth/register/` | Inscription Admin | AllowAny | `{email, password, first_name, last_name, organization:{name, subdomain}}` |
| POST | `/auth/refresh/` | Refresh access token | AllowAny | Cookie `refresh_token` |
| POST | `/auth/logout/` | Déconnexion | IsAuthenticated | Cookie `refresh_token` |
| GET | `/auth/me/` | Utilisateur courant | IsAuthenticated | - |
| PATCH | `/auth/profile/` | Mettre à jour profil | IsAuthenticated | `{first_name, last_name, phone, ...}` |
| POST | `/auth/change-password/` | Changer mot de passe | IsAuthenticated | `{old_password, new_password, confirm_password}` |

---

## Core Endpoints

**Base** : `/api/core/`

### Organizations

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/core/organizations/` | Liste organisations (admin) | IsAdminUser | - |
| GET | `/core/organizations/{id}/` | Détail organisation | IsAdminUser | - |
| POST | `/core/organizations/` | Créer organisation | IsAdminUser | `{name, subdomain, category}` |
| PUT | `/core/organizations/{id}/` | Modifier organisation | IsAdminUser | `{name, logo, ...}` |
| DELETE | `/core/organizations/{id}/` | Supprimer organisation | IsAdminUser | - |

### Modules

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/core/modules/` | Liste modules disponibles | IsAuthenticated | - |
| GET | `/core/modules/{id}/` | Détail module | IsAuthenticated | - |
| POST | `/core/organization-modules/` | Activer module | IsAdminUser | `{organization, module, is_enabled}` |
| PUT | `/core/organization-modules/{id}/` | Toggle module | IsAdminUser | `{is_enabled}` |

### Roles & Permissions

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/core/roles/` | Liste rôles | IsAuthenticated | `?organization=uuid` |
| POST | `/core/roles/` | Créer rôle | IsAdminUser | `{organization, code, name, permissions:[]}` |
| PUT | `/core/roles/{id}/` | Modifier rôle | IsAdminUser | `{name, permissions:[]}` |
| DELETE | `/core/roles/{id}/` | Supprimer rôle | IsAdminUser | - |
| GET | `/core/permissions/` | Liste permissions | IsAuthenticated | `?category=hr` |

---

## HR Endpoints

**Base** : `/api/hr/`

### Employees

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/employees/` | Liste employés | `hr.view_employees` | `?organization=uuid&department=uuid&employment_status=active` |
| GET | `/hr/employees/{id}/` | Détail employé | `hr.view_employees` | - |
| POST | `/hr/employees/` | Créer employé | `hr.create_employees` | `{email, first_name, last_name, organization, department, position, hire_date}` |
| PUT | `/hr/employees/{id}/` | Modifier employé | `hr.update_employees` | - |
| DELETE | `/hr/employees/{id}/` | Supprimer employé | `hr.delete_employees` | - |
| POST | `/hr/employees/{id}/activate/` | Activer employé | `hr.update_employees` | - |

### Departments

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/departments/` | Liste départements | `hr.view_departments` | `?organization=uuid` |
| POST | `/hr/departments/` | Créer département | `hr.create_departments` | `{organization, name, code, head}` |
| PUT | `/hr/departments/{id}/` | Modifier département | `hr.update_departments` | - |
| DELETE | `/hr/departments/{id}/` | Supprimer département | `hr.delete_departments` | - |

### Positions

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/positions/` | Liste postes | `hr.view_positions` | `?organization=uuid` |
| POST | `/hr/positions/` | Créer poste | `hr.create_positions` | `{organization, title, min_salary, max_salary}` |
| PUT | `/hr/positions/{id}/` | Modifier poste | `hr.update_positions` | - |
| DELETE | `/hr/positions/{id}/` | Supprimer poste | `hr.delete_positions` | - |

### Contracts

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/contracts/` | Liste contrats | `hr.view_contracts` | `?employee=uuid&is_active=true` |
| POST | `/hr/contracts/` | Créer contrat | `hr.create_contracts` | `{employee, contract_type, start_date, base_salary, is_active}` |
| PUT | `/hr/contracts/{id}/` | Modifier contrat | `hr.update_contracts` | - |
| POST | `/hr/contracts/{id}/activate/` | Activer contrat | `hr.update_contracts` | - |

### Leave Management

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/leave-types/` | Liste types de congés | `hr.view_leave_requests` | `?organization=uuid` |
| POST | `/hr/leave-types/` | Créer type congé | `hr.create_leave_requests` | `{organization, name, default_days_per_year, is_paid}` |
| GET | `/hr/leave-requests/` | Liste demandes | `hr.view_leave_requests` | `?employee=uuid&status=pending` |
| POST | `/hr/leave-requests/` | Créer demande | `hr.create_leave_requests` | `{employee, leave_type, start_date, end_date, total_days, reason}` |
| POST | `/hr/leave-requests/{id}/approve/` | Approuver | `hr.approve_leave_requests` | `{approval_notes}` |
| POST | `/hr/leave-requests/{id}/reject/` | Rejeter | `hr.approve_leave_requests` | `{approval_notes}` |
| GET | `/hr/leave-balances/` | Soldes congés | `hr.view_leave_requests` | `?employee=uuid&year=2025` |
| POST | `/hr/leave-balances/initialize/` | Initialiser solde | `hr.create_leave_requests` | `{employee, year, allocated_days}` |

### Payroll

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/payroll-periods/` | Liste périodes paie | `hr.view_payroll` | `?organization=uuid&status=approved` |
| POST | `/hr/payroll-periods/` | Créer période | `hr.create_payroll` | `{organization, name, start_date, end_date}` |
| GET | `/hr/payslips/` | Liste fiches de paie | `hr.view_payroll` | `?employee=uuid&payroll_period=uuid&status=paid` |
| POST | `/hr/payslips/` | Créer fiche | `hr.create_payroll` | `{employee, base_salary, items:[{name, amount, is_deduction}]}` |
| GET | `/hr/payslips/{id}/pdf/` | Générer PDF | `hr.view_payroll` | - |
| POST | `/hr/payroll-advances/` | Demander avance | `hr.create_payroll` | `{employee, amount, reason}` |
| POST | `/hr/payroll-advances/{id}/approve/` | Approuver avance | `hr.approve_payroll` | - |

### Attendance

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/hr/attendances/` | Liste pointages | `hr.view_attendance` | `?user=uuid&date=2025-01-15&organization=uuid` |
| POST | `/hr/attendances/check-in/` | Check-in | `hr.create_attendance` | `{location, notes}` |
| POST | `/hr/attendances/check-out/` | Check-out | `hr.create_attendance` | `{location, notes}` |
| POST | `/hr/attendances/start-break/` | Pause début | `hr.create_attendance` | - |
| POST | `/hr/attendances/end-break/` | Pause fin | `hr.create_attendance` | - |
| POST | `/hr/attendances/{id}/approve/` | Approuver | `hr.approve_attendance` | - |
| POST | `/hr/qr-sessions/` | Créer session QR | `hr.create_qr_session` | `{organization, employee, mode, expires_at}` |
| POST | `/hr/qr-sessions/scan/` | Scanner QR | AllowAny | `{session_token, action}` |

---

## Inventory Endpoints

**Base** : `/api/inventory/`

### Products

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/products/` | Liste produits | `inventory.view_products` | `?organization=uuid&category=uuid&search=laptop` |
| GET | `/inventory/products/{id}/` | Détail produit | `inventory.view_products` | - |
| POST | `/inventory/products/` | Créer produit | `inventory.create_products` | `{organization, category, name, sku, purchase_price, selling_price, unit}` |
| PUT | `/inventory/products/{id}/` | Modifier produit | `inventory.update_products` | - |
| DELETE | `/inventory/products/{id}/` | Supprimer produit | `inventory.delete_products` | - |
| GET | `/inventory/products/{id}/stock-levels/` | Niveaux de stock | `inventory.view_products` | - |

### Stock & Warehouses

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/warehouses/` | Liste entrepôts | `inventory.view_warehouses` | `?organization=uuid` |
| POST | `/inventory/warehouses/` | Créer entrepôt | `inventory.create_warehouses` | `{organization, name, code, address}` |
| GET | `/inventory/stocks/` | Stock par entrepôt | `inventory.view_stock` | `?product=uuid&warehouse=uuid` |
| POST | `/inventory/stocks/adjust/` | Ajuster stock | `inventory.update_stock` | `{product, warehouse, quantity, reason}` |
| GET | `/inventory/movements/` | Mouvements stock | `inventory.view_movements` | `?product=uuid&movement_type=in&date__gte=2025-01-01` |
| POST | `/inventory/movements/` | Créer mouvement | `inventory.create_movements` | `{product, warehouse, movement_type, quantity}` |

### Sales

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/sales/` | Liste ventes | `inventory.view_sales` | `?organization=uuid&customer=uuid&payment_status=paid&date__gte=2025-01-01` |
| GET | `/inventory/sales/{id}/` | Détail vente | `inventory.view_sales` | - |
| POST | `/inventory/sales/` | Créer vente | `inventory.create_sales` | `{organization, customer, warehouse, items:[{product, quantity, unit_price, discount_value}]}` |
| GET | `/inventory/sales/{id}/receipt-pdf/` | Reçu PDF | `inventory.view_sales` | - |
| POST | `/inventory/sales/{id}/send-email/` | Envoyer par email | `inventory.view_sales` | `{email}` |
| GET | `/inventory/sales/stats/` | Statistiques ventes | `inventory.view_sales` | `?organization=uuid&start_date=2025-01-01&end_date=2025-01-31` |

### Orders (Purchase)

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/orders/` | Liste commandes | `inventory.view_orders` | `?organization=uuid&supplier=uuid&status=pending` |
| POST | `/inventory/orders/` | Créer commande | `inventory.create_orders` | `{organization, supplier, warehouse, items:[{product, quantity, unit_price}]}` |
| POST | `/inventory/orders/{id}/receive/` | Réceptionner | `inventory.update_orders` | `{items:[{product, received_quantity}]}` |
| POST | `/inventory/orders/{id}/cancel/` | Annuler | `inventory.update_orders` | - |

### Customers & Suppliers

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/customers/` | Liste clients | `inventory.view_customers` | `?organization=uuid&search=name` |
| POST | `/inventory/customers/` | Créer client | `inventory.create_customers` | `{organization, name, code, email, phone, credit_limit}` |
| GET | `/inventory/suppliers/` | Liste fournisseurs | `inventory.view_suppliers` | `?organization=uuid` |
| POST | `/inventory/suppliers/` | Créer fournisseur | `inventory.create_suppliers` | `{organization, name, code, email, phone, address}` |

### Credit Sales

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/credit-sales/` | Liste créances | `inventory.view_credit_sales` | `?organization=uuid&status=overdue&customer=uuid` |
| POST | `/inventory/credit-sales/` | Créer créance | `inventory.create_credit_sales` | `{sale, customer, total_amount, due_date, grace_period_days}` |
| POST | `/inventory/credit-sales/{id}/record-payment/` | Enregistrer paiement | `inventory.update_credit_sales` | `{amount, payment_method, payment_date}` |

### Payments & Expenses

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/inventory/payments/` | Liste paiements | `inventory.view_payments` | `?sale=uuid&date__gte=2025-01-01` |
| POST | `/inventory/payments/` | Créer paiement | `inventory.create_payments` | `{sale, amount, payment_method, reference}` |
| GET | `/inventory/expenses/` | Liste dépenses | `inventory.view_expenses` | `?organization=uuid&category=uuid` |
| POST | `/inventory/expenses/` | Créer dépense | `inventory.create_expenses` | `{organization, category, description, amount, expense_date, payment_method}` |

---

## Notifications Endpoints

**Base** : `/api/notifications/`

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| GET | `/notifications/` | Liste notifications | IsAuthenticated | `?is_read=false&organization=uuid` |
| GET | `/notifications/{id}/` | Détail notification | IsAuthenticated | - |
| POST | `/notifications/{id}/mark-as-read/` | Marquer lue | IsAuthenticated | - |
| POST | `/notifications/mark-all-as-read/` | Tout marquer lu | IsAuthenticated | - |
| GET | `/notifications/unread-count/` | Compteur non lues | IsAuthenticated | `?organization=uuid` |
| GET | `/notifications/preferences/` | Préférences | IsAuthenticated | - |
| PUT | `/notifications/preferences/` | Modifier préférences | IsAuthenticated | `{receive_alerts, receive_system, min_priority}` |

---

## AI Assistant Endpoints

**Base** : `/api/ai/`

| Méthode | URL | Description | Permission | Query Params |
|---------|-----|-------------|------------|--------------|
| POST | `/ai/chat/` | Conversation AI | IsAuthenticated | `{message, organization, context:{}}` |
| GET | `/ai/suggestions/` | Suggestions AI | IsAuthenticated | `?organization=uuid&type=sales` |

---

## Notes

- Tous les endpoints nécessitent authentification sauf `/auth/login/` et `/auth/register/`
- Les permissions sont vérifiées via `BaseCRUDPermission` ou permissions custom
- AdminUser bypass toutes les permissions
- Filtrer par `organization` pour isolation multi-tenant
- Pagination : 10 résultats par défaut, max 100

---

**Références** :
- **DRF Routers** : https://www.django-rest-framework.org/api-guide/routers/
- **DRF ViewSets** : https://www.django-rest-framework.org/api-guide/viewsets/
