"""
HR Module Models
================
Ce module contient tous les modèles liés à la gestion RH :
- Employee : Utilisateur employé d'une organisation
- Department, Position : Structure organisationnelle
- Contract : Contrats de travail
- Leave Management : Gestion des congés
- Payroll : Gestion de la paie
- Attendance : Pointage des heures
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from lourabackend.models import TimeStampedModel
from core.models import Organization, Role, Permission, BaseUser


# ===============================
# EMPLOYEE MANAGEMENT
# ===============================

class EmployeeManager(models.Manager):
    """Manager pour le modèle Employee"""

    def get_queryset(self):
        return super().get_queryset().filter(user_type='employee')

    def create_user(self, email, organization, password=None, **extra_fields):
        """Crée et retourne un employé"""
        extra_fields['user_type'] = 'employee'
        
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        if not organization:
            raise ValueError("L'organisation est obligatoire")

        email = BaseUser.objects.normalize_email(email)
        user = self.model(email=email, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Employee(BaseUser):
    """
    Employé d'une organisation.
    Hérite de BaseUser pour le polymorphisme avec AdminUser.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employees',
        help_text="Organisation de l'employé"
    )

    employee_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Matricule de l'employé"
    )

    date_of_birth = models.DateField(null=True, blank=True)

    GENDER_CHOICES = [
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('other', 'Autre'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    position = models.ForeignKey(
        'Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    contract = models.ForeignKey(
        'Contract',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)

    # Manager peut être Employee ou AdminUser
    manager = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )

    assigned_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        help_text="Rôle attribué à l'employé"
    )

    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('on_leave', 'En congé'),
        ('suspended', 'Suspendu'),
        ('terminated', 'Terminé'),
    ]

    employment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    emergency_contact = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Contact d'urgence (name, phone, relationship)"
    )

    custom_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='employees_with_permission',
        help_text="Permissions personnalisées"
    )

    objects = EmployeeManager()

    class Meta:
        db_table = 'employees'
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'employment_status']),
            models.Index(fields=['employee_id']),
        ]

    def save(self, *args, **kwargs):
        self.user_type = 'employee'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.organization.name})"

    def has_permission(self, permission_code):
        """
        Vérifie si l'employé a une permission.
        Supporte les anciens formats (can_view_employee) et les convertit
        vers le nouveau format (hr.view_employees).
        """
        # Mapping des anciens codes vers les nouveaux
        LEGACY_MAPPING = {
            # Employees
            'can_view_employee': 'hr.view_employees',
            'can_create_employee': 'hr.create_employees',
            'can_update_employee': 'hr.update_employees',
            'can_delete_employee': 'hr.delete_employees',
            'can_activate_employee': 'hr.update_employees',
            # Departments
            'can_view_department': 'hr.view_departments',
            'can_create_department': 'hr.create_departments',
            'can_update_department': 'hr.update_departments',
            'can_delete_department': 'hr.delete_departments',
            # Positions
            'can_view_position': 'hr.view_positions',
            'can_create_position': 'hr.create_positions',
            'can_update_position': 'hr.update_positions',
            'can_delete_position': 'hr.delete_positions',
            # Contracts
            'can_view_contract': 'hr.view_contracts',
            'can_create_contract': 'hr.create_contracts',
            'can_update_contract': 'hr.update_contracts',
            'can_delete_contract': 'hr.delete_contracts',
            # Roles
            'can_view_role': 'hr.view_roles',
            'can_create_role': 'hr.create_roles',
            'can_update_role': 'hr.update_roles',
            'can_delete_role': 'hr.delete_roles',
            # Leave
            'can_view_leave': 'hr.view_leave_requests',
            'can_create_leave': 'hr.create_leave_requests',
            'can_approve_leave': 'hr.approve_leave_requests',
            # Payroll
            'can_view_payroll': 'hr.view_payroll',
            'can_create_payroll': 'hr.create_payroll',
            'can_update_payroll': 'hr.update_payroll',
            'can_export_payroll': 'hr.export_payroll',
            # Attendance
            'can_view_attendance': 'hr.view_attendance',
            'can_view_all_attendance': 'hr.view_all_attendance',
            'can_create_attendance': 'hr.create_attendance',
            'can_update_attendance': 'hr.update_attendance',
            'can_delete_attendance': 'hr.delete_attendance',
            'can_approve_attendance': 'hr.approve_attendance',
            'can_manual_checkin': 'hr.manual_checkin',
            'can_create_qr_session': 'hr.create_qr_session',
        }
        
        # Normaliser le code de permission
        normalized_code = LEGACY_MAPPING.get(permission_code, permission_code)
        
        if self.custom_permissions.filter(code=normalized_code).exists():
            return True
        if self.assigned_role:
            return self.assigned_role.permissions.filter(code=normalized_code).exists()
        return False

    def get_all_permissions(self):
        """Retourne toutes les permissions de l'employé"""
        permission_codes = set()
        if self.assigned_role:
            permission_codes.update(
                self.assigned_role.permissions.values_list('code', flat=True)
            )
        permission_codes.update(
            self.custom_permissions.values_list('code', flat=True)
        )
        return Permission.objects.filter(code__in=permission_codes)

    def is_super_admin(self):
        return self.assigned_role and self.assigned_role.code == 'super_admin'

    def is_hr_admin(self):
        return self.assigned_role and self.assigned_role.code in ['super_admin', 'hr_admin']

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email


# ===============================
# ORGANIZATION STRUCTURE
# ===============================

class Department(TimeStampedModel):
    """Département d'une organisation"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    
    # Responsable (Employee ou AdminUser)
    head = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    
    # Département parent (hiérarchie)
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_departments'
    )
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'departments'
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        unique_together = [['organization', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def get_head_name(self):
        return self.head.get_full_name() if self.head else None


class Position(TimeStampedModel):
    """Poste dans l'organisation"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    min_salary = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    max_salary = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'positions'
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        unique_together = [['organization', 'title']]
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.organization.name})"


class Contract(TimeStampedModel):
    """
    Contrat de travail
    
    Règle métier importante : Un employé ne peut avoir qu'un seul contrat actif
    à un instant donné. Quand un contrat est activé, les autres contrats de
    l'employé sont automatiquement désactivés.
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='contracts'
    )

    CONTRACT_TYPE_CHOICES = [
        ('permanent', 'CDI'),
        ('temporary', 'CDD'),
        ('contract', 'Contractuel'),
        ('internship', 'Stage'),
        ('freelance', 'Freelance'),
    ]

    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    base_salary = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(max_length=3, default='', blank=True)

    SALARY_PERIOD_CHOICES = [
        ('hourly', 'Horaire'),
        ('daily', 'Journalier'),
        ('monthly', 'Mensuel'),
        ('annual', 'Annuel'),
    ]
    salary_period = models.CharField(max_length=10, choices=SALARY_PERIOD_CHOICES, default='monthly')
    hours_per_week = models.DecimalField(
        max_digits=5, decimal_places=2, default=40,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('168.00'))]
    )
    description = models.TextField(blank=True)
    contract_file_url = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'contracts'
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-start_date']
        indexes = [models.Index(fields=['employee', 'is_active'])]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_contract_type_display()}"

    def save(self, *args, **kwargs):
        """
        Override save pour garantir un seul contrat actif par employé.
        Si ce contrat est activé, désactive les autres contrats de l'employé
        et met à jour la référence du contrat actif sur l'employé.
        """
        # Déterminer si c'est une création ou une mise à jour
        is_new = self.pk is None
        
        # Si ce contrat devient actif, désactiver les autres contrats de l'employé
        if self.is_active:
            # Désactiver tous les autres contrats actifs de cet employé
            Contract.objects.filter(
                employee=self.employee,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
        
        # Mettre à jour la référence du contrat actif sur l'employé
        self._update_employee_contract()

    def _update_employee_contract(self):
        """Met à jour le champ contract de l'employé avec le contrat actif courant."""
        if self.is_active:
            # Ce contrat est actif, le lier à l'employé
            if self.employee.contract_id != self.pk:
                Employee.objects.filter(pk=self.employee.pk).update(contract=self)
        else:
            # Ce contrat n'est plus actif, vérifier s'il y a un autre contrat actif
            active_contract = Contract.objects.filter(
                employee=self.employee,
                is_active=True
            ).first()
            
            if active_contract:
                Employee.objects.filter(pk=self.employee.pk).update(contract=active_contract)
            elif self.employee.contract_id == self.pk:
                # Aucun contrat actif et c'était ce contrat qui était lié
                Employee.objects.filter(pk=self.employee.pk).update(contract=None)

    def activate(self):
        """Active ce contrat et désactive tous les autres contrats de l'employé."""
        self.is_active = True
        self.save()

    def deactivate(self):
        """Désactive ce contrat."""
        self.is_active = False
        self.save()

    @classmethod
    def get_active_contract(cls, employee):
        """Retourne le contrat actif d'un employé, s'il existe."""
        return cls.objects.filter(employee=employee, is_active=True).first()

    @property
    def is_expired(self):
        """Vérifie si le contrat a expiré (basé sur end_date)."""
        from django.utils import timezone
        if self.end_date:
            return self.end_date < timezone.now().date()
        return False


# ===============================
# LEAVE MANAGEMENT
# ===============================

class LeaveType(TimeStampedModel):
    """Type de congé"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='leave_types'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    default_days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_consecutive_days = models.PositiveIntegerField(null=True, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'leave_types'
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        unique_together = [['organization', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class LeaveRequest(TimeStampedModel):
    """Demande de congé"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='requests', null=True, blank=True)
    title = models.CharField(max_length=200, blank=True, help_text="Titre descriptif de la demande")
    start_date = models.DateField()
    end_date = models.DateField()
    start_half_day = models.BooleanField(default=False)
    end_half_day = models.BooleanField(default=False)
    total_days = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.TextField(blank=True)
    attachment_url = models.URLField(max_length=500, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Approbateur (Employee ou AdminUser)
    approver = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leave_requests'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    class Meta:
        db_table = 'leave_requests'
        verbose_name = "Demande de congé"
        verbose_name_plural = "Demandes de congés"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    def get_approver_name(self):
        return self.approver.get_full_name() if self.approver else None


class LeaveBalance(TimeStampedModel):
    """
    Solde de congés par employé, par année.

    Solde GLOBAL uniquement : tous types de congés confondus.
    Chaque employé a un seul solde annuel qui couvre tous les types de congés.
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    year = models.PositiveIntegerField(help_text="Année du solde de congés")
    allocated_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Nombre de jours alloués pour l'année"
    )

    class Meta:
        db_table = 'leave_balances'
        verbose_name = "Solde de congé"
        verbose_name_plural = "Soldes de congés"
        ordering = ['-year']
        constraints = [
            # Un seul solde par employé et par année
            models.UniqueConstraint(
                fields=['employee', 'year'],
                name='unique_employee_year_balance',
            ),
        ]

    def __str__(self):
        return (
            f"{self.employee.get_full_name()} - Solde global "
            f"({self.year}): {self.allocated_days} alloués, "
            f"{self.used_days} utilisés, {self.remaining_days} restants"
        )

    @property
    def used_days(self):
        """Calcule les jours utilisés à partir des demandes approuvées de l'année (tous types confondus)."""
        from django.db.models import Sum
        total = LeaveRequest.objects.filter(
            employee=self.employee,
            status='approved',
            start_date__year=self.year,
        ).aggregate(total=Sum('total_days'))['total']
        return total or 0

    @property
    def pending_days(self):
        """Calcule les jours en attente d'approbation pour l'année (tous types confondus)."""
        from django.db.models import Sum
        total = LeaveRequest.objects.filter(
            employee=self.employee,
            status='pending',
            start_date__year=self.year,
        ).aggregate(total=Sum('total_days'))['total']
        return total or 0

    @property
    def remaining_days(self):
        """Jours restants = alloués - utilisés - en attente."""
        return float(self.allocated_days) - float(self.used_days) - float(self.pending_days)

    @classmethod
    def get_or_create_for_employee(cls, employee, year=None, default_days=0):
        """
        Récupère ou crée le solde global d'un employé pour une année.
        """
        if year is None:
            from django.utils import timezone
            year = timezone.now().year

        balance, created = cls.objects.get_or_create(
            employee=employee,
            year=year,
            defaults={'allocated_days': default_days}
        )
        return balance

    @classmethod
    def initialize_for_employee(cls, employee, year=None, default_days=0):
        """
        Initialise le solde global de congés pour un employé.
        Vérifie que le nombre de jours alloués est suffisant par rapport aux jours déjà utilisés.
        """
        if year is None:
            from django.utils import timezone
            year = timezone.now().year

        # Vérifier les jours déjà utilisés pour cette année
        from django.db.models import Sum
        used_days = LeaveRequest.objects.filter(
            employee=employee,
            status='approved',
            start_date__year=year,
        ).aggregate(total=Sum('total_days'))['total'] or 0

        pending_days = LeaveRequest.objects.filter(
            employee=employee,
            status='pending',
            start_date__year=year,
        ).aggregate(total=Sum('total_days'))['total'] or 0

        total_committed = float(used_days) + float(pending_days)

        # Vérifier que le nombre de jours alloués est suffisant
        if float(default_days) < total_committed:
            from rest_framework import serializers
            raise serializers.ValidationError({
                'default_days': (
                    f"Le nombre de jours alloués ({default_days}) est insuffisant. "
                    f"L'employé a déjà {used_days} jour(s) utilisé(s) et {pending_days} jour(s) en attente "
                    f"pour l'année {year}. Minimum requis: {total_committed} jours."
                )
            })

        balance, created = cls.objects.get_or_create(
            employee=employee,
            year=year,
            defaults={'allocated_days': default_days}
        )

        if not created:
            # Si le solde existe déjà, on met à jour le nombre de jours alloués
            balance.allocated_days = default_days
            balance.save()

        return [balance]

    @classmethod
    def check_balance(cls, employee, leave_type, total_days, year=None):
        """
        Vérifie si un employé peut prendre `total_days` jours.
        Vérifie uniquement le solde global (leave_type ignoré).

        Retourne (can_take: bool, message: str)
        """
        if year is None:
            from django.utils import timezone
            year = timezone.now().year

        total_days = float(total_days)

        # Vérifier le solde global
        try:
            balance = cls.objects.get(
                employee=employee,
                year=year,
            )
            if balance.remaining_days < total_days:
                return (
                    False,
                    f"Solde insuffisant : "
                    f"{balance.remaining_days:.1f} jour(s) restant(s), "
                    f"{total_days:.1f} demandé(s)."
                )
        except cls.DoesNotExist:
            # Pas de solde configuré → pas de limite
            pass

        return (True, "")


# ===============================
# PAYROLL MANAGEMENT
# ===============================

class PayrollPeriod(TimeStampedModel):
    """Période de paie"""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payroll_periods')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('processing', 'En traitement'),
        ('approved', 'Approuvé'),
        ('paid', 'Payé'),
        ('closed', 'Clôturé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'payroll_periods'
        verbose_name = "Période de paie"
        verbose_name_plural = "Périodes de paie"
        unique_together = [['organization', 'name']]
        ordering = ['-start_date']
        indexes = [models.Index(fields=['organization', 'status'])]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Payslip(TimeStampedModel):
    """Fiche de paie"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    # Période de paie optionnelle - permet de créer des fiches de paie ad-hoc
    payroll_period = models.ForeignKey(
        PayrollPeriod, 
        on_delete=models.CASCADE, 
        related_name='payslips',
        null=True,
        blank=True
    )
    
    # Description/titre de la fiche de paie (utile quand pas de période)
    description = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Description ou titre de la fiche de paie (ex: 'Paie Janvier 2026', 'Prime exceptionnelle')"
    )

    base_salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    currency = models.CharField(max_length=3, default='GNF')
    worked_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    leave_days_taken = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('approved', 'Approuvé'),
        ('paid', 'Payé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=50, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    payslip_file_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'payslips'
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"
        ordering = ['-created_at', 'employee__last_name']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['payroll_period', 'status']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            # Unicité conditionnelle: un employé ne peut avoir qu'une fiche par période (si période définie)
            models.UniqueConstraint(
                fields=['employee', 'payroll_period'],
                name='unique_employee_period',
                condition=models.Q(payroll_period__isnull=False)
            ),
        ]

    def __str__(self):
        if self.payroll_period:
            return f"{self.employee.get_full_name()} - {self.payroll_period.name}"
        elif self.description:
            return f"{self.employee.get_full_name()} - {self.description}"
        return f"{self.employee.get_full_name()} - {self.created_at.strftime('%B %Y')}"
    
    def get_display_name(self):
        """Retourne un nom d'affichage pour la fiche de paie"""
        if self.description:
            return self.description
        if self.payroll_period:
            return self.payroll_period.name
        return f"Paie du {self.created_at.strftime('%d/%m/%Y')}"

    def calculate_totals(self):
        """Calcule les totaux à partir des items"""
        items = self.items.all()
        total_allowances = sum(item.amount for item in items if not item.is_deduction)
        total_deductions = sum(item.amount for item in items if item.is_deduction)
        
        self.gross_salary = self.base_salary + Decimal(str(total_allowances))
        self.total_deductions = Decimal(str(total_deductions))
        self.net_salary = self.gross_salary - self.total_deductions
        self.save()


class PayslipItem(TimeStampedModel):
    """Ligne de fiche de paie (prime ou déduction)"""

    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_deduction = models.BooleanField(default=False)

    class Meta:
        db_table = 'payslip_items'
        verbose_name = "Ligne de fiche de paie"
        verbose_name_plural = "Lignes de fiches de paie"
        ordering = ['is_deduction', 'name']

    def __str__(self):
        return f"{self.name} - {self.amount} ({'Déduction' if self.is_deduction else 'Prime'})"


class PayrollAdvance(TimeStampedModel):
    """Demande d'avance sur salaire"""

    class AdvanceStatus(models.TextChoices):
        PENDING = 'pending', 'En attente'
        APPROVED = 'approved', 'Approuvée'
        REJECTED = 'rejected', 'Rejetée'
        # PAID = 'paid', 'payé'
        DEDUCTED = 'deducted', 'Déduite'  # Simplifié: plus de statut PAID intermédiaire

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_advances')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reason = models.TextField()
    request_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=AdvanceStatus.choices, default=AdvanceStatus.PENDING)

    # Approbateur (Employee ou AdminUser)
    approved_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_advances'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payslip = models.ForeignKey(Payslip, on_delete=models.SET_NULL, null=True, blank=True, related_name='advances_deducted')
    deduction_month = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'payroll_advances'
        verbose_name = "Avance sur salaire"
        verbose_name_plural = "Avances sur salaire"
        ordering = ['-request_date', '-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['request_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Avance {self.amount} - {self.employee.get_full_name()} - {self.get_status_display()}"


# ===============================
# ATTENDANCE MANAGEMENT
# ===============================

class Attendance(TimeStampedModel):
    """Pointage d'un utilisateur"""

    # Utilisateur (Employee ou AdminUser)
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    # Cache pour performance
    user_email = models.EmailField(max_length=255, blank=True, default='')
    user_full_name = models.CharField(max_length=255, blank=True, default='')

    date = models.DateField()

    check_in = models.DateTimeField(null=True, blank=True)
    check_in_location = models.CharField(max_length=255, blank=True)
    check_in_notes = models.TextField(blank=True)

    check_out = models.DateTimeField(null=True, blank=True)
    check_out_location = models.CharField(max_length=255, blank=True)
    check_out_notes = models.TextField(blank=True)

    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)

    total_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    break_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    STATUS_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En retard'),
        ('half_day', 'Demi-journée'),
        ('on_leave', 'En congé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    is_approved = models.BooleanField(default=False)

    # Approbateur (Employee ou AdminUser)
    approved_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_attendances'
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    notes = models.TextField(blank=True)
    is_overtime = models.BooleanField(default=False)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'attendances'
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        ordering = ['-date', '-check_in']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['organization', 'date']),
            models.Index(fields=['date', 'status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'user', 'date'],
                name='unique_user_date_attendance'
            )
        ]

    def __str__(self):
        return f"{self.user_full_name or self.user_email} - {self.date} ({self.status})"

    def calculate_hours(self):
        """Calcule les heures travaillées en tenant compte de toutes les pauses"""
        if self.check_in and self.check_out:
            total_time = self.check_out - self.check_in
            total_hours = total_time.total_seconds() / 3600

            # Calculer la durée totale des pauses depuis le modèle Break
            break_hours = 0
            if self.pk:  # Only if saved (has breaks relation)
                for brk in self.breaks.all():
                    if brk.start_time and brk.end_time:
                        break_time = brk.end_time - brk.start_time
                        break_hours += break_time.total_seconds() / 3600

            # Fallback: utiliser les anciens champs si pas de breaks liés
            if break_hours == 0 and self.break_start and self.break_end:
                break_time = self.break_end - self.break_start
                break_hours = break_time.total_seconds() / 3600

            self.break_duration = Decimal(str(round(break_hours, 2)))
            self.total_hours = Decimal(str(round(total_hours - break_hours, 2)))

            if self.total_hours > 8:
                self.is_overtime = True
                self.overtime_hours = self.total_hours - 8
            else:
                self.is_overtime = False
                self.overtime_hours = 0

    def get_total_break_duration_minutes(self):
        """Retourne la durée totale des pauses en minutes"""
        total_minutes = 0
        for brk in self.breaks.all():
            if brk.start_time and brk.end_time:
                delta = brk.end_time - brk.start_time
                total_minutes += delta.total_seconds() / 60
        return round(total_minutes)

    def has_active_break(self):
        """Vérifie s'il y a une pause en cours"""
        return self.breaks.filter(end_time__isnull=True).exists()

    def get_active_break(self):
        """Retourne la pause en cours, ou None"""
        return self.breaks.filter(end_time__isnull=True).first()

    def save(self, *args, **kwargs):
        self.calculate_hours()
        # Mettre à jour le cache
        if self.user:
            self.user_email = self.user.email
            self.user_full_name = self.user.get_full_name()
        super().save(*args, **kwargs)



class Break(TimeStampedModel):
    """Pause individuelle liée à un pointage. Permet plusieurs pauses par jour."""

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='breaks'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'attendance_breaks'
        verbose_name = "Pause"
        verbose_name_plural = "Pauses"
        ordering = ['start_time']

    def __str__(self):
        end = self.end_time.strftime('%H:%M') if self.end_time else 'en cours'
        return f"Pause {self.start_time.strftime('%H:%M')} → {end}"

    @property
    def duration_minutes(self):
        """Durée de la pause en minutes"""
        if self.start_time and self.end_time:
            return round((self.end_time - self.start_time).total_seconds() / 60)
        return 0

    @property
    def is_active(self):
        """Vrai si la pause est en cours"""
        return self.end_time is None


# ===============================
# QR CODE ATTENDANCE
# ===============================

class QRCodeSession(TimeStampedModel):
    """Session QR Code pour le pointage"""
    import uuid

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='qr_sessions')
    session_token = models.CharField(max_length=64, unique=True, db_index=True)

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='qr_sessions',
        null=True,
        blank=True
    )

    allowed_employees = models.ManyToManyField(
        'Employee',
        related_name='allowed_qr_sessions',
        blank=True
    )

    created_by = models.ForeignKey(
        'core.AdminUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_qr_sessions'
    )

    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    MODE_CHOICES = [
        ('auto', 'Auto'),
        ('check_in', 'Arrivée'),
        ('check_out', 'Départ'),
    ]
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='auto')

    class Meta:
        db_table = 'hr_qr_code_sessions'
        verbose_name = "Session QR Code"
        verbose_name_plural = "Sessions QR Code"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        name = self.employee.get_full_name() if self.employee else "Multi-employés"
        return f"QR Session: {name} - {self.session_token[:8]}..."

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def get_qr_code_data(self):
        import json
        return json.dumps({
            'session_token': self.session_token,
            'employee_name': self.employee.get_full_name() if self.employee else None,
            'employee_id': str(self.employee.id) if self.employee else None,
        })
