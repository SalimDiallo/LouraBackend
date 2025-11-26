from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from lourabackend.models import BaseProfile, TimeStampedModel
from core.models import Organization


# ===============================
# EMPLOYEE MANAGEMENT
# ===============================

class EmployeeManager(BaseUserManager):
    """Custom manager for Employee model"""

    def create_user(self, email, organization, password=None, **extra_fields):
        """Create and return an employee user"""
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        if not organization:
            raise ValueError("L'organisation est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Employee(BaseProfile):
    """
    Employee: Utilisateur appartenant à une organisation.
    Un employé appartient à une seule organisation et a des permissions limitées basées sur son rôle.
    """

    # Link to organization (many employees per organization)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employees',
        help_text="L'organisation à laquelle appartient cet employé"
    )

    # Employee identification
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Identifiant unique de l'employé (matricule)"
    )

    # Employment details
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

    # Direct manager
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'
    )

    # Role/Permission field
    ROLE_CHOICES = [
        ('admin', 'Administrateur RH'),
        ('manager', 'Manager'),
        ('employee', 'Employé'),
        ('readonly', 'Lecture seule'),
    ]

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='employee'
    )

    # Employment status
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

    objects = EmployeeManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'employees'
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        # Email unique per organization
        unique_together = [['email', 'organization']]
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'employment_status']),
            models.Index(fields=['employee_id']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.organization.name})"


# ===============================
# HR CONFIGURATION MODELS
# ===============================

class Department(TimeStampedModel):
    """Département au sein d'une organisation"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='departments'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    # Department head
    head = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
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


class Position(TimeStampedModel):
    """Poste/Fonction dans l'organisation"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='positions'
    )

    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    # Salary range
    min_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    max_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
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
    """Contrat de travail d'un employé"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='contracts'
    )

    CONTRACT_TYPE_CHOICES = [
        ('cdi', 'CDI - Contrat à Durée Indéterminée'),
        ('cdd', 'CDD - Contrat à Durée Déterminée'),
        ('stage', 'Stage'),
        ('freelance', 'Freelance/Consultant'),
        ('apprenticeship', 'Apprentissage'),
    ]

    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Salary information
    base_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    currency = models.CharField(max_length=3, default='GNF')

    SALARY_PERIOD_CHOICES = [
        ('hourly', 'Horaire'),
        ('daily', 'Journalier'),
        ('monthly', 'Mensuel'),
        ('annual', 'Annuel'),
    ]

    salary_period = models.CharField(
        max_length=10,
        choices=SALARY_PERIOD_CHOICES,
        default='monthly'
    )

    # Working hours
    hours_per_week = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('168.00'))]
    )

    # Contract details
    description = models.TextField(blank=True)
    contract_file_url = models.URLField(max_length=500, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'contracts'
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['employee', 'is_active']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_contract_type_display()}"


# ===============================
# LEAVE MANAGEMENT
# ===============================

class LeaveType(TimeStampedModel):
    """Type de congé configuré par organisation"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='leave_types'
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    # Leave allocation
    default_days_per_year = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de jours par défaut alloués par an"
    )

    # Settings
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    max_consecutive_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Nombre maximum de jours consécutifs autorisés"
    )

    # Color for UI display
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Couleur hex pour l'affichage")

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'leave_types'
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        unique_together = [['organization', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class LeaveBalance(TimeStampedModel):
    """Solde de congés d'un employé pour une année"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances'
    )

    year = models.PositiveIntegerField()

    # Balance tracking
    total_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Total de jours alloués"
    )

    used_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Jours utilisés"
    )

    pending_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Jours en attente d'approbation"
    )

    class Meta:
        db_table = 'leave_balances'
        verbose_name = "Solde de congés"
        verbose_name_plural = "Soldes de congés"
        unique_together = [['employee', 'leave_type', 'year']]
        ordering = ['-year', 'leave_type']
        indexes = [
            models.Index(fields=['employee', 'year']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.year})"

    @property
    def available_days(self):
        """Jours de congés disponibles"""
        return self.total_days - self.used_days - self.pending_days


class LeaveRequest(TimeStampedModel):
    """Demande de congé"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )

    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='requests'
    )

    start_date = models.DateField()
    end_date = models.DateField()

    # Half-day options
    start_half_day = models.BooleanField(default=False, help_text="Demi-journée de début")
    end_half_day = models.BooleanField(default=False, help_text="Demi-journée de fin")

    total_days = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Nombre total de jours demandés"
    )

    reason = models.TextField(blank=True)
    attachment_url = models.URLField(max_length=500, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('cancelled', 'Annulé'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Approval workflow
    approver = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
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


# ===============================
# PAYROLL MANAGEMENT
# ===============================

class PayrollPeriod(TimeStampedModel):
    """Période de paie"""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='payroll_periods'
    )

    name = models.CharField(max_length=100, help_text="Ex: Janvier 2025, Q1 2025")
    start_date = models.DateField()
    end_date = models.DateField()
    payment_date = models.DateField(help_text="Date de versement prévue")

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('processing', 'En traitement'),
        ('approved', 'Approuvé'),
        ('paid', 'Payé'),
        ('closed', 'Clôturé'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'payroll_periods'
        verbose_name = "Période de paie"
        verbose_name_plural = "Périodes de paie"
        unique_together = [['organization', 'name']]
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['organization', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Payslip(TimeStampedModel):
    """Fiche de paie d'un employé"""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='payslips'
    )

    payroll_period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='payslips'
    )

    # Salary components
    base_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Earnings (additions)
    overtime_pay = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    bonuses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Deductions
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    social_security = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    other_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Calculated totals
    gross_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Salaire brut (base + primes + indemnités)"
    )

    total_deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Total des déductions"
    )

    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Salaire net à payer"
    )

    currency = models.CharField(max_length=3, default='GNF')

    # Working hours
    worked_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    # Leave days
    leave_days_taken = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # Payment status
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('approved', 'Approuvé'),
        ('paid', 'Payé'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    payment_method = models.CharField(max_length=50, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)
    payslip_file_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'payslips'
        verbose_name = "Fiche de paie"
        verbose_name_plural = "Fiches de paie"
        unique_together = [['employee', 'payroll_period']]
        ordering = ['-payroll_period__start_date', 'employee__last_name']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['payroll_period', 'status']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.payroll_period.name}"

    def save(self, *args, **kwargs):
        """Calculate totals before saving"""
        # Calculate gross salary
        self.gross_salary = (
            self.base_salary +
            self.overtime_pay +
            self.bonuses +
            self.allowances
        )

        # Calculate total deductions
        self.total_deductions = (
            self.tax +
            self.social_security +
            self.other_deductions
        )

        # Calculate net salary
        self.net_salary = self.gross_salary - self.total_deductions

        super().save(*args, **kwargs)


class PayslipItem(TimeStampedModel):
    """Ligne de détail d'une fiche de paie (pour les éléments personnalisés)"""

    payslip = models.ForeignKey(
        Payslip,
        on_delete=models.CASCADE,
        related_name='items'
    )

    ITEM_TYPE_CHOICES = [
        ('earning', 'Gain'),
        ('deduction', 'Déduction'),
    ]

    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES)
    description = models.CharField(max_length=255)

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    quantity = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Montant total (amount * quantity)"
    )

    class Meta:
        db_table = 'payslip_items'
        verbose_name = "Ligne de fiche de paie"
        verbose_name_plural = "Lignes de fiches de paie"
        ordering = ['item_type', 'description']

    def __str__(self):
        return f"{self.description} - {self.total}"

    def save(self, *args, **kwargs):
        """Calculate total before saving"""
        self.total = self.amount * self.quantity
        super().save(*args, **kwargs)
