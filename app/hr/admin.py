from django.contrib import admin
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip, PayslipItem,
    Permission, Role
)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category']
    list_filter = ['category']
    search_fields = ['code', 'name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'is_system_role', 'is_active']
    list_filter = ['organization', 'is_system_role', 'is_active']
    search_fields = ['name', 'code']
    filter_horizontal = ['permissions']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'employee_id', 'organization', 'department', 'assigned_role', 'employment_status', 'is_active']
    list_filter = ['organization', 'department', 'assigned_role', 'employment_status', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    filter_horizontal = ['custom_permissions']
    fieldsets = (
        ('Informations de base', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'avatar_url')
        }),
        ('Organisation', {
            'fields': ('organization', 'employee_id', 'department', 'position', 'contract')
        }),
        ('Emploi', {
            'fields': ('hire_date', 'termination_date', 'manager', 'assigned_role', 'employment_status')
        }),
        ('Permissions', {
            'fields': ('custom_permissions',),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': ('language', 'timezone')
        }),
        ('Statut', {
            'fields': ('is_active', 'email_verified', 'last_login')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'head', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'code', 'organization', 'min_salary', 'max_salary', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['title', 'code']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['employee', 'contract_type', 'start_date', 'end_date', 'base_salary', 'currency', 'is_active']
    list_filter = ['contract_type', 'is_active', 'start_date']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    date_hierarchy = 'start_date'


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'default_days_per_year', 'is_paid', 'requires_approval', 'is_active']
    list_filter = ['organization', 'is_paid', 'requires_approval', 'is_active']
    search_fields = ['name', 'code']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_days', 'used_days', 'pending_days', 'available_days']
    list_filter = ['year', 'leave_type']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'approver']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'reason']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'start_date', 'end_date', 'payment_date', 'status']
    list_filter = ['organization', 'status', 'start_date']
    search_fields = ['name']
    date_hierarchy = 'start_date'


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ['employee', 'payroll_period', 'gross_salary', 'net_salary', 'currency', 'status', 'payment_date']
    list_filter = ['status', 'payroll_period', 'payment_date']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['gross_salary', 'total_deductions', 'net_salary', 'created_at', 'updated_at']


@admin.register(PayslipItem)
class PayslipItemAdmin(admin.ModelAdmin):
    list_display = ['payslip', 'item_type', 'description', 'amount', 'quantity', 'total']
    list_filter = ['item_type']
    search_fields = ['description']
    readonly_fields = ['total']
