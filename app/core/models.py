"""
Core Module Models
==================
Ce module contient les modèles de base :
- BaseUser : Modèle utilisateur parent (pour AdminUser et Employee)
- AdminUser : Administrateur d'organisations
- Organization : Organisation multi-tenant
- Permission, Role : Gestion des permissions
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager as DjangoBaseUserManager, 
    PermissionsMixin, 
    Group, 
    Permission as DjangoPermission
)

from lourabackend.models import TimeStampedModel


# ===============================
# BASE USER (Modèle parent commun)
# ===============================

class BaseUserManager(DjangoBaseUserManager):
    """Manager pour BaseUser"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        return self.create_user(email, password, **extra_fields)


class BaseUser(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Modèle utilisateur de base.
    AdminUser et Employee héritent de ce modèle (multi-table inheritance).
    Permet d'utiliser ForeignKey(BaseUser) pour référencer les deux types.
    """
    
    class UserType(models.TextChoices):
        ADMIN = 'admin', 'Administrateur'
        EMPLOYEE = 'employee', 'Employé'
    
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.EMPLOYEE
    )

    # Préférences
    language = models.CharField(max_length=5, default='fr')
    timezone = models.CharField(max_length=50, default='Africa/Conakry')

    # Statut
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    # Groupes et permissions Django
    groups = models.ManyToManyField(
        Group,
        related_name='base_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        DjangoPermission,
        related_name='base_user_permissions_set',
        blank=True
    )

    objects = BaseUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'base_users'
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]

    @property
    def is_admin_user(self):
        return self.user_type == self.UserType.ADMIN

    @property
    def is_employee_user(self):
        return self.user_type == self.UserType.EMPLOYEE

    def get_concrete_user(self):
        """Retourne l'objet AdminUser ou Employee selon le type"""
        if self.user_type == self.UserType.ADMIN:
            try:
                return self.adminuser
            except AttributeError:
                return self
        elif self.user_type == self.UserType.EMPLOYEE:
            try:
                return self.employee
            except AttributeError:
                return self
        return self

    def has_org_permission(self, permission_code):
        """Vérifie les permissions organisationnelles"""
        if self.user_type == self.UserType.ADMIN:
            return True
        concrete = self.get_concrete_user()
        if hasattr(concrete, 'has_permission'):
            return concrete.has_permission(permission_code)
        return False

    def get_organization(self):
        """Retourne l'organisation de l'utilisateur"""
        concrete = self.get_concrete_user()
        if hasattr(concrete, 'organization'):
            return concrete.organization
        if hasattr(concrete, 'organizations'):
            return concrete.organizations.first()
        return None


# ===============================
# PERMISSIONS (Modèle personnalisé)
# ===============================

class Permission(TimeStampedModel):
    """Permission granulaire pour le système de permissions personnalisé"""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'core_permissions'
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(TimeStampedModel):
    """Rôle regroupant des permissions"""

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='roles',
        null=True,
        blank=True,
        help_text="null = rôle système global"
    )
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name='roles', blank=True)
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_roles'
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        unique_together = [['organization', 'code']]
        ordering = ['name']

    def __str__(self):
        if self.is_system_role:
            return f"{self.name} (Système)"
        return f"{self.name} ({self.organization.name if self.organization else 'Global'})"

    def get_all_permissions(self):
        return list(self.permissions.values_list('code', flat=True))


# ===============================
# ORGANIZATION
# ===============================

class Category(models.Model):
    """Catégorie d'organisation"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'categories'
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name


class AdminUserManager(BaseUserManager):
    """Manager pour AdminUser"""

    def get_queryset(self):
        return super().get_queryset().filter(user_type='admin')

    def create_user(self, email, password=None, **extra_fields):
        extra_fields['user_type'] = 'admin'
        return super().create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('user_type', 'admin')
        return super().create_superuser(email, password, **extra_fields)


class AdminUser(BaseUser):
    """
    Administrateur d'organisations.
    Hérite de BaseUser pour le polymorphisme.
    """
    
    objects = AdminUserManager()

    class Meta:
        db_table = 'admin_users'
        verbose_name = "Administrateur"
        verbose_name_plural = "Administrateurs"

    def save(self, *args, **kwargs):
        self.user_type = 'admin'
        super().save(*args, **kwargs)

    def get_organizations_for_admin(self):
        return self.organizations.all()

    def has_permission(self, permission_code):
        """AdminUser a toutes les permissions"""
        return True


class Organization(TimeStampedModel):
    """Organisation multi-tenant"""
    
    name = models.CharField(max_length=255)
    subdomain = models.SlugField(max_length=63, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations"
    )

    admin = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name='organizations'
    )


    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def settings(self):
        obj, _ = OrganizationSettings.objects.get_or_create(organization=self)
        return obj


class OrganizationSettings(models.Model):
    """Paramètres d'organisation"""

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name='organization_settings'
    )
    country = models.CharField(max_length=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='MAD')
    theme = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'organization_settings'
        verbose_name = "Paramètres d'organisation"
        verbose_name_plural = "Paramètres d'organisations"

    def __str__(self):
        return f"Paramètres: {self.organization.name}"


# ===============================
# MODULE MANAGEMENT
# ===============================

class Module(TimeStampedModel):
    """
    Module représentant une fonctionnalité de l'application.
    Les modules peuvent être activés/désactivés pour chaque organisation.
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identifiant unique du module (ex: hr.employees, hr.payroll)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Nom d'affichage du module"
    )
    description = models.TextField(
        blank=True,
        help_text="Description détaillée du module"
    )
    app_name = models.CharField(
        max_length=50,
        help_text="Nom de l'application Django associée (ex: hr, inventory)"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icône du module (ex: Users, DollarSign, Calendar)"
    )
    category = models.CharField(
        max_length=50,
        default='general',
        help_text="Catégorie du module (ex: hr, finance, inventory)"
    )

    # Configuration pour l'activation automatique
    default_for_all = models.BooleanField(
        default=False,
        help_text="Si True, ce module est activé par défaut pour toutes les organisations"
    )
    default_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des noms de catégories pour lesquelles ce module est activé par défaut"
    )

    # Gestion des dépendances et permissions
    requires_subscription_tier = models.CharField(
        max_length=50,
        blank=True,
        help_text="Niveau d'abonnement requis (ex: basic, premium, enterprise)"
    )
    depends_on = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des codes de modules requis"
    )

    is_core = models.BooleanField(
        default=False,
        help_text="Module core qui ne peut pas être désactivé"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Module actif et disponible"
    )

    order = models.IntegerField(
        default=0,
        help_text="Ordre d'affichage"
    )

    class Meta:
        db_table = 'modules'
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def is_default_for_category(self, category_name):
        """Vérifie si ce module est activé par défaut pour une catégorie donnée"""
        if self.default_for_all:
            return True
        return category_name in self.default_categories

    def get_dependencies(self):
        """Retourne les modules dont ce module dépend"""
        if not self.depends_on:
            return Module.objects.none()
        return Module.objects.filter(code__in=self.depends_on)


class OrganizationModule(TimeStampedModel):
    """
    RelationMany-to-Many entre Organization et Module.
    Permet de gérer les modules activés pour chaque organisation.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='organization_modules'
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='organization_modules'
    )

    is_enabled = models.BooleanField(
        default=True,
        help_text="Module activé pour cette organisation"
    )

    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Paramètres spécifiques du module pour cette organisation"
    )

    enabled_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date d'activation du module"
    )
    enabled_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enabled_modules',
        help_text="Utilisateur ayant activé le module"
    )

    class Meta:
        db_table = 'organization_modules'
        verbose_name = "Module d'organisation"
        verbose_name_plural = "Modules d'organisations"
        unique_together = [['organization', 'module']]
        ordering = ['module__order', 'module__name']

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.organization.name} - {self.module.name}"
