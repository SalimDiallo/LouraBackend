# HR (Ressources Humaines) - Documentation

## Vue d'ensemble

L'application **hr** est le module de gestion des ressources humaines. Elle gère les employés, l'organisation interne (départements, postes), les contrats, les congés, la paie (périodes, fiches de paie, avances), les pointages (présence avec QR code) et les permissions/rôles personnalisés.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/hr/`
- **Modèles** : 16 modèles (Employee, Department, Position, Contract, LeaveType, LeaveRequest, LeaveBalance, PayrollPeriod, Payslip, PayslipItem, PayrollAdvance, Attendance, Break, QRCodeSession)
- **ViewSets** : 12 ViewSets principaux
- **Endpoints** : ~80 endpoints
- **Dépendances** : `core` (Organization, BaseUser, Role, Permission)

## Modèles de données

### Employee

**Description** : Employé d'une organisation. Hérite de BaseUser pour le polymorphisme avec AdminUser.

**Champs principaux** :
- Tous les champs de `BaseUser` (email, first_name, last_name, phone, etc.)
- `organization` (ForeignKey) : Organisation de l'employé
- `employee_id` (CharField) : Matricule
- `date_of_birth` (DateField) : Date de naissance
- `gender` (CharField) : Sexe (male, female, other)
- `address`, `city`, `country` (CharField/TextField) : Adresse
- `department` (ForeignKey) : Département
- `position` (ForeignKey) : Poste
- `contract` (ForeignKey) : Contrat actif
- `hire_date`, `termination_date` (DateField) : Dates d'embauche/départ
- `manager` (ForeignKey to BaseUser) : Manager
- `assigned_role` (ForeignKey to Role) : Rôle assigné
- `employment_status` (CharField) : Statut (active, on_leave, suspended, terminated)
- `emergency_contact` (JSONField) : Contact d'urgence
- `custom_permissions` (ManyToMany) : Permissions personnalisées

**Relations** :
- ForeignKey vers `Organization`, `Department`, `Position`, `Contract`, `Role`, `BaseUser` (manager)
- ManyToMany avec `Permission` (custom_permissions)

**Méthodes importantes** :
- `has_permission(permission_code)` : Vérifie si l'employé a une permission (supporte mapping legacy)
- `get_all_permissions()` : Retourne toutes les permissions (rôle + custom)
- `is_super_admin()`, `is_hr_admin()` : Vérifications de rôle

### Department

**Description** : Département d'une organisation (structure hiérarchique possible).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom du département
- `code` (CharField) : Code unique
- `description` (TextField) : Description
- `head` (ForeignKey to BaseUser) : Responsable (Employee ou AdminUser)
- `parent_department` (ForeignKey to self) : Département parent (hiérarchie)
- `is_active` (BooleanField) : Département actif

**Relations** :
- ForeignKey vers `Organization`, `BaseUser` (head), `Department` (parent)
- OneToMany avec `Employee` (employés du département)

### Position

**Description** : Poste dans l'organisation.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `title` (CharField) : Titre du poste
- `code` (CharField) : Code unique
- `description` (TextField) : Description
- `min_salary`, `max_salary` (DecimalField) : Fourchette de salaire
- `is_active` (BooleanField) : Poste actif

### Contract

**Description** : Contrat de travail. RÈGLE IMPORTANTE : Un employé ne peut avoir qu'un seul contrat actif à la fois.

**Champs principaux** :
- `employee` (ForeignKey) : Employé
- `contract_type` (CharField) : Type (permanent/CDI, temporary/CDD, contract, internship, freelance)
- `start_date`, `end_date` (DateField) : Dates de début/fin
- `base_salary` (DecimalField) : Salaire de base
- `currency` (CharField) : Devise
- `salary_period` (CharField) : Période (hourly, daily, monthly, annual)
- `hours_per_week` (DecimalField) : Heures par semaine
- `description` (TextField) : Description
- `contract_file_url` (URLField) : URL du fichier contrat
- `is_active` (BooleanField) : Contrat actif

**Méthodes importantes** :
- `save()` : Override pour désactiver automatiquement les autres contrats actifs de l'employé
- `activate()`, `deactivate()` : Gestion de l'activation
- `is_expired` (property) : Vérifie si le contrat a expiré
- `get_active_contract(employee)` (classmethod) : Retourne le contrat actif d'un employé

### LeaveType

**Description** : Type de congé (congé payé, congé maladie, etc.).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom du type de congé
- `code` (CharField) : Code unique
- `description` (TextField) : Description
- `default_days_per_year` (IntegerField) : Jours par défaut par an
- `is_paid` (BooleanField) : Congé payé
- `requires_approval` (BooleanField) : Nécessite approbation
- `max_consecutive_days` (IntegerField) : Jours consécutifs maximum
- `color` (CharField) : Couleur pour l'affichage
- `is_active` (BooleanField) : Type actif

### LeaveRequest

**Description** : Demande de congé d'un employé.

**Champs principaux** :
- `employee` (ForeignKey) : Employé
- `leave_type` (ForeignKey) : Type de congé (nullable)
- `title` (CharField) : Titre descriptif
- `start_date`, `end_date` (DateField) : Dates de début/fin
- `start_half_day`, `end_half_day` (BooleanField) : Demi-journées
- `total_days` (DecimalField) : Nombre de jours
- `reason` (TextField) : Raison
- `attachment_url` (URLField) : Fichier joint
- `status` (CharField) : Statut (pending, approved, rejected, cancelled)
- `approver` (ForeignKey to BaseUser) : Approbateur
- `approval_date` (DateTimeField) : Date d'approbation
- `approval_notes` (TextField) : Notes d'approbation

### LeaveBalance

**Description** : Solde de congés GLOBAL d'un employé pour une année (tous types confondus).

**Champs principaux** :
- `employee` (ForeignKey) : Employé
- `year` (IntegerField) : Année
- `allocated_days` (DecimalField) : Jours alloués

**Propriétés calculées** :
- `used_days` : Jours utilisés (sum des demandes approved)
- `pending_days` : Jours en attente (sum des demandes pending)
- `remaining_days` : Jours restants (alloués - utilisés - en attente)

**Méthodes importantes** :
- `get_or_create_for_employee(employee, year, default_days)` : Récupère ou crée le solde
- `initialize_for_employee(employee, year, default_days)` : Initialise avec validation
- `check_balance(employee, leave_type, total_days, year)` : Vérifie si l'employé peut prendre X jours

### PayrollPeriod

**Description** : Période de paie (mois, quinzaine, etc.).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom de la période
- `start_date`, `end_date` (DateField) : Dates de début/fin
- `payment_date` (DateField) : Date de paiement
- `status` (CharField) : Statut (draft, processing, approved, paid, closed)
- `notes` (TextField) : Notes

### Payslip

**Description** : Fiche de paie d'un employé.

**Champs principaux** :
- `employee` (ForeignKey) : Employé
- `payroll_period` (ForeignKey, nullable) : Période (nullable pour fiches ad-hoc)
- `description` (CharField) : Description/titre (utile sans période)
- `base_salary` (DecimalField) : Salaire de base
- `gross_salary` (DecimalField, calculé) : Salaire brut
- `total_deductions` (DecimalField, calculé) : Déductions totales
- `net_salary` (DecimalField, calculé) : Salaire net
- `currency` (CharField) : Devise
- `worked_hours`, `overtime_hours`, `leave_days_taken` (DecimalField) : Détails
- `status` (CharField) : Statut (draft, approved, paid)
- `payment_method`, `payment_date`, `payment_reference` (CharField/DateField) : Paiement
- `notes` (TextField) : Notes
- `payslip_file_url` (URLField) : URL du fichier PDF

**Relations** :
- ForeignKey vers `Employee`, `PayrollPeriod` (nullable)
- OneToMany avec `PayslipItem` (lignes de paie)

**Méthodes importantes** :
- `calculate_totals()` : Calcule gross_salary, total_deductions, net_salary depuis les items
- `get_display_name()` : Retourne un nom d'affichage

### PayslipItem

**Description** : Ligne de fiche de paie (prime ou déduction).

**Champs principaux** :
- `payslip` (ForeignKey) : Fiche de paie
- `name` (CharField) : Nom de la ligne
- `amount` (DecimalField) : Montant
- `is_deduction` (BooleanField) : Déduction (True) ou Prime (False)

### PayrollAdvance

**Description** : Demande d'avance sur salaire.

**Champs principaux** :
- `employee` (ForeignKey) : Employé
- `amount` (DecimalField) : Montant
- `reason` (TextField) : Raison
- `request_date` (DateField) : Date de demande
- `status` (CharField) : Statut (pending, approved, rejected, deducted)
- `approved_by` (ForeignKey to BaseUser) : Approbateur
- `approved_date`, `rejection_reason` (DateTimeField/TextField) : Approbation/rejet
- `payment_date` (DateField) : Date de paiement
- `payslip` (ForeignKey, nullable) : Fiche de paie où l'avance est déduite
- `deduction_month` (DateField) : Mois de déduction
- `notes` (TextField) : Notes

### Attendance

**Description** : Pointage d'un utilisateur (Employee ou AdminUser).

**Champs principaux** :
- `user` (ForeignKey to BaseUser) : Utilisateur (Employee ou AdminUser)
- `organization` (ForeignKey) : Organisation
- `user_email`, `user_full_name` (CharField, cache) : Cache pour performance
- `date` (DateField) : Date du pointage
- `check_in`, `check_out` (DateTimeField) : Arrivée/départ
- `check_in_location`, `check_out_location` (CharField) : Localisation
- `check_in_notes`, `check_out_notes` (TextField) : Notes
- `break_start`, `break_end` (DateTimeField, deprecated) : Anciens champs pause
- `total_hours`, `break_duration` (DecimalField, calculé) : Heures travaillées/pause
- `status` (CharField) : Statut (present, absent, late, half_day, on_leave)
- `approval_status` (CharField) : Statut d'approbation (pending, approved, rejected)
- `is_approved` (BooleanField) : Approuvé
- `approved_by` (ForeignKey to BaseUser) : Approbateur
- `approval_date`, `rejection_reason` (DateTimeField/TextField) : Approbation/rejet
- `notes` (TextField) : Notes
- `is_overtime`, `overtime_hours` (BooleanField/DecimalField) : Heures sup

**Relations** :
- ForeignKey vers `BaseUser` (user, approved_by), `Organization`
- OneToMany avec `Break` (nouvelles pauses multiples)

**Méthodes importantes** :
- `calculate_hours()` : Calcule total_hours et break_duration depuis breaks
- `has_active_break()`, `get_active_break()` : Gestion des pauses
- `get_total_break_duration_minutes()` : Durée totale des pauses en minutes

### Break

**Description** : Pause individuelle liée à un pointage (support de plusieurs pauses par jour).

**Champs principaux** :
- `attendance` (ForeignKey) : Pointage
- `start_time`, `end_time` (DateTimeField) : Début/fin de la pause
- `notes` (TextField) : Notes

**Propriétés** :
- `duration_minutes` : Durée en minutes
- `is_active` : Pause en cours (end_time is None)

### QRCodeSession

**Description** : Session QR Code pour le pointage (support multi-employés).

**Champs principaux** :
- `id` (UUID) : Identifiant
- `organization` (ForeignKey) : Organisation
- `session_token` (CharField, unique) : Token de session
- `employee` (ForeignKey, nullable) : Employé principal (backward compat)
- `allowed_employees` (ManyToMany) : Employés autorisés (nouveau)
- `created_by` (ForeignKey to AdminUser) : Créateur
- `expires_at` (DateTimeField) : Date d'expiration
- `is_active` (BooleanField) : Session active
- `mode` (CharField) : Mode (auto, check_in, check_out)

**Méthodes importantes** :
- `is_expired()` : Vérifie si expiré
- `get_qr_code_data()` : Génère les données QR

## API Endpoints

### EmployeeViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/employees/ | Liste des employés | hr.view_employees |
| POST | /api/hr/employees/ | Créer un employé | hr.create_employees |
| GET | /api/hr/employees/{id}/ | Détails d'un employé | hr.view_employees |
| PUT/PATCH | /api/hr/employees/{id}/ | Modifier un employé | hr.update_employees |
| DELETE | /api/hr/employees/{id}/ | Supprimer un employé | hr.delete_employees |
| POST | /api/hr/employees/{id}/activate/ | Activer un employé | hr.activate_employees |
| POST | /api/hr/employees/{id}/deactivate/ | Désactiver un employé | hr.activate_employees |

**Filtres** : `department`, `position`, `employment_status`, `is_active`, `search` (prénom, nom, email, matricule)

### DepartmentViewSet, PositionViewSet, ContractViewSet

Endpoints CRUD standards + activate/deactivate pour Department et Position.

### LeaveTypeViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/leave-types/ | Liste des types de congé | hr.view_leave_types |
| POST | /api/hr/leave-types/ | Créer un type | hr.create_leave_types |
| PUT/PATCH | /api/hr/leave-types/{id}/ | Modifier un type | hr.update_leave_types |
| DELETE | /api/hr/leave-types/{id}/ | Supprimer un type | hr.delete_leave_types |

### LeaveRequestViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/leave-requests/ | Liste des demandes | hr.view_leave_requests |
| POST | /api/hr/leave-requests/ | Créer une demande | hr.create_leave_requests |
| GET | /api/hr/leave-requests/{id}/ | Détails | hr.view_leave_requests |
| PUT/PATCH | /api/hr/leave-requests/{id}/ | Modifier | hr.update_leave_requests |
| DELETE | /api/hr/leave-requests/{id}/ | Supprimer | hr.delete_leave_requests |
| POST | /api/hr/leave-requests/{id}/approve/ | Approuver | hr.approve_leave_requests |
| POST | /api/hr/leave-requests/{id}/reject/ | Rejeter | hr.approve_leave_requests |
| GET | /api/hr/leave-requests/my_requests/ | Mes demandes | (employee) |
| GET | /api/hr/leave-requests/pending_approvals/ | Demandes en attente | hr.approve_leave_requests |

**Filtres** : `employee`, `status`, `leave_type`, `start_date`, `end_date`

### LeaveBalanceViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/leave-balances/ | Liste des soldes | hr.view_leave_balances |
| POST | /api/hr/leave-balances/ | Créer/initialiser un solde | hr.create_leave_balances |
| GET | /api/hr/leave-balances/{id}/ | Détails | hr.view_leave_balances |
| PUT/PATCH | /api/hr/leave-balances/{id}/ | Modifier | hr.update_leave_balances |
| DELETE | /api/hr/leave-balances/{id}/ | Supprimer | hr.delete_leave_balances |
| POST | /api/hr/leave-balances/initialize/ | Initialiser pour un employé | hr.create_leave_balances |

**Filtres** : `employee`, `year`

### PayrollPeriodViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/payroll-periods/ | Liste des périodes | hr.view_payroll_periods |
| POST | /api/hr/payroll-periods/ | Créer une période | hr.create_payroll_periods |
| GET | /api/hr/payroll-periods/{id}/ | Détails | hr.view_payroll_periods |
| PUT/PATCH | /api/hr/payroll-periods/{id}/ | Modifier | hr.update_payroll_periods |
| DELETE | /api/hr/payroll-periods/{id}/ | Supprimer | hr.delete_payroll_periods |

**Filtres** : `status`, `start_date`, `end_date`

### PayslipViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/payslips/ | Liste des fiches de paie | hr.view_payroll |
| POST | /api/hr/payslips/ | Créer une fiche | hr.create_payroll |
| GET | /api/hr/payslips/{id}/ | Détails | hr.view_payroll |
| PUT/PATCH | /api/hr/payslips/{id}/ | Modifier | hr.update_payroll |
| DELETE | /api/hr/payslips/{id}/ | Supprimer | hr.delete_payroll |
| GET | /api/hr/payslips/{id}/export_pdf/ | Exporter en PDF | hr.export_payroll |
| GET | /api/hr/payslips/my_payslips/ | Mes fiches (employee) | (employee) |

**Filtres** : `employee`, `payroll_period`, `status`

### PayrollAdvanceViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/payroll-advances/ | Liste des avances | hr.view_payroll_advances |
| POST | /api/hr/payroll-advances/ | Créer une avance | hr.create_payroll_advances |
| GET | /api/hr/payroll-advances/{id}/ | Détails | hr.view_payroll_advances |
| PUT/PATCH | /api/hr/payroll-advances/{id}/ | Modifier | hr.update_payroll_advances |
| DELETE | /api/hr/payroll-advances/{id}/ | Supprimer | hr.delete_payroll_advances |
| POST | /api/hr/payroll-advances/{id}/approve/ | Approuver | hr.approve_payroll_advances |
| POST | /api/hr/payroll-advances/{id}/reject/ | Rejeter | hr.approve_payroll_advances |
| GET | /api/hr/payroll-advances/my_advances/ | Mes avances (employee) | (employee) |
| GET | /api/hr/payroll-advances/pending_approvals/ | Avances en attente | hr.approve_payroll_advances |

**Filtres** : `employee`, `status`

### AttendanceViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/hr/attendances/ | Liste des pointages | hr.view_attendance |
| POST | /api/hr/attendances/ | Créer un pointage | hr.create_attendance |
| GET | /api/hr/attendances/{id}/ | Détails | hr.view_attendance |
| PUT/PATCH | /api/hr/attendances/{id}/ | Modifier | hr.update_attendance |
| DELETE | /api/hr/attendances/{id}/ | Supprimer | hr.delete_attendance |
| POST | /api/hr/attendances/check_in/ | Pointer l'arrivée | (authenticated) |
| POST | /api/hr/attendances/check_out/ | Pointer le départ | (authenticated) |
| POST | /api/hr/attendances/{id}/start_break/ | Commencer une pause | (authenticated) |
| POST | /api/hr/attendances/{id}/end_break/ | Terminer une pause | (authenticated) |
| POST | /api/hr/attendances/{id}/approve/ | Approuver | hr.approve_attendance |
| POST | /api/hr/attendances/{id}/reject/ | Rejeter | hr.approve_attendance |
| GET | /api/hr/attendances/my_attendance/ | Mes pointages | (employee) |
| GET | /api/hr/attendances/stats/ | Statistiques | hr.view_attendance |
| POST | /api/hr/attendances/qr_check_in/ | Pointer via QR code | (authenticated) |
| POST | /api/hr/attendances/create_qr_session/ | Créer session QR | hr.create_qr_session |
| GET | /api/hr/attendances/qr_sessions/ | Liste sessions QR | hr.create_qr_session |
| DELETE | /api/hr/attendances/qr_sessions/{id}/ | Supprimer session QR | hr.create_qr_session |

**Filtres** : `user`, `date`, `status`, `approval_status`, `start_date`, `end_date`

### PermissionViewSet, RoleViewSet

Endpoints CRUD pour la gestion des permissions et rôles personnalisés.

## Serializers

**Employees** : EmployeeSerializer, EmployeeCreateSerializer, EmployeeListSerializer, EmployeeUpdateSerializer
**HR Config** : DepartmentSerializer, PositionSerializer, ContractSerializer
**Leaves** : LeaveTypeSerializer, LeaveRequestSerializer, LeaveBalanceSerializer, LeaveRequestApprovalSerializer
**Payroll** : PayrollPeriodSerializer, PayslipSerializer, PayslipCreateSerializer, PayrollAdvanceSerializer, PayrollAdvanceCreateSerializer, PayrollAdvanceApprovalSerializer
**Attendance** : AttendanceSerializer, AttendanceCreateSerializer, AttendanceCheckInSerializer, AttendanceCheckOutSerializer, AttendanceApprovalSerializer, QRCodeSessionSerializer, QRAttendanceCheckInSerializer
**Permissions** : PermissionSerializer, RoleSerializer

## Permissions

### Permissions personnalisées

Le module hr définit des permissions granulaires :
- **Employees** : `hr.view_employees`, `hr.create_employees`, `hr.update_employees`, `hr.delete_employees`, `hr.activate_employees`
- **Departments** : `hr.view_departments`, `hr.create_departments`, `hr.update_departments`, `hr.delete_departments`
- **Positions** : `hr.view_positions`, `hr.create_positions`, `hr.update_positions`, `hr.delete_positions`
- **Contracts** : `hr.view_contracts`, `hr.create_contracts`, `hr.update_contracts`, `hr.delete_contracts`
- **Roles** : `hr.view_roles`, `hr.create_roles`, `hr.update_roles`, `hr.delete_roles`
- **Leave** : `hr.view_leave_requests`, `hr.create_leave_requests`, `hr.approve_leave_requests`, etc.
- **Payroll** : `hr.view_payroll`, `hr.create_payroll`, `hr.update_payroll`, `hr.export_payroll`, `hr.approve_payroll_advances`
- **Attendance** : `hr.view_attendance`, `hr.create_attendance`, `hr.approve_attendance`, `hr.view_all_attendance`, `hr.create_qr_session`, `hr.manual_checkin`

### Classes de permissions Django

- **IsHRAdmin** : Utilisateur avec permission hr.admin
- **IsManagerOrHRAdmin** : Manager ou HR Admin
- **IsAdminUserOrEmployee** : AdminUser ou Employee authentifié
- **CanAccessOwnOrManage** : Accès à ses propres données ou données managées
- **RequiresEmployeePermission, RequiresDepartmentPermission, etc.** : Permissions spécifiques par module

## Services/Utilities

- **hr/permissions.py** : Classes de permissions personnalisées
- **hr/constants.py** : Constantes (permissions prédéfinies, rôles)
- **core/permission_dependencies.py** : Gestion des dépendances entre permissions

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Gestion des employés** : CRUD complet avec filtres (département, position, statut)
2. **Structure organisationnelle** : Départements hiérarchiques, postes avec fourchettes de salaire
3. **Contrats** : Gestion des contrats avec règle d'unicité du contrat actif
4. **Congés** : Demandes de congés avec validation du solde, approbation, solde global par employé/année
5. **Paie** : Périodes de paie, fiches de paie avec primes/déductions, avances sur salaire
6. **Pointage** : Système de pointage avec check-in/out, pauses multiples, QR code multi-employés
7. **Permissions/Rôles** : Système de permissions granulaires avec rôles personnalisés

## Points d'attention

### Multi-table Inheritance
- Employee hérite de BaseUser : attention aux requêtes et aux ForeignKeys

### Contrat unique actif
- La méthode `Contract.save()` désactive automatiquement les autres contrats actifs de l'employé
- Utiliser `activate()` et `deactivate()` pour gérer l'activation

### Solde de congés global
- **Un seul solde par employé/année** (tous types de congés confondus)
- Utiliser `LeaveBalance.check_balance()` avant de créer une demande
- `initialize_for_employee()` valide que le solde alloué est suffisant par rapport aux jours déjà utilisés/en attente

### Pauses multiples
- Le nouveau modèle `Break` supporte plusieurs pauses par jour
- Les anciens champs `break_start`/`break_end` sur `Attendance` sont deprecated
- `calculate_hours()` utilise maintenant les breaks pour calculer la durée totale

### QR Code multi-employés
- Une session QR peut être utilisée par plusieurs employés (champ `allowed_employees`)
- Le champ `employee` est conservé pour backward compatibility
- Modes supportés : `auto` (détection automatique), `check_in` (arrivée uniquement), `check_out` (départ uniquement)

### Permissions granulaires
- Le système de permissions personnalisé (Permission/Role) est indépendant de Django
- `Employee.has_permission()` supporte le mapping des anciens codes (ex: `can_view_employee` → `hr.view_employees`)
- Les AdminUser ont toujours toutes les permissions

### Génération PDF
- Le ViewSet `PayslipViewSet` hérite de `PDFGeneratorMixin` pour l'export PDF
- Endpoint : `/api/hr/payslips/{id}/export_pdf/`

### Avances sur salaire
- Workflow : pending → approved → deducted (simplifié, plus de statut PAID intermédiaire)
- Lien avec `Payslip` pour traçabilité de la déduction

### Statistiques et filtres
- Endpoints dédiés aux statistiques : `/api/hr/attendances/stats/`, `/api/hr/stats/overview/`, etc.
- Filtres avancés disponibles sur la plupart des ViewSets (date ranges, status, etc.)
