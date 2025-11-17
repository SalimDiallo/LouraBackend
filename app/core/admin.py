from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import AdminUser, Organization, Category, OrganizationSettings


@admin.register(AdminUser)
class AdminUserAdmin(BaseUserAdmin):
    """Admin configuration for AdminUser"""
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates importantes', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

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
        (None, {'fields': ('name', 'subdomain', 'logo_url')}),
        ('Relations', {'fields': ('admin', 'category')}),
        ('Status', {'fields': ('is_active',)}),
        ('Dates', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ['created_at', 'updated_at']
