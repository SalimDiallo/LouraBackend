from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip, PayslipItem, Permission, Role,
    Attendance, QRCodeSession
)


# ===============================
# PERMISSION SERIALIZERS
# ===============================

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""

    id = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'category', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_id(self, obj):
        """Convert UUID to string"""
        return str(obj.id) if obj.id else None


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
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

    def get_id(self, obj):
        """Convert UUID to string"""
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        """Convert UUID to string"""
        return str(obj.organization.id) if obj.organization else None

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

    id = serializers.SerializerMethodField()
    permission_count = serializers.SerializerMethodField()
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'description', 'permission_count', 'permissions', 'is_system_role', 'is_active']

    def get_id(self, obj):
        """Convert UUID to string"""
        return str(obj.id) if obj.id else None

    def get_permission_count(self, obj):
        return obj.permissions.count()


# Alias for create/update operations (uses same serializer as RoleSerializer)
RoleCreateSerializer = RoleSerializer


# ===============================
# EMPLOYEE SERIALIZERS
# ===============================

class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model - Full details"""

    id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_subdomain = serializers.CharField(source='organization.subdomain', read_only=True)
    department = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    position = serializers.SerializerMethodField()
    position_title = serializers.CharField(source='position.title', read_only=True)
    contract = serializers.SerializerMethodField()
    manager = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    emergency_contact = serializers.SerializerMethodField()

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
            'organization', 'organization_name', 'organization_subdomain',
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

    def get_id(self, obj):
        """Convert UUID to string"""
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        """Convert UUID to string"""
        return str(obj.organization.id) if obj.organization else None

    def get_department(self, obj):
        """Convert UUID to string"""
        return str(obj.department.id) if obj.department else None

    def get_position(self, obj):
        """Convert UUID to string"""
        return str(obj.position.id) if obj.position else None

    def get_contract(self, obj):
        """Convert UUID to string"""
        return str(obj.contract.id) if obj.contract else None

    def get_manager(self, obj):
        """Convert UUID to string"""
        return str(obj.manager.id) if obj.manager else None

    def get_emergency_contact(self, obj):
        """Ensure emergency_contact JSONField is properly serializable"""
        return obj.emergency_contact if obj.emergency_contact else None

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
    """Serializer pour les items de paie (primes et déductions)"""

    class Meta:
        model = PayslipItem
        fields = ['id', 'name', 'amount', 'is_deduction']
        read_only_fields = ['id']


class PayslipSerializer(serializers.ModelSerializer):
    """Serializer complet pour lecture de fiches de paie"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    payroll_period_name = serializers.CharField(source='payroll_period.name', read_only=True)
    period_start = serializers.DateField(source='payroll_period.start_date', read_only=True)
    period_end = serializers.DateField(source='payroll_period.end_date', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Inclure les items (primes et déductions) via des méthodes
    allowances = serializers.SerializerMethodField()
    deductions = serializers.SerializerMethodField()

    # Détails de l'employé
    employee_details = EmployeeListSerializer(source='employee', read_only=True)

    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'payroll_period', 'payroll_period_name', 'period_start', 'period_end',
            'base_salary', 'allowances', 'deductions',
            'gross_salary', 'total_deductions', 'net_salary',
            'currency', 'worked_hours', 'overtime_hours', 'leave_days_taken',
            'status', 'status_display', 'payment_method', 'payment_date',
            'payment_reference', 'payslip_file_url', 'notes',
            'created_at', 'updated_at', 'employee_details'
        ]
        read_only_fields = [
            'id', 'gross_salary', 'total_deductions', 'net_salary',
            'created_at', 'updated_at'
        ]

    def get_allowances(self, obj):
        """Retourner seulement les items qui sont des primes (is_deduction=False)"""
        items = obj.items.filter(is_deduction=False)
        return PayslipItemSerializer(items, many=True).data

    def get_deductions(self, obj):
        """Retourner seulement les items qui sont des déductions (is_deduction=True)"""
        items = obj.items.filter(is_deduction=True)
        return PayslipItemSerializer(items, many=True).data


class PayslipCreateSerializer(serializers.ModelSerializer):
    """Serializer pour création/modification de fiches de paie"""

    allowances = PayslipItemSerializer(many=True, required=False)
    deductions = PayslipItemSerializer(many=True, required=False)

    class Meta:
        model = Payslip
        fields = [
            'employee', 'payroll_period', 'base_salary',
            'allowances', 'deductions',
            'currency', 'worked_hours', 'overtime_hours', 'leave_days_taken',
            'payment_method', 'notes'
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

    def create(self, validated_data):
        # Extraire les items (primes et déductions)
        allowances_data = validated_data.pop('allowances', [])
        deductions_data = validated_data.pop('deductions', [])

        # Créer le payslip
        payslip = Payslip.objects.create(**validated_data)

        # Créer les primes (is_deduction=False)
        for allowance in allowances_data:
            # Remove is_deduction from allowance data to avoid duplicate argument
            allowance_copy = {k: v for k, v in allowance.items() if k != 'is_deduction'}
            PayslipItem.objects.create(
                payslip=payslip,
                is_deduction=False,
                **allowance_copy
            )

        # Créer les déductions (is_deduction=True)
        for deduction in deductions_data:
            # Remove is_deduction from deduction data to avoid duplicate argument
            deduction_copy = {k: v for k, v in deduction.items() if k != 'is_deduction'}
            PayslipItem.objects.create(
                payslip=payslip,
                is_deduction=True,
                **deduction_copy
            )

        # Calculer les totaux
        payslip.calculate_totals()

        return payslip

    def update(self, instance, validated_data):
        # Extraire les items
        allowances_data = validated_data.pop('allowances', None)
        deductions_data = validated_data.pop('deductions', None)

        # Mettre à jour les champs de base
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Si des allowances/deductions sont fournis, les remplacer complètement
        if allowances_data is not None or deductions_data is not None:
            # Supprimer tous les anciens items
            instance.items.all().delete()

            # Recréer les primes
            if allowances_data:
                for allowance in allowances_data:
                    # Remove is_deduction from allowance data to avoid duplicate argument
                    allowance_copy = {k: v for k, v in allowance.items() if k != 'is_deduction'}
                    PayslipItem.objects.create(
                        payslip=instance,
                        is_deduction=False,
                        **allowance_copy
                    )

            # Recréer les déductions
            if deductions_data:
                for deduction in deductions_data:
                    # Remove is_deduction from deduction data to avoid duplicate argument
                    deduction_copy = {k: v for k, v in deduction.items() if k != 'is_deduction'}
                    PayslipItem.objects.create(
                        payslip=instance,
                        is_deduction=True,
                        **deduction_copy
                    )

        # Recalculer les totaux
        instance.calculate_totals()

        return instance


# ===============================
# AUTHENTICATION SERIALIZERS
# ===============================

class EmployeeLoginSerializer(serializers.Serializer):
    """Serializer for employee login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Get employee by email (there should be only one active employee with this email)
        try:
            employee = Employee.objects.select_related('organization').get(email=email, is_active=True)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'Identifiants invalides.'
            })
        except Employee.MultipleObjectsReturned:
            # Si plusieurs employés avec le même email existent (cas rare), prendre le premier actif
            employee = Employee.objects.select_related('organization').filter(
                email=email,
                is_active=True
            ).first()
            if not employee:
                raise serializers.ValidationError({
                    'email': 'Identifiants invalides.'
                })

        # Check password
        if not employee.check_password(password):
            raise serializers.ValidationError({
                'password': 'Identifiants invalides.'
            })

        # Check if organization is active
        if not employee.organization.is_active:
            raise serializers.ValidationError({
                'email': 'L\'organisation associée à ce compte est désactivée.'
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


# ===============================
# ATTENDANCE SERIALIZERS
# ===============================

class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model"""

    id = serializers.SerializerMethodField()
    employee = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_id_number = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    approved_by_admin_name = serializers.SerializerMethodField()
    is_on_break = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_number', 'department_name',
            'user_email', 'user_full_name',
            'date', 'check_in', 'check_in_location', 'check_in_notes',
            'check_out', 'check_out_location', 'check_out_notes',
            'break_start', 'break_end', 'is_on_break', 'total_hours', 'break_duration',
            'status', 'approval_status', 'is_approved',
            'approved_by', 'approved_by_name', 'approved_by_admin', 'approved_by_admin_name',
            'approval_date', 'rejection_reason', 'notes', 'is_overtime', 'overtime_hours',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_hours', 'break_duration', 'is_overtime',
            'overtime_hours', 'created_at', 'updated_at'
        ]

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_employee(self, obj):
        return str(obj.employee.id) if obj.employee else None

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None

    def get_employee_id_number(self, obj):
        return obj.employee.employee_id if obj.employee else None

    def get_department_name(self, obj):
        return obj.employee.department.name if obj.employee and obj.employee.department else None

    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None

    def get_approved_by_admin_name(self, obj):
        return obj.approved_by_admin.get_full_name() if obj.approved_by_admin else None

    def get_is_on_break(self, obj):
        """Check if currently on break"""
        return bool(obj.break_start and not obj.break_end)


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records"""

    class Meta:
        model = Attendance
        fields = [
            'employee', 'date', 'check_in', 'check_in_location', 'check_in_notes',
            'check_out', 'check_out_location', 'check_out_notes',
            'break_start', 'break_end', 'status', 'notes'
        ]

    def validate(self, attrs):
        # Validate check times
        check_in = attrs.get('check_in')
        check_out = attrs.get('check_out')
        break_start = attrs.get('break_start')
        break_end = attrs.get('break_end')

        if check_out and check_in and check_out <= check_in:
            raise serializers.ValidationError({
                'check_out': 'L\'heure de sortie doit être après l\'heure d\'entrée.'
            })

        if break_end and break_start and break_end <= break_start:
            raise serializers.ValidationError({
                'break_end': 'L\'heure de fin de pause doit être après l\'heure de début.'
            })

        if break_start and check_in and break_start < check_in:
            raise serializers.ValidationError({
                'break_start': 'La pause doit commencer après le pointage d\'entrée.'
            })

        if break_end and check_out and break_end > check_out:
            raise serializers.ValidationError({
                'break_end': 'La pause doit finir avant le pointage de sortie.'
            })

        return attrs


class AttendanceCheckInSerializer(serializers.Serializer):
    """Serializer for employee check-in"""

    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class AttendanceCheckOutSerializer(serializers.Serializer):
    """Serializer for employee check-out"""

    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class AttendanceApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting attendance"""

    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class AttendanceBreakSerializer(serializers.Serializer):
    """Serializer for break start/end"""

    notes = serializers.CharField(required=False, allow_blank=True)


class AttendanceStatsSerializer(serializers.Serializer):
    """Serializer for attendance statistics"""

    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    on_leave_days = serializers.IntegerField()
    total_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    overtime_hours = serializers.DecimalField(max_digits=8, decimal_places=2)
    average_hours_per_day = serializers.DecimalField(max_digits=5, decimal_places=2)


# ===============================
# QR CODE ATTENDANCE SERIALIZERS
# ===============================

class QRCodeSessionSerializer(serializers.ModelSerializer):
    """Serializer for QRCodeSession model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    qr_code_data = serializers.SerializerMethodField()

    class Meta:
        model = QRCodeSession
        fields = [
            'id', 'organization', 'session_token', 'qr_code_data',
            'employee', 'employee_name', 'employee_email',
            'created_by', 'created_by_name',
            'expires_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_token', 'organization', 'created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None

    def get_qr_code_data(self, obj):
        return obj.get_qr_code_data()


class QRCodeSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a QR code session"""

    employee = serializers.UUIDField()
    expires_in_minutes = serializers.IntegerField(default=5, min_value=1, max_value=60)

    def validate_employee(self, value):
        from hr.models import Employee
        try:
            employee = Employee.objects.get(id=value, organization=self.context['organization'])
            if not employee.is_active:
                raise serializers.ValidationError("Cet employé n'est pas actif")
            return employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employé introuvable")

    def create(self, validated_data):
        import secrets
        from datetime import timedelta
        from django.utils import timezone
        from hr.models import QRCodeSession

        employee = validated_data['employee']
        expires_in_minutes = validated_data['expires_in_minutes']

        # Générer un token unique
        session_token = secrets.token_urlsafe(32)

        # Calculer l'expiration
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)

        # Créer la session
        session = QRCodeSession.objects.create(
            organization=self.context['organization'],
            employee=employee,
            session_token=session_token,
            expires_at=expires_at,
            created_by=self.context['request'].user if hasattr(self.context['request'].user, 'adminuser') else None,
            is_active=True
        )

        return session


class QRAttendanceCheckInSerializer(serializers.Serializer):
    """Serializer for checking in via QR code"""

    session_token = serializers.CharField()
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_session_token(self, value):
        from hr.models import QRCodeSession
        try:
            session = QRCodeSession.objects.get(
                session_token=value,
                is_active=True
            )

            if session.is_expired():
                raise serializers.ValidationError("Cette session QR a expiré")

            return session
        except QRCodeSession.DoesNotExist:
            raise serializers.ValidationError("Session QR invalide")

    def create(self, validated_data):
        from hr.models import Attendance
        from django.utils import timezone

        session = validated_data['session_token']
        location = validated_data.get('location', '')
        notes = validated_data.get('notes', '')

        # Créer ou récupérer le pointage du jour
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            employee=session.employee,
            date=today,
            defaults={
                'check_in': timezone.now(),
                'check_in_location': location,
                'check_in_notes': notes,
                'status': 'present',
            }
        )

        if not created:
            # Si le pointage existe déjà, mise à jour
            if not attendance.check_in:
                attendance.check_in = timezone.now()
                attendance.check_in_location = location
                attendance.check_in_notes = notes
                attendance.status = 'present'
                attendance.save()

        # Désactiver la session après utilisation
        session.is_active = False
        session.save()

        return attendance
