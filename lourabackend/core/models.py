from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission as DjangoPermission
from django.utils import timezone

from lourabackend.models import BaseProfile, TimeStampedModel

# -------------------------------
# Category Model for Organization
# -------------------------------
class Category(models.Model):
    """Category for Organizations (one-to-many: one category, many organizations)"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

# -------------------------------
# Organization Models
# -------------------------------
class AdminUser(AbstractBaseUser,BaseUserManager ,TimeStampedModel):
    """
    AdminUser: Superviseur d'une ou plusieurs organisations.
    Un admin a plusieurs organisations, et une organisation est gérée/créée par un seul admin.
    """
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'admin_users'
        verbose_name = "Administrateur d'organisation"

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Organization(TimeStampedModel):
    """Multi-tenant organization model"""
    name = models.CharField(max_length=255)
    subdomain = models.SlugField(max_length=63, unique=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)

    # Add category field: an organization has one category; a category can have many organizations
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations"
    )

    # One organization is created/managed by a single admin (owner)
    admin = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        related_name='organizations',
        help_text="L'admin qui a créé ou qui gère cette organisation"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def settings(self):
        obj, _ = OrganizationSettings.objects.get_or_create(organization=self)
        return obj

class OrganizationSettings(models.Model):
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

    def __str__(self):
        return f"Settings for {self.organization.name} ({self.country or 'no country'})"
