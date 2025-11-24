from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission as DjangoPermission
from django.utils import timezone

class TimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()


class BaseProfile(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)

    # Preferences
    language = models.CharField(max_length=5, default='fr')
    timezone = models.CharField(max_length=50, default='Africa/Conakry')

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    # Groups and Django permissions, only relevant for UserManager
    groups = models.ManyToManyField(
        Group,
        related_name='core_user_set',
        blank=True,
        help_text='The groups this account belongs to.'
    )
    user_permissions = models.ManyToManyField(
        DjangoPermission,
        related_name='core_user_permissions_set',
        blank=True,
        help_text='Specific permissions for this account.'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        abstract = True

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
