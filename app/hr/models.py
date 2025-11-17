from django.db import models
# from lourabackend.models import BaseProfile, TimeStampedModel
# from core.models import Organization

# -------------------------------
# FUTURE IMPLEMENTATION: Employee Models
# -------------------------------

"""
TODO: Phase 2 - Employee Management

When implementing employee functionality, consider the following structure:

class EmployeeManager(BaseUserManager):
    '''Custom manager for Employee model'''

    def create_user(self, email, organization, password=None, **extra_fields):
        '''Create and return an employee user'''
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        if not organization:
            raise ValueError("L'organisation est obligatoire")

        email = self.normalize_email(email)
        user = self.model(email=email, organization=organization, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Employee(BaseProfile, TimeStampedModel):
    '''
    Employee: Utilisateur appartenant à une organisation.
    Un employé appartient à une seule organisation et a des permissions limitées.
    '''
    # Link to organization (many employees per organization)
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='employees',
        help_text="L'organisation à laquelle appartient cet employé"
    )

    # Employee-specific fields
    employee_id = models.CharField(max_length=50, blank=True)
    position = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(null=True, blank=True)

    # Role/Permission field (can be FK to Role model later)
    role = models.CharField(
        max_length=50,
        choices=[
            ('admin', 'Administrateur'),
            ('manager', 'Manager'),
            ('employee', 'Employé'),
            ('readonly', 'Lecture seule'),
        ],
        default='employee'
    )

    objects = EmployeeManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'organization']

    class Meta:
        db_table = 'employees'
        verbose_name = "Employé"
        unique_together = [['email', 'organization']]  # Email unique per organization
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.organization.name})"


class EmployeePermission(TimeStampedModel):
    '''
    Custom permissions for employees within their organization
    '''
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='custom_permissions'
    )

    permission_code = models.CharField(max_length=100)
    permission_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'employee_permissions'
        unique_together = [['employee', 'permission_code']]


Authentication Endpoints Structure:

/api/core/auth/          -> AdminUser authentication (current)
  - register/
  - login/
  - logout/
  - me/

/api/hr/auth/            -> Employee authentication (future)
  - login/               -> Employee login (requires organization context)
  - logout/
  - me/
  - change-password/

Key Implementation Notes:
1. Employees authenticate with email + organization subdomain + password
2. Employee tokens should include organization scope
3. All employee queries must be filtered by their organization
4. Consider using custom permissions classes like IsEmployeeOfOrganization
5. Employee creation should be done by AdminUser or authorized employees only
6. Implement organization-scoped querysets for all employee-accessible models
"""
