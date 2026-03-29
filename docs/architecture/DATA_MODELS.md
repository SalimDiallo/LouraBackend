# Data Models - Loura Backend

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Schéma des relations principales](#schéma-des-relations-principales)
3. [Modèles par application](#modèles-par-application)
4. [Relations inter-applications](#relations-inter-applications)
5. [Patterns de conception](#patterns-de-conception)
6. [Contraintes et validations](#contraintes-et-validations)
7. [Index et optimisations](#index-et-optimisations)

---

## Vue d'ensemble

Le projet Loura compte **55+ modèles** répartis sur 6 applications Django principales :

| Application   | Nombre de modèles | Description                                  |
|---------------|-------------------|----------------------------------------------|
| **core**      | 9                 | Organisation, Utilisateurs, Permissions, Modules |
| **hr**        | 15                | Employés, Contrats, Congés, Paie, Pointage  |
| **inventory** | 25                | Produits, Stock, Ventes, Commandes, Clients |
| **notifications** | 2             | Notifications internes                       |
| **authentication** | 0            | Sérializers et vues uniquement              |
| **ai**        | 0                 | Services IA (pas de modèles DB)              |

**Total** : ~55 modèles actifs

---

## Schéma des relations principales

```
┌────────────────────────────────────────────────────────────────────┐
│                      CORE MODELS (Base)                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐                                             │
│  │  Organization    │ ◄──────┐                                     │
│  │  (Tenant)        │        │                                     │
│  └─────┬────────────┘        │                                     │
│        │                     │                                     │
│        │ Has                 │ Belongs to                          │
│        │                     │                                     │
│  ┌─────▼────────────┐  ┌────┴────────────┐                        │
│  │  BaseUser        │  │  Module         │                        │
│  │  (Abstract)      │  │  (Features)     │                        │
│  └─────┬────────────┘  └─────────────────┘                        │
│        │                                                           │
│   ┌────┴────┐                                                      │
│   │         │                                                      │
│  ┌▼────────▼┐      ┌──────────────┐                               │
│  │AdminUser │      │  Employee    │ ◄──┐                          │
│  │(Owner)   │      │  (User)      │    │                          │
│  └──────────┘      └──────┬───────┘    │                          │
│                           │            │                          │
│                     ┌─────▼─────┐      │                          │
│                     │   Role    │      │                          │
│                     │(Permissions)     │                          │
│                     └───────────┘      │                          │
│                                        │                          │
└────────────────────────────────────────┼──────────────────────────┘
                                         │
┌────────────────────────────────────────┼──────────────────────────┐
│                      HR MODELS         │                          │
├────────────────────────────────────────┼──────────────────────────┤
│                                        │                          │
│  ┌──────────────────────────────────┐  │                          │
│  │         Employee                 │──┘                          │
│  │  ├─ Department                   │                             │
│  │  ├─ Position                     │                             │
│  │  ├─ Contract (1:1 active)        │                             │
│  │  └─ Assigned Role                │                             │
│  └─────┬────────────────────────────┘                             │
│        │                                                           │
│   ┌────┴─────┬──────────┬────────────┬────────────┐               │
│   │          │          │            │            │               │
│  ┌▼──────┐  ┌▼──────┐  ┌▼──────┐   ┌▼────────┐  ┌▼──────┐        │
│  │Contract│  │Leave  │  │Payslip│   │Attendance│ │Advance│        │
│  │        │  │Request│  │       │   │          │ │       │        │
│  └────────┘  └───────┘  └───────┘   └──────────┘ └───────┘        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                   INVENTORY MODELS                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │  Category    │      │  Product     │      │  Supplier    │    │
│  └──────────────┘      └──────┬───────┘      └──────────────┘    │
│                               │                                   │
│                         ┌─────┴─────┬──────────┬────────────┐     │
│                         │           │          │            │     │
│                    ┌────▼────┐  ┌───▼────┐  ┌─▼─────┐  ┌───▼───┐ │
│                    │  Stock  │  │  Sale  │  │ Order │  │Movement│ │
│                    │(Whse)   │  │        │  │       │  │        │ │
│                    └─────────┘  └────┬───┘  └───────┘  └────────┘ │
│                                      │                             │
│                                 ┌────▼────────┐                    │
│                                 │ SaleItem    │                    │
│                                 │ (Line)      │                    │
│                                 └─────────────┘                    │
│                                                                    │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │  Customer    │      │ CreditSale   │      │  Payment     │    │
│  └──────────────┘      └──────────────┘      └──────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                  NOTIFICATIONS MODELS                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────┐                                   │
│  │     Notification           │                                   │
│  │  ├─ recipient (BaseUser)   │                                   │
│  │  ├─ sender (BaseUser)      │                                   │
│  │  └─ entity_type/entity_id  │                                   │
│  └────────────────────────────┘                                   │
│                                                                    │
│  ┌────────────────────────────┐                                   │
│  │ NotificationPreference     │                                   │
│  │  (User settings)           │                                   │
│  └────────────────────────────┘                                   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Modèles par application

### 1. Core (9 modèles)

**Fichier** : `app/core/models.py`

#### BaseUser (Modèle parent abstrait)
- **Héritage** : `AbstractBaseUser`, `PermissionsMixin`, `TimeStampedModel`
- **Champs principaux** : `email`, `first_name`, `last_name`, `user_type`, `is_active`
- **Relations** : Base pour `AdminUser` et `Employee`
- **Ligne** : 46-149

#### AdminUser (Administrateur)
- **Héritage** : `BaseUser`
- **Rôle** : Propriétaire d'organisations
- **Relations** : `organizations` (Many via ForeignKey), `created_qr_sessions`
- **Ligne** : 241-264

#### Organization (Tenant)
- **Champs** : `name`, `subdomain`, `logo`, `category`, `admin`, `is_active`
- **Relations** :
  - `admin` → AdminUser
  - `employees` → Employee
  - `departments`, `products`, `sales`, etc.
- **Ligne** : 266-305

#### OrganizationSettings
- **Relation** : OneToOne avec Organization
- **Champs** : `country`, `currency`, `theme`, `contact_email`
- **Ligne** : 306-326

#### Category (Catégorie d'organisation)
- **Champs** : `name`, `description`
- **Usage** : Classifier les organisations (Restaurant, Retail, etc.)
- **Ligne** : 211-224

#### Permission (Permission granulaire)
- **Champs** : `code`, `name`, `category`, `description`
- **Usage** : Système de permissions personnalisé
- **Ligne** : 155-171

#### Role (Rôle avec permissions)
- **Relations** :
  - `organization` (FK)
  - `permissions` (M2M)
- **Champs** : `code`, `name`, `is_system_role`, `is_active`
- **Ligne** : 173-205

#### Module (Fonctionnalité activable)
- **Champs** : `code`, `name`, `app_name`, `icon`, `category`
- **Usage** : Activer/désactiver modules par organisation
- **Ligne** : 332-423

#### OrganizationModule (Relation M2M)
- **Relations** : `organization`, `module`
- **Champs** : `is_enabled`, `settings`, `enabled_by`
- **Ligne** : 425-476

---

### 2. HR - Gestion RH (15 modèles)

**Fichier** : `app/hr/models.py`

#### Employee (Employé)
- **Héritage** : `BaseUser`
- **Relations** :
  - `organization` (FK - required)
  - `department` (FK - optional)
  - `position` (FK - optional)
  - `contract` (FK - current active)
  - `manager` (FK - BaseUser)
  - `assigned_role` (FK - Role)
  - `custom_permissions` (M2M - Permission)
- **Champs uniques** : `employee_id`, `date_of_birth`, `gender`, `address`, `hire_date`, `employment_status`
- **Ligne** : 47-255

#### Department (Département)
- **Relations** :
  - `organization` (FK)
  - `head` (FK - BaseUser)
  - `parent_department` (FK - self, hiérarchique)
- **Ligne** : 261-305

#### Position (Poste)
- **Relations** : `organization` (FK)
- **Champs** : `title`, `code`, `min_salary`, `max_salary`
- **Ligne** : 307-337

#### Contract (Contrat de travail)
- **Relations** : `employee` (FK)
- **Champs** : `contract_type`, `start_date`, `end_date`, `base_salary`, `currency`, `salary_period`, `hours_per_week`
- **Règle métier** : Un seul contrat actif par employé (logique dans `save()`)
- **Ligne** : 339-459

#### LeaveType (Type de congé)
- **Relations** : `organization` (FK)
- **Champs** : `name`, `default_days_per_year`, `is_paid`, `requires_approval`, `color`
- **Ligne** : 465-492

#### LeaveRequest (Demande de congé)
- **Relations** :
  - `employee` (FK)
  - `leave_type` (FK)
  - `approver` (FK - BaseUser)
- **Champs** : `start_date`, `end_date`, `start_half_day`, `end_half_day`, `total_days`, `status`, `reason`
- **Ligne** : 494-542

#### LeaveBalance (Solde de congés)
- **Relations** : `employee` (FK)
- **Champs** : `year`, `allocated_days`
- **Propriétés calculées** : `used_days`, `pending_days`, `remaining_days`
- **Contrainte** : Unique (employee, year)
- **Ligne** : 544-709

#### PayrollPeriod (Période de paie)
- **Relations** : `organization` (FK)
- **Champs** : `name`, `start_date`, `end_date`, `payment_date`, `status`
- **Ligne** : 715-744

#### Payslip (Fiche de paie)
- **Relations** :
  - `employee` (FK)
  - `payroll_period` (FK - optional)
- **Champs** : `base_salary`, `gross_salary`, `total_deductions`, `net_salary`, `status`, `payment_date`
- **Ligne** : 746-832

#### PayslipItem (Ligne de fiche de paie)
- **Relations** : `payslip` (FK)
- **Champs** : `name`, `amount`, `is_deduction`
- **Ligne** : 834-850

#### PayrollAdvance (Avance sur salaire)
- **Relations** :
  - `employee` (FK)
  - `approved_by` (FK - BaseUser)
  - `payslip` (FK - optional)
- **Champs** : `amount`, `reason`, `status`, `payment_date`, `deduction_month`
- **Ligne** : 852-896

#### Attendance (Pointage)
- **Relations** :
  - `user` (FK - BaseUser)
  - `organization` (FK)
  - `approved_by` (FK - BaseUser)
- **Champs** : `date`, `check_in`, `check_out`, `break_start`, `break_end`, `total_hours`, `status`, `approval_status`
- **Contrainte** : Unique (organization, user, date)
- **Ligne** : 902-1043

#### Break (Pause)
- **Relations** : `attendance` (FK)
- **Champs** : `start_time`, `end_time`, `notes`
- **Ligne** : 1046-1079

#### QRCodeSession (Session QR pour pointage)
- **Relations** :
  - `organization` (FK)
  - `employee` (FK - optional)
  - `allowed_employees` (M2M)
  - `created_by` (FK - AdminUser)
- **Champs** : `session_token`, `expires_at`, `is_active`, `mode`
- **Ligne** : 1085-1150

---

### 3. Inventory - Gestion Stock (25 modèles)

**Fichier** : `app/inventory/models.py`

#### Category (Catégorie de produits)
- **Relations** : `organization`, `parent` (self)
- **Ligne** : 15-44

#### Warehouse (Entrepôt)
- **Relations** : `organization`
- **Champs** : `name`, `code`, `address`, `city`, `manager_name`, `phone`
- **Ligne** : 51-78

#### Supplier (Fournisseur)
- **Relations** : `organization`
- **Champs** : `name`, `code`, `email`, `phone`, `address`, `tax_id`, `payment_terms`
- **Ligne** : 85-117

#### Product (Produit)
- **Relations** : `organization`, `category`
- **Champs** : `name`, `sku`, `purchase_price`, `selling_price`, `unit`, `min_stock_level`, `max_stock_level`, `barcode`
- **Méthodes** : `get_total_stock()`, `is_low_stock()`
- **Ligne** : 124-213

#### Stock (Quantité par entrepôt)
- **Relations** : `product`, `warehouse`
- **Champs** : `quantity`, `location`
- **Contrainte** : Unique (product, warehouse)
- **Ligne** : 219-250

#### Movement (Mouvement de stock)
- **Relations** : `organization`, `product`, `warehouse`, `destination_warehouse`, `order`, `sale`
- **Types** : `in`, `out`, `transfer`, `adjustment`
- **Ligne** : 256-329

#### Order (Commande d'approvisionnement)
- **Relations** : `organization`, `supplier`, `warehouse`
- **Champs** : `order_number`, `order_date`, `expected_delivery_date`, `status`, `total_amount`
- **Transport** : `transport_mode`, `transport_company`, `tracking_number`, `transport_cost`
- **Ligne** : 335-440

#### OrderItem (Ligne de commande)
- **Relations** : `order`, `product`
- **Champs** : `quantity`, `unit_price`, `received_quantity`
- **Ligne** : 442-485

#### StockCount (Inventaire physique)
- **Relations** : `organization`, `warehouse`
- **Champs** : `count_number`, `count_date`, `status`
- **Ligne** : 491-527

#### StockCountItem (Ligne d'inventaire)
- **Relations** : `stock_count`, `product`
- **Champs** : `expected_quantity`, `counted_quantity`
- **Méthode** : `get_difference()`
- **Ligne** : 529-570

#### Alert (Alerte de stock)
- **Relations** : `organization`, `product`, `warehouse`
- **Types** : `stock_warning`, `low_stock`, `out_of_stock`, `overstock`, `high_value_low_stock`, `no_movement`, `expiring_soon`
- **Ligne** : 576-628

#### Customer (Client)
- **Relations** : `organization`
- **Champs** : `name`, `code`, `email`, `phone`, `address`, `tax_id`, `credit_limit`
- **Méthode** : `get_total_debt()`
- **Ligne** : 640-687

#### Sale (Vente)
- **Relations** : `organization`, `customer`, `warehouse`
- **Champs avec remises** : `subtotal`, `discount_type`, `discount_value`, `discount_amount`, `tax_rate`, `tax_amount`, `total_amount`, `paid_amount`
- **Méthode** : `calculate_totals()`
- **Ligne** : 693-859

#### SaleItem (Ligne de vente)
- **Relations** : `sale`, `product`
- **Champs** : `quantity`, `unit_price`, `discount_type`, `discount_value`, `discount_amount`, `total`
- **Ligne** : 861-939

#### Payment (Paiement/Reçu)
- **Relations** : `organization`, `sale`
- **Champs** : `receipt_number`, `payment_date`, `amount`, `payment_method`, `customer_name`, `is_credit_payment`
- **Ligne** : 945-1001

#### ExpenseCategory (Catégorie de dépense)
- **Relations** : `organization`
- **Ligne** : 1007-1029

#### Expense (Dépense)
- **Relations** : `organization`, `category`
- **Champs** : `expense_number`, `description`, `amount`, `expense_date`, `payment_method`, `beneficiary`
- **Ligne** : 1031-1085

#### ProformaInvoice (Facture pro forma)
- **Relations** : `organization`, `customer`, `converted_sale`
- **Champs** : `proforma_number`, `issue_date`, `validity_date`, `subtotal`, `total_amount`, `status`
- **Ligne** : 1091-1184

#### ProformaItem (Ligne pro forma)
- **Relations** : `proforma`, `product`
- **Ligne** : 1186-1238

#### PurchaseOrder (Bon de commande)
- **Relations** : `organization`, `supplier`, `warehouse`
- **Champs** : `order_number`, `order_date`, `expected_delivery_date`, `status`, `total_amount`
- **Ligne** : 1244-1324

#### PurchaseOrderItem (Ligne bon de commande)
- **Relations** : `purchase_order`, `product`
- **Ligne** : 1326-1374

#### DeliveryNote (Bon de livraison)
- **Relations** : `organization`, `sale`
- **Champs** : `delivery_number`, `delivery_date`, `recipient_name`, `delivery_address`, `carrier_name`, `status`
- **Ligne** : 1380-1438

#### DeliveryNoteItem (Ligne de livraison)
- **Relations** : `delivery_note`, `product`
- **Ligne** : 1440-1475

#### CreditSale (Vente à crédit)
- **Relations** : `organization`, `sale` (OneToOne), `customer`
- **Champs** : `total_amount`, `paid_amount`, `remaining_amount`, `due_date`, `grace_period_days`, `status`
- **Méthodes** : `sync_from_sale()`, `update_status()`
- **Ligne** : 1481-1617

---

### 4. Notifications (2 modèles)

**Fichier** : `app/notifications/models.py`

#### Notification
- **Relations** :
  - `organization` (FK)
  - `recipient` (FK - BaseUser)
  - `sender` (FK - BaseUser, optional)
- **Champs** : `notification_type`, `priority`, `title`, `message`, `entity_type`, `entity_id`, `action_url`, `is_read`
- **Ligne** : 25-155

#### NotificationPreference
- **Relations** : `organization`, `user` (BaseUser)
- **Champs** : `receive_alerts`, `receive_system`, `receive_user`, `min_priority`
- **Contrainte** : Unique (organization, user)
- **Ligne** : 161-218

---

## Relations inter-applications

### Dépendances de modèles

```python
# Core → Autres applications (pas de dépendances)
Organization, BaseUser, AdminUser, Permission, Role, Module

# HR → Core
Employee(BaseUser)  # Héritage
Employee.organization → Organization
Employee.assigned_role → Role
Employee.custom_permissions → Permission (M2M)
Employee.manager → BaseUser

# Inventory → Core
Product.organization → Organization
Sale.organization → Organization
Customer.organization → Organization

# Inventory → HR (optionnel)
Movement.created_by → Employee (via metadata, pas FK directe)

# Notifications → Core
Notification.organization → Organization
Notification.recipient → BaseUser
Notification.sender → BaseUser

# Notifications → HR/Inventory
Notification.entity_type + entity_id (générique, sans FK)
```

### ForeignKey vs GenericForeignKey

Le projet utilise principalement des **ForeignKey classiques** :
- ✅ Plus performantes
- ✅ Intégrité référentielle garantie
- ✅ Requêtes SQL optimisées

Les notifications utilisent un pattern **pseudo-générique** :
```python
entity_type = models.CharField()  # 'product', 'employee', 'sale'
entity_id = models.CharField()     # UUID ou ID de l'entité
```

---

## Patterns de conception

### 1. Héritage multi-table (Multi-table Inheritance)

**BaseUser** comme parent polymorphe :

```python
class BaseUser(AbstractBaseUser, PermissionsMixin):
    user_type = models.CharField(choices=UserType.choices)
    # Champs communs

class AdminUser(BaseUser):
    # Pas de champs supplémentaires pour l'instant

class Employee(BaseUser):
    organization = models.ForeignKey(Organization)
    department = models.ForeignKey(Department)
    # Champs spécifiques RH
```

**Avantages** :
- ForeignKey vers BaseUser → supporte Admin et Employee
- Méthode `get_concrete_user()` pour récupérer l'objet enfant
- `user_type` pour identifier le type sans requête DB

**Voir** : `app/core/models.py` (lignes 46-149)

### 2. TimeStampedModel (Abstract Base Class)

Tous les modèles héritent de `TimeStampedModel` :

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

**Voir** : `app/lourabackend/models.py`

### 3. Soft Delete (non implémenté)

Actuellement, les suppressions sont **hard delete** (CASCADE).

Pour une future implémentation :
```python
is_deleted = models.BooleanField(default=False)
deleted_at = models.DateTimeField(null=True, blank=True)
```

### 4. Caching de champs calculés

Exemple dans `Attendance` :
```python
# Cache pour éviter N+1 queries
user_email = models.EmailField(blank=True, default='')
user_full_name = models.CharField(max_length=255, blank=True)

def save(self, *args, **kwargs):
    self.user_email = self.user.email
    self.user_full_name = self.user.get_full_name()
    super().save(*args, **kwargs)
```

**Voir** : `app/hr/models.py` (lignes 1036-1042)

### 5. Propriétés calculées (@property)

Au lieu de stocker en DB, calculer à la volée :

```python
@property
def remaining_days(self):
    """Jours restants = alloués - utilisés - en attente."""
    return float(self.allocated_days) - float(self.used_days) - float(self.pending_days)
```

**Voir** : `app/hr/models.py` (lignes 607-609)

---

## Contraintes et validations

### 1. Contraintes d'unicité (unique_together)

```python
# Un seul solde de congé par employé et par année
class LeaveBalance(TimeStampedModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'year'],
                name='unique_employee_year_balance',
            ),
        ]
```

### 2. Contraintes conditionnelles

```python
# Un employé ne peut avoir qu'une fiche de paie par période
class Payslip(TimeStampedModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'payroll_period'],
                name='unique_employee_period',
                condition=models.Q(payroll_period__isnull=False)
            ),
        ]
```

**Voir** : `app/hr/models.py` (lignes 798-805)

### 3. Validateurs de champs

```python
from django.core.validators import MinValueValidator, MaxValueValidator

class Product(TimeStampedModel):
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
```

### 4. Validations métier dans save()

```python
class Contract(TimeStampedModel):
    def save(self, *args, **kwargs):
        # Un seul contrat actif par employé
        if self.is_active:
            Contract.objects.filter(
                employee=self.employee,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)
```

**Voir** : `app/hr/models.py` (lignes 396-416)

---

## Index et optimisations

### 1. Index sur ForeignKey

Django crée automatiquement des index sur les ForeignKey.

### 2. Index composites

```python
class Employee(BaseUser):
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'employment_status']),
            models.Index(fields=['employee_id']),
        ]
```

### 3. Index sur champs fréquemment filtrés

```python
class Notification(TimeStampedModel):
    class Meta:
        indexes = [
            models.Index(fields=['recipient', '-created_at'], name='idx_notif_recipient_date'),
            models.Index(fields=['organization', 'is_read'], name='idx_notif_org_read'),
        ]
```

### 4. Ordre par défaut (ordering)

```python
class Employee(BaseUser):
    class Meta:
        ordering = ['last_name', 'first_name']
```

Évite le besoin de `.order_by()` dans les QuerySets.

### 5. Select_related et Prefetch_related

Non définis dans les modèles, mais utilisés dans les ViewSets :

```python
queryset = Employee.objects.select_related(
    'organization', 'department', 'position', 'assigned_role'
).prefetch_related('custom_permissions')
```

---

## Migrations

### Nombre de migrations

```bash
app/core/migrations/        : ~15 migrations
app/hr/migrations/          : ~25 migrations
app/inventory/migrations/   : ~40 migrations
app/notifications/migrations/: ~5 migrations
```

### Dernières migrations appliquées

Pour voir l'état des migrations :
```bash
python manage.py showmigrations
```

### Créer de nouvelles migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Bonnes pratiques appliquées

✅ **Tous les modèles métier ont `organization`** : Isolation multi-tenant
✅ **TimeStampedModel** : Audit trail automatique
✅ **Choices avec TextChoices/IntegerChoices** : Type-safe
✅ **help_text** sur les champs : Documentation inline
✅ **verbose_name et verbose_name_plural** : Admin Django
✅ **db_table explicite** : Contrôle des noms de tables
✅ **Index sur colonnes fréquemment filtrées**
✅ **Constraints pour intégrité métier**
✅ **Validators pour validation de données**

---

## Références

- **Django Models** : https://docs.djangoproject.com/en/5.2/topics/db/models/
- **Model Meta options** : https://docs.djangoproject.com/en/5.2/ref/models/options/
- **Validators** : https://docs.djangoproject.com/en/5.2/ref/validators/

---

**Dernière mise à jour** : 2025-01-15
**Version** : 1.0.0
