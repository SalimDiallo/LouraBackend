from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    AdminUser,
    BaseUser,
    Organization,
    Category,
    OrganizationSettings,
    Module,
    OrganizationModule,
    Permission,
    Role,
)

@admin.register(AdminUser)
class AdminUserAdmin(BaseUserAdmin):
    """Admin configuration for AdminUser"""
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone', 'avatar_url', 'language', 'timezone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Détails', {'fields': ('user_type',)}),
        ('Dates importantes', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'phone', 'avatar_url', 'language', 'timezone'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']




@admin.register(BaseUser)
class BaseUserAdmin(admin.ModelAdmin):
    """Admin configuration for BaseUser"""
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'created_at']
    list_filter = ['user_type', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category"""
    list_display = ['name', 'description']
    search_fields = ['name']


class OrganizationSettingsInline(admin.StackedInline):
    """Inline admin for OrganizationSettings"""
    model = OrganizationSettings
    can_delete = False
    verbose_name_plural = 'Settings'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for Organization"""
    list_display = ['name', 'subdomain', 'admin', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'subdomain', 'admin__email']
    ordering = ['-created_at']
    inlines = [OrganizationSettingsInline]

    fieldsets = (
        (None, {'fields': ('name', 'subdomain', 'logo_url', 'logo')}),
        ('Relations', {'fields': ('admin', 'category')}),
        ('Status', {'fields': ('is_active',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    """Admin configuration for OrganizationSettings"""
    list_display = ['organization', 'country', 'currency', 'theme', 'contact_email']
    list_filter = ['country', 'currency', 'theme']
    search_fields = ['organization__name', 'contact_email']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin configuration for Module"""
    list_display = ['code', 'name', 'app_name', 'category', 'is_core', 'is_active', 'order']
    list_filter = ['is_core', 'is_active', 'app_name', 'category']
    search_fields = ['code', 'name', 'app_name']
    ordering = ['order', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OrganizationModule)
class OrganizationModuleAdmin(admin.ModelAdmin):
    """Admin configuration for OrganizationModule"""
    list_display = ['organization', 'module', 'is_enabled', 'enabled_at', 'enabled_by']
    list_filter = ['is_enabled', 'module', 'organization']
    search_fields = ['organization__name', 'module__name']
    readonly_fields = ['created_at', 'updated_at', 'enabled_at']


# @admin.register(Permission)
# class PermissionAdmin(admin.ModelAdmin):
#     """Admin configuration for Permission"""
#     list_display = ['code', 'name', 'category', 'description']
#     list_filter = ['category']
#     search_fields = ['code', 'name', 'category', 'description']


# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     """Admin configuration for Role"""
#     list_display = ['code', 'name', 'organization', 'is_system_role', 'is_active']
#     list_filter = ['organization', 'is_system_role', 'is_active']
#     search_fields = ['code', 'name', 'organization__name']
