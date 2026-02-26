"""
Admin interface for Services module
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    BusinessProfile,
    ServiceType,
    ServiceField,
    ServiceStatus,
    Service,
    ServiceStatusHistory,
    ServiceActivity,
    ServiceComment,
    ServiceTemplate
)


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'color_badge', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('organization', 'name', 'code', 'description')
        }),
        ('Apparence', {
            'fields': ('icon', 'color')
        }),
        ('Configuration', {
            'fields': ('is_active', 'settings')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.name
        )
    color_badge.short_description = 'Couleur'


class ServiceFieldInline(admin.TabularInline):
    model = ServiceField
    extra = 0
    fields = ['name', 'field_key', 'field_type', 'is_required', 'order']


class ServiceStatusInline(admin.TabularInline):
    model = ServiceStatus
    extra = 0
    fields = ['name', 'code', 'status_type', 'is_initial', 'is_final', 'order']


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'business_profile', 'allow_nested_services', 'has_pricing', 'is_active']
    list_filter = ['is_active', 'business_profile', 'allow_nested_services', 'has_pricing']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ServiceFieldInline, ServiceStatusInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('business_profile', 'name', 'code', 'description')
        }),
        ('Apparence', {
            'fields': ('icon', 'color')
        }),
        ('Configuration du workflow', {
            'fields': ('requires_approval', 'allow_nested_services', 'allowed_child_types')
        }),
        ('Configuration du pricing', {
            'fields': ('has_pricing', 'pricing_model')
        }),
        ('Valeurs par défaut', {
            'fields': ('default_values', 'settings')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['allowed_child_types']


@admin.register(ServiceField)
class ServiceFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_key', 'service_type', 'field_type', 'is_required', 'is_visible_in_list', 'order']
    list_filter = ['field_type', 'is_required', 'is_unique', 'is_searchable', 'is_visible_in_list', 'service_type']
    search_fields = ['name', 'field_key', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('service_type', 'name', 'field_key', 'field_type', 'description')
        }),
        ('Configuration', {
            'fields': ('is_required', 'is_unique', 'is_searchable', 'is_visible_in_list', 'order')
        }),
        ('Valeurs et validation', {
            'fields': ('default_value', 'validation_rules', 'options')
        }),
        ('Paramètres avancés', {
            'fields': ('settings', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'service_type', 'status_type', 'color_badge', 'is_initial', 'is_final', 'order']
    list_filter = ['status_type', 'is_initial', 'is_final', 'service_type']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('service_type', 'name', 'code', 'description')
        }),
        ('Apparence', {
            'fields': ('color', 'icon')
        }),
        ('Configuration du workflow', {
            'fields': ('status_type', 'order', 'is_initial', 'is_final', 'requires_comment')
        }),
        ('Transitions', {
            'fields': ('allowed_next_statuses',)
        }),
        ('Permissions', {
            'fields': ('required_permission',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['allowed_next_statuses']

    def color_badge(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.color,
            obj.name
        )
    color_badge.short_description = 'Couleur'


class ServiceStatusHistoryInline(admin.TabularInline):
    model = ServiceStatusHistory
    extra = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class ServiceCommentInline(admin.TabularInline):
    model = ServiceComment
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'content', 'is_internal', 'created_at']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'title', 'service_type', 'client_name',
        'current_status_badge', 'assigned_to', 'priority_badge',
        'start_date', 'created_at'
    ]
    list_filter = [
        'service_type', 'current_status', 'priority',
        'client_type', 'is_archived', 'created_at'
    ]
    search_fields = ['reference', 'title', 'client_name', 'client_email', 'description']
    readonly_fields = ['id', 'reference', 'created_at', 'updated_at']
    inlines = [ServiceStatusHistoryInline, ServiceCommentInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('organization', 'service_type', 'reference', 'title', 'description')
        }),
        ('Client', {
            'fields': ('client_type', 'client_name', 'client_email', 'client_phone', 'client_user')
        }),
        ('Gestion', {
            'fields': ('assigned_to', 'parent_service', 'current_status', 'priority')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'completed_at')
        }),
        ('Données dynamiques', {
            'fields': ('field_values',)
        }),
        ('Tarification', {
            'fields': ('estimated_amount', 'actual_amount', 'currency')
        }),
        ('Organisation', {
            'fields': ('tags', 'metadata', 'attachments')
        }),
        ('Statut', {
            'fields': ('is_archived',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def current_status_badge(self, obj):
        if obj.current_status:
            return format_html(
                '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
                obj.current_status.color,
                obj.current_status.name
            )
        return '-'
    current_status_badge.short_description = 'Statut'

    def priority_badge(self, obj):
        colors = {
            'low': '#6B7280',
            'normal': '#3B82F6',
            'high': '#F59E0B',
            'urgent': '#EF4444'
        }
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; border-radius: 3px; color: white;">{}</span>',
            colors.get(obj.priority, '#6B7280'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priorité'


@admin.register(ServiceStatusHistory)
class ServiceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['service', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['to_status', 'created_at']
    search_fields = ['service__reference', 'comment']
    readonly_fields = ['id', 'service', 'from_status', 'to_status', 'changed_by', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceActivity)
class ServiceActivityAdmin(admin.ModelAdmin):
    list_display = ['service', 'activity_type', 'title', 'user', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['service__reference', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('service', 'activity_type', 'user')
        }),
        ('Détails', {
            'fields': ('title', 'description', 'data')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ServiceComment)
class ServiceCommentAdmin(admin.ModelAdmin):
    list_display = ['service', 'user', 'content_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['service__reference', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('service', 'user', 'parent_comment')
        }),
        ('Contenu', {
            'fields': ('content', 'attachments')
        }),
        ('Options', {
            'fields': ('is_internal',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Contenu'


@admin.register(ServiceTemplate)
class ServiceTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'is_active', 'created_at']
    list_filter = ['is_active', 'service_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('service_type', 'name', 'description')
        }),
        ('Configuration', {
            'fields': ('default_field_values', 'default_title_template')
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
