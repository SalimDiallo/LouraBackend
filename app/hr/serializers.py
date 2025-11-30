from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip, PayslipItem, Permission, Role
)


# ===============================
# PERMISSION SERIALIZERS
# ===============================

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""

    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'category', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""

    permissions = PermissionSerializer(many=True, read_only=True)
    permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of permission codes to assign to this role"
    )
    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'organization', 'code', 'name', 'description',
            'permissions', 'permission_codes', 'permission_count',
            'is_system_role', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_system_role', 'created_at', 'updated_at']

    def get_permission_count(self, obj):
        return obj.permissions.count()

    def create(self, validated_data):
        permission_codes = validated_data.pop('permission_codes', [])
        role = Role.objects.create(**validated_data)

        if permission_codes:
            permissions = Permission.objects.filter(code__in=permission_codes)
            role.permissions.set(permissions)

        return role

    def update(self, instance, validated_data):
        permission_codes = validated_data.pop('permission_codes', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update permissions if provided
        if permission_codes is not None:
            permissions = Permission.objects.filter(code__in=permission_codes)
            instance.permissions.set(permissions)

        return instance


class RoleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing roles"""

    permission_count = serializers.SerializerMethodField()
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'description', 'permission_count', 'permissions', 'is_system_role', 'is_active']

    def get_permission_count(self, obj):
        return obj.permissions.count()


# Alias for create/update operations (uses same serializer as RoleSerializer)
RoleCreateSerializer = RoleSerializer


# ===============================
# EMPLOYEE SERIALIZERS
# ===============================

class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model - Full details"""

    full_name = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    manager_name = serializers.SerializerMethodField()

    # Role information
    role = RoleListSerializer(source='assigned_role', read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='assigned_role',
        write_only=True,
        required=False,
        allow_null=True
    )

    # All permissions (role + custom)
    all_permissions = serializers.SerializerMethodField()

    # Custom permissions
    custom_permissions = PermissionSerializer(many=True, read_only=True)
    custom_permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Employee
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone',
            'avatar_url', 'employee_id', 'date_of_birth', 'gender', 'address', 'city', 'country',
            'organization', 'organization_name',
            'department', 'department_name', 'position', 'position_title',
            'contract', 'hire_date', 'termination_date', 'manager', 'manager_name',
            'emergency_contact', 'role', 'role_id', 'employment_status', 'language', 'timezone',
            'all_permissions', 'custom_permissions', 'custom_permission_codes',
            'is_active', 'email_verified', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'organization': {'required': False},  # Will be set by view
        }

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None

    def get_all_permissions(self, obj):
        """Get all permissions (role + custom)"""
        permissions = obj.get_all_permissions()
        return PermissionSerializer(permissions, many=True).data


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating employees"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='assigned_role',
        required=False,
        allow_null=True
    )

    custom_permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Employee
        fields = [
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'phone', 'employee_id', 'date_of_birth', 'gender', 'address', 'city', 'country',
            'department', 'position', 'hire_date', 'manager', 'emergency_contact',
            'role_id', 'employment_status', 'custom_permission_codes'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        custom_permission_codes = validated_data.pop('custom_permission_codes', [])

        # Organization will be set by the view
        employee = Employee.objects.create_user(
            password=password,
            **validated_data
        )

        # Add custom permissions if provided
        if custom_permission_codes:
            permissions = Permission.objects.filter(code__in=custom_permission_codes)
            employee.custom_permissions.set(permissions)

        return employee


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for listing employees - Minimal info"""

    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    role_name = serializers.CharField(source='assigned_role.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'email', 'full_name', 'employee_id',
            'department_name', 'position_title', 'role_name',
            'employment_status', 'is_active'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employees"""

    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='assigned_role',
        required=False,
        allow_null=True
    )

    custom_permission_codes = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'phone', 'avatar_url',
            'employee_id', 'date_of_birth', 'gender', 'address', 'city', 'country',
            'department', 'position', 'hire_date',
            'termination_date', 'manager', 'emergency_contact', 'role_id', 'employment_status',
            'language', 'timezone', 'is_active', 'custom_permission_codes'
        ]

    def update(self, instance, validated_data):
        custom_permission_codes = validated_data.pop('custom_permission_codes', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update custom permissions if provided
        if custom_permission_codes is not None:
            permissions = Permission.objects.filter(code__in=custom_permission_codes)
            instance.custom_permissions.set(permissions)

        return instance


# ===============================
# HR CONFIGURATION SERIALIZERS
# ===============================

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""

    head_name = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'organization', 'name', 'code', 'description',
            'head', 'head_name', 'employee_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None

    def get_employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for Position model"""

    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Position
        fields = [
            'id', 'organization', 'title', 'code', 'description',
            'min_salary', 'max_salary', 'employee_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for Contract model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    salary_period_display = serializers.CharField(source='get_salary_period_display', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id', 'employee', 'employee_name', 'contract_type',
            'contract_type_display', 'start_date', 'end_date',
            'base_salary', 'currency', 'salary_period', 'salary_period_display',
            'hours_per_week', 'description', 'contract_file_url',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===============================
# LEAVE MANAGEMENT SERIALIZERS
# ===============================

class LeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for LeaveType model"""

    class Meta:
        model = LeaveType
        fields = [
            'id', 'organization', 'name', 'code', 'description',
            'default_days_per_year', 'is_paid', 'requires_approval',
            'max_consecutive_days', 'color', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    available_days = serializers.ReadOnlyField()

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'year', 'total_days', 'used_days', 'pending_days', 'available_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'available_days']


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_color = serializers.CharField(source='leave_type.color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'leave_type_color', 'start_date', 'end_date', 'start_half_day',
            'end_half_day', 'total_days', 'reason', 'attachment_url',
            'status', 'status_display', 'approver_name',
            'approval_date', 'approval_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee', 'status', 'approval_date',
            'approval_notes', 'created_at', 'updated_at'
        ]

    def get_approver_name(self, obj):
        """Retourne le nom de l'approbateur (Employee ou AdminUser)"""
        return obj.get_approver_name()

    def validate(self, attrs):
        """Validate leave request dates and availability"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': 'La date de fin doit être après la date de début.'
            })

        return attrs


class LeaveRequestApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting leave requests"""

    approval_notes = serializers.CharField(required=False, allow_blank=True)


# ===============================
# PAYROLL SERIALIZERS
# ===============================

class PayrollPeriodSerializer(serializers.ModelSerializer):
    """Serializer for PayrollPeriod model"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payslip_count = serializers.SerializerMethodField()
    total_net_salary = serializers.SerializerMethodField()

    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'organization', 'name', 'start_date', 'end_date',
            'payment_date', 'status', 'status_display', 'notes',
            'payslip_count', 'total_net_salary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def get_payslip_count(self, obj):
        return obj.payslips.count()

    def get_total_net_salary(self, obj):
        from django.db.models import Sum
        total = obj.payslips.aggregate(total=Sum('net_salary'))['total']
        return float(total) if total else 0.0


class PayslipItemSerializer(serializers.ModelSerializer):
    """Serializer for PayslipItem model"""

    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)

    class Meta:
        model = PayslipItem
        fields = [
            'id', 'payslip', 'item_type', 'item_type_display',
            'description', 'amount', 'quantity', 'total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']


class PayslipSerializer(serializers.ModelSerializer):
    """Serializer for Payslip model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    payroll_period_name = serializers.CharField(source='payroll_period.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PayslipItemSerializer(many=True, read_only=True)

    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'payroll_period', 'payroll_period_name', 'base_salary',
            'overtime_pay', 'bonuses', 'allowances', 'tax',
            'social_security', 'other_deductions', 'gross_salary',
            'total_deductions', 'net_salary', 'currency',
            'worked_hours', 'overtime_hours', 'leave_days_taken',
            'status', 'status_display', 'payment_method', 'payment_date',
            'payment_reference', 'notes', 'payslip_file_url',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'gross_salary', 'total_deductions', 'net_salary',
            'created_at', 'updated_at'
        ]


class PayslipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payslips"""

    class Meta:
        model = Payslip
        fields = [
            'employee', 'payroll_period', 'base_salary', 'overtime_pay',
            'bonuses', 'allowances', 'tax', 'social_security',
            'other_deductions', 'currency', 'worked_hours',
            'overtime_hours', 'leave_days_taken', 'payment_method', 'notes'
        ]

    def validate(self, attrs):
        """Validate that employee belongs to same organization as payroll period"""
        employee = attrs.get('employee')
        payroll_period = attrs.get('payroll_period')

        if employee and payroll_period:
            if employee.organization != payroll_period.organization:
                raise serializers.ValidationError({
                    'employee': "L'employé doit appartenir à la même organisation que la période de paie."
                })

        return attrs


# ===============================
# AUTHENTICATION SERIALIZERS
# ===============================

class EmployeeLoginSerializer(serializers.Serializer):
    """Serializer for employee login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    organization_subdomain = serializers.CharField(
        help_text="Subdomain de l'organisation"
    )

    def validate(self, attrs):
        from core.models import Organization

        email = attrs.get('email')
        password = attrs.get('password')
        organization_subdomain = attrs.get('organization_subdomain')

        # Get organization
        try:
            organization = Organization.objects.get(subdomain=organization_subdomain)
        except Organization.DoesNotExist:
            raise serializers.ValidationError({
                'organization_subdomain': 'Organisation non trouvée.'
            })

        # Get employee
        try:
            employee = Employee.objects.get(email=email, organization=organization)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'Identifiants invalides.'
            })

        # Check password
        if not employee.check_password(password):
            raise serializers.ValidationError({
                'password': 'Identifiants invalides.'
            })

        # Check if employee is active
        if not employee.is_active:
            raise serializers.ValidationError({
                'email': 'Ce compte est désactivé.'
            })

        # Check if organization is active
        if not organization.is_active:
            raise serializers.ValidationError({
                'organization_subdomain': 'Cette organisation est désactivée.'
            })

        attrs['employee'] = employee
        return attrs


class EmployeeChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing employee password"""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les nouveaux mots de passe ne correspondent pas."
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value
