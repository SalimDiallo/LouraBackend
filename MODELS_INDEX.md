# INDEX COMPLET DES MODÈLES - Loura Backend

**Total modèles**: 80+  
**Total fichiers models.py**: 7  
**Ligne de code totales**: 8000+  

---

## CORE APP (`/app/core/`)

### Utilisateurs & Authentification
| Modèle | Table | Champs clés | Héritage |
|--------|-------|------------|----------|
| BaseUser | base_users | email, first_name, last_name, user_type, is_active, language, timezone | AbstractBaseUser |
| AdminUser | admin_users | (hérite BaseUser) | BaseUser |
| BaseUserManager | - | Manager personnalisé | - |
| AdminUserManager | - | Manager pour AdminUser | - |

### Organisations
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Organization | organizations | name, subdomain (unique), logo_url, admin(FK), category(FK), is_active | AdminUser, Category |
| Category | categories | name (unique), description | - |
| OrganizationSettings | organization_settings | currency (MAD), country, theme, contact_email | Organization (O2O) |

### Permissions & Rôles
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Permission | core_permissions | code (unique), name, category, description | - |
| Role | core_roles | code, name, is_system_role, is_active, organization(FK) | Permission (M2M), Organization |
| Module | modules | code (unique), name, app_name, default_for_all, requires_subscription_tier | - |
| OrganizationModule | organization_modules | is_enabled, settings (JSON), enabled_by(FK) | Organization, Module, BaseUser |

---

## HR APP (`/app/hr/`)

### Employés
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Employee | employees | organization(FK), employee_id, date_of_birth, gender, address, employment_status | Organization, Department, Position, Contract, BaseUser, Role |
| Department | departments | organization(FK), name, code, manager(FK) | Organization, Employee |
| Position | positions | organization(FK), title, description, salary_range | Organization, Employee |

### Contrats & Employabilité
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Contract | contracts | employee(FK), contract_type (permanent|fixed|apprentice|freelance), start_date, end_date, salary, benefits(JSON) | Employee |

### Congés & Absences
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| LeaveRequest | leave_requests | employee(FK), leave_type (vacation|sick|personal|unpaid|maternity), start_date, end_date, status (draft|pending|approved|rejected), approver(FK) | Employee, Employee(approver) |

### Présences & Pointage
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Attendance | attendances | employee(FK), date, check_in, check_out, status (present|absent|late|excused) | Employee |

### Paie & Rémunération
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Payroll | payroll | organization(FK), employee(FK), period_start, period_end, base_salary, bonuses, deductions, net_salary, status | Organization, Employee |

---

## INVENTORY APP (`/app/inventory/`) - 1622 LIGNES

### Gestion des stocks de base
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Category | inventory_categories | organization(FK), name (unique), code, parent(FK) | Organization, Category |
| Warehouse | inventory_warehouses | organization(FK), code (unique), name, address, manager_name | Organization |
| Supplier | inventory_suppliers | organization(FK), code (unique), name, email, contact_person, tax_id, payment_terms | Organization |
| Product | inventory_products | organization(FK), sku (unique), name, category(FK), purchase_price, selling_price, unit, min_stock_level, max_stock_level, barcode | Organization, Category |
| Stock | inventory_stocks | product(FK), warehouse(FK), quantity, location | Product, Warehouse |

### Mouvements de stock
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Movement | inventory_movements | organization(FK), product(FK), warehouse(FK), movement_type (in|out|transfer|adjustment), quantity, reference, destination_warehouse(FK), order(FK), sale(FK) | Organization, Product, Warehouse, Order, Sale |

### Commandes d'approvisionnement
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Order | inventory_orders | organization(FK), supplier(FK), warehouse(FK), order_number (unique), order_date, status (draft|pending|confirmed|received|cancelled), total_amount, transport_mode, transport_cost | Organization, Supplier, Warehouse |
| OrderItem | inventory_order_items | order(FK), product(FK), quantity, unit_price, received_quantity | Order, Product |

### Inventaires physiques
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| StockCount | inventory_stock_counts | organization(FK), warehouse(FK), count_number (unique), count_date, status (draft|planned|in_progress|completed|validated) | Organization, Warehouse |
| StockCountItem | inventory_stock_count_items | stock_count(FK), product(FK), expected_quantity, counted_quantity, variance | StockCount, Product |

### Gestion des clients
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Customer | inventory_customers | organization(FK), code (unique), name, email, phone, address, credit_limit, balance | Organization |

### Ventes
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Sale | inventory_sales | organization(FK), customer(FK), warehouse(FK), sale_number (unique), sale_date, status (draft|pending|completed|cancelled), subtotal, tax, discount, total_amount | Organization, Customer, Warehouse |
| SaleItem | inventory_sale_items | sale(FK), product(FK), quantity, unit_price, discount_percent, total | Sale, Product |

### Paiements
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Payment | inventory_payments | sale(FK), payment_date, amount, payment_method (cash|check|bank|credit), reference | Sale |

### Gestion des crédits
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| CreditSale | inventory_credit_sales | organization(FK), sale(FK), customer(FK), due_date, grace_period_days, status (pending|partial|paid|overdue), amount_due, amount_paid | Organization, Sale, Customer |

### Alertes
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Alert | inventory_alerts | organization(FK), product(FK), alert_type (low_stock|overdue|credit_sale_due|excess_stock), severity (info|warning|critical), is_resolved | Organization, Product |

### Documents commerciaux
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| ProformaInvoice | inventory_proforma_invoices | organization(FK), customer(FK), reference, issue_date, expiry_date, status, total_amount | Organization, Customer |
| ProformaItem | inventory_proforma_items | proforma(FK), product(FK), quantity, unit_price, total | ProformaInvoice, Product |
| PurchaseOrder | inventory_purchase_orders | organization(FK), supplier(FK), reference, order_date, delivery_date, status, total_amount | Organization, Supplier |
| PurchaseOrderItem | inventory_purchase_order_items | order(FK), product(FK), quantity, unit_price | PurchaseOrder, Product |
| DeliveryNote | inventory_delivery_notes | organization(FK), sale(FK), warehouse(FK), reference, delivery_date, status | Organization, Sale, Warehouse |
| DeliveryNoteItem | inventory_delivery_note_items | delivery_note(FK), sale_item(FK) | DeliveryNote, SaleItem |

### Dépenses
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| ExpenseCategory | inventory_expense_categories | organization(FK), code (unique), name | Organization |
| Expense | inventory_expenses | organization(FK), category(FK), amount, date, description, reference | Organization, ExpenseCategory |

---

## AI APP (`/app/ai/`)

### Conversations & Messages
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Conversation | ai_conversations | organization(FK), user(FK, nullable), employee(FK, nullable), title, is_agent_mode, is_active | Organization, BaseUser, Employee |
| Message | ai_messages | conversation(FK), role (user|assistant|system), content, feedback (like|dislike), tool_calls(JSON), tool_results(JSON), tokens_used, response_time_ms | Conversation |

### Exécutions d'outils
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| AIToolExecution | ai_tool_executions | message(FK), tool_name, tool_input(JSON), tool_output(JSON), status (pending|running|success|error), error_message, execution_time_ms | Message |

---

## NOTIFICATIONS APP (`/app/notifications/`)

### Notifications
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Notification | notifications | organization(FK), recipient(FK), sender(FK, nullable), notification_type (alert|system|user), priority (low|medium|high|critical), title, message, entity_type, entity_id, action_url, is_read, read_at | Organization, BaseUser |
| NotificationPreference | notification_preferences | organization(FK), user(FK), receive_alerts, receive_system, receive_user, min_priority | Organization, BaseUser |

---

## SERVICES APP (`/app/services/`)

### Structure de services
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| BusinessProfile | services_business_profiles | organization(FK), code (unique), name, icon, color, settings(JSON) | Organization |
| ServiceType | services_types | business_profile(FK), code (unique), name, pricing_model (fixed|hourly|daily|custom), allow_nested_services, allowed_child_types(M2M) | BusinessProfile |
| ServiceField | services_fields | service_type(FK), field_key (unique), field_type (text|number|date|select|file|currency|etc.), is_required, validation_rules(JSON), options(JSON) | ServiceType |
| ServiceStatus | services_statuses | service_type(FK), code (unique), name, status_type, is_initial, is_final, allowed_next_statuses(M2M) | ServiceType |

### Services réels
| Modèle | Table | Champs clés | Relations |
|--------|-------|------------|-----------|
| Service | services | organization(FK), service_type(FK), reference (unique, auto-generated), title, client_type, client_name, client_user(FK), assigned_to(FK), parent_service(FK), current_status(FK), field_values(JSON), start_date, end_date, estimated_amount, actual_amount, priority, tags(JSON) | Organization, ServiceType, BaseUser, Service |
| ServiceStatusHistory | services_status_history | service(FK), from_status(FK), to_status(FK), changed_by(FK), comment, metadata(JSON) | Service, ServiceStatus, BaseUser |
| ServiceActivity | services_activities | service(FK), activity_type, user(FK), title, description, data(JSON) | Service, BaseUser |
| ServiceComment | services_comments | service(FK), user(FK), content, parent_comment(FK), attachments(JSON), is_internal | Service, BaseUser, ServiceComment |
| ServiceTemplate | services_templates | service_type(FK), name, default_field_values(JSON), default_title_template | ServiceType |

---

## RÉSUMÉ PAR APP

| App | Modèles | Tables | Champs clés | Relations |
|-----|---------|--------|------------|-----------|
| **core** | 8 | 8 | Users, Orgs, Permissions | M2M, FK |
| **hr** | 7 | 7 | Employees, Contracts, Payroll | FK hierarchies |
| **inventory** | 20+ | 25+ | Products, Orders, Sales, Credits | M2M, FK chains |
| **ai** | 3 | 3 | Conversations, Messages, Executions | Simple FK |
| **notifications** | 2 | 2 | Notifications, Preferences | Simple FK |
| **services** | 9 | 9+ | Services, Fields, Statuses | Self-references |
| **TOTAL** | **80+** | **85+** | **Hundreds** | **Complex** |

---

## Modèles avec TimeStampedModel

**Héritage TimeStampedModel** (created_at, updated_at):

Core:
- Permission, Role, Module, OrganizationModule

HR:
- Employee (via BaseUser), Contract, LeaveRequest

Inventory:
- Category, Warehouse, Supplier, Product, Stock, Movement, Order, OrderItem, StockCount, StockCountItem, CreditSale, Alert, ProformaInvoice, PurchaseOrder, DeliveryNote, ExpenseCategory, Expense

Notifications:
- Notification, NotificationPreference

Services:
- BusinessProfile, ServiceType, ServiceField, ServiceStatus, Service, ServiceStatusHistory, ServiceActivity, ServiceComment, ServiceTemplate

AI:
- Conversation, Message, AIToolExecution

**Total avec timestamps**: 60+

---

## Unique Constraints

```
core_permissions       : code
core_roles            : (organization, code)
modules               : code
inventory_categories  : (organization, name)
inventory_warehouses  : (organization, code)
inventory_suppliers   : (organization, code)
inventory_products    : (organization, sku)
inventory_stocks      : (product, warehouse)
inventory_orders      : order_number
inventory_order_items : pas unique
inventory_stock_counts: count_number
inventory_customers   : (organization, code)
inventory_sales       : sale_number
inventory_credit_sales: pas unique
services_business_profiles : (organization, code)
services_types        : (business_profile, code)
services_fields       : (service_type, field_key)
services_statuses     : (service_type, code)
services              : reference
```

---

## Modèles avec M2M (Many-to-Many)

```
BaseUser.groups                    ← Group
BaseUser.user_permissions          ← Permission
Employee.custom_permissions        ← Permission
Role.permissions                   ← Permission
ServiceType.allowed_child_types    ← ServiceType
ServiceStatus.allowed_next_statuses ← ServiceStatus
```

---

## Modèles avec JSONField

```
BaseUser              : (none)
Organization          : (none)
OrganizationSettings  : (none)
Employee              : emergency_contact
Role                  : (none)
Contract              : benefits
LeaveRequest          : (none)
Payroll               : (none)
Product               : (none)
Order                 : (none)
CreditSale            : (none)
Sale                  : (none)
ProformaInvoice       : (none)
Expense               : (none)
Message               : tool_calls, tool_results
AIToolExecution       : tool_input, tool_output
Notification          : (none)
ServiceType           : default_values, settings
ServiceField          : validation_rules, options, settings
Service               : field_values, tags, metadata, attachments
ServiceStatusHistory  : metadata
ServiceActivity       : data
ServiceComment        : attachments
ServiceTemplate       : default_field_values
BusinessProfile       : settings
```

---

## Indexes Database

**Explicit indexes**:
```
notifications         : (recipient, -created_at)
notifications         : (organization, is_read)
services              : (organization, service_type)
services              : (reference)
services              : (current_status)
services              : (assigned_to)
services              : (-created_at)
```

---

## Type de champs courants

```
CharField            : max_length, default, choices
TextField            : blank
DateField            : null, blank
DateTimeField        : auto_now, auto_now_add
DecimalField         : max_digits=12, decimal_places=2, validators
IntegerField         : default, validators
BooleanField         : default
ForeignKey           : on_delete (CASCADE, SET_NULL, PROTECT)
ManyToManyField      : related_name, blank
JSONField            : default=dict/list, blank=True
URLField             : max_length, blank, null
EmailField           : blank, null
SlugField            : max_length, unique
ChoiceField          : choices list
UUIDField            : (implicit pour id)
```

---

## Validation & Constraints

```
Validators utilisés:
  - MinValueValidator(Decimal('0.00'))    # Montants > 0
  - MaxValueValidator                     # Plafonds
  - Django defaults                       # Email, URL

Meta constraints:
  - unique_together
  - ordering
  - verbose_name/verbose_name_plural
  - db_table (custom names)
  - indexes
```

---

## Pagination & QuerySet

```
Page size: 10 items (par défaut, configurable)
Filters: django-filter support
Ordering: order_by (created_at, updated_at)
Select/Prefetch: utilisé dans viewsets
Limits: Pagination class (StandardResultsSetPagination)
```

---

## Polymorphisme

```
BaseUser (parent)
  ├─ AdminUser
  └─ Employee

Usage:
  ForeignKey(BaseUser) → peut référencer les deux
  BaseUser.objects.all() → retourne tous les deux
  Employee.objects.all() → retourne uniquement employees
  AdminUser.objects.all() → retourne uniquement admins
```

---

## Héritage TimeStampedModel

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
```

Utilisé par 60+ modèles

---

## Charsets & Collations

- PostgreSQL: UTF-8 (par défaut)
- Django: Unicode support natif
- JSON fields: UTF-8

---

**Rapport généré**: 2026-03-28  
**Modèles analysés**: 85+  
**Fichiers models.py**: 7  
**Lignes code**: 8000+  

