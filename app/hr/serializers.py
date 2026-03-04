from core.models import BaseUser
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from core.models import Permission, Role
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveRequest, LeaveBalance,
    PayrollPeriod, Payslip, PayslipItem, PayrollAdvance,
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

    def _resolve_permission_dependencies(self, permission_codes):
        """
        Résout les dépendances de permissions en ajoutant automatiquement
        les permissions requises.
        """
        from core.permission_dependencies import get_all_required_permissions
        return get_all_required_permissions(permission_codes)

    def create(self, validated_data):
        permission_codes = validated_data.pop('permission_codes', [])
        role = Role.objects.create(**validated_data)

        if permission_codes:
            # Auto-ajouter les dépendances manquantes
            complete_codes = self._resolve_permission_dependencies(permission_codes)
            permissions = Permission.objects.filter(code__in=complete_codes)
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
            # Auto-ajouter les dépendances manquantes
            complete_codes = self._resolve_permission_dependencies(permission_codes)
            permissions = Permission.objects.filter(code__in=complete_codes)
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
    department_name = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    position_title = serializers.SerializerMethodField()
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

    def get_department_name(self, obj):
        """Get department name safely"""
        return obj.department.name if obj.department else None

    def get_position(self, obj):
        """Convert UUID to string"""
        return str(obj.position.id) if obj.position else None

    def get_position_title(self, obj):
        """Get position title safely"""
        return obj.position.title if obj.position else None

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

    def _resolve_permission_dependencies(self, permission_codes):
        """
        Résout les dépendances de permissions en ajoutant automatiquement
        les permissions requises.
        """
        from core.permission_dependencies import get_all_required_permissions
        return get_all_required_permissions(permission_codes)

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        custom_permission_codes = validated_data.pop('custom_permission_codes', [])

        # Organization will be set by the view
        employee = Employee.objects.create_user(
            password=password,
            **validated_data
        )

        # Add custom permissions if provided (with dependencies resolved)
        if custom_permission_codes:
            complete_codes = self._resolve_permission_dependencies(custom_permission_codes)
            permissions = Permission.objects.filter(code__in=complete_codes)
            employee.custom_permissions.set(permissions)

        return employee


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer for listing employees - Minimal info with salary"""

    full_name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    position_title = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    # Salary information from active contract
    base_salary = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    salary_period = serializers.SerializerMethodField()
    salary_period_display = serializers.SerializerMethodField()
    contract_type = serializers.SerializerMethodField()
    contract_type_display = serializers.SerializerMethodField()
    gender = serializers.CharField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'email', 'full_name', 'employee_id',
            'department', 'department_name', 'position_title', 'role_name', 'gender',
            'employment_status', 'is_active', 'hire_date',
            # Salary fields
            'base_salary', 'currency', 'salary_period', 'salary_period_display',
            'contract_type', 'contract_type_display'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_department(self, obj):
        """Convert department UUID to string"""
        return str(obj.department.id) if obj.department else None

    def get_department_name(self, obj):
        """Get department name safely"""
        return obj.department.name if obj.department else None

    def get_position_title(self, obj):
        """Get position title safely"""
        return obj.position.title if obj.position else None

    def get_role_name(self, obj):
        """Get role name safely"""
        return obj.assigned_role.name if obj.assigned_role else None

    def _get_active_contract(self, obj):
        """Récupère le contrat actif de l'employé"""
        return obj.contracts.filter(is_active=True).first()

    def get_base_salary(self, obj):
        contract = self._get_active_contract(obj)
        return float(contract.base_salary) if contract else None

    def get_currency(self, obj):
        contract = self._get_active_contract(obj)
        return contract.currency if contract else None

    def get_salary_period(self, obj):
        contract = self._get_active_contract(obj)
        return contract.salary_period if contract else None

    def get_salary_period_display(self, obj):
        contract = self._get_active_contract(obj)
        return contract.get_salary_period_display() if contract else None

    def get_contract_type(self, obj):
        contract = self._get_active_contract(obj)
        return contract.contract_type if contract else None

    def get_contract_type_display(self, obj):
        contract = self._get_active_contract(obj)
        return contract.get_contract_type_display() if contract else None


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

    def _resolve_permission_dependencies(self, permission_codes):
        """
        Résout les dépendances de permissions en ajoutant automatiquement
        les permissions requises.
        """
        from core.permission_dependencies import get_all_required_permissions
        return get_all_required_permissions(permission_codes)

    def update(self, instance, validated_data):
        custom_permission_codes = validated_data.pop('custom_permission_codes', None)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update custom permissions if provided (with dependencies resolved)
        if custom_permission_codes is not None:
            complete_codes = self._resolve_permission_dependencies(custom_permission_codes)
            permissions = Permission.objects.filter(code__in=complete_codes)
            instance.custom_permissions.set(permissions)

        return instance


# ===============================
# HR CONFIGURATION SERIALIZERS
# ===============================

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""

    head_name = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    head_type = serializers.SerializerMethodField()
    # Champ "manager" en lecture (alias de head pour le frontend)
    manager = serializers.SerializerMethodField()
    # Champ "manager" en écriture (alias de head pour rétrocompatibilité)
    manager_write = serializers.UUIDField(write_only=True, required=False, allow_null=True, source='manager_input')
    # parent_department name pour affichage
    parent_department_name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'organization', 'name', 'code', 'description',
            'head', 'manager', 'manager_write', 'head_name', 'head_type',
            'parent_department', 'parent_department_name',
            'employee_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def get_head_name(self, obj):
        return obj.get_head_name()

    def get_head_type(self, obj):
        """Retourne le type du responsable (employee ou admin)"""
        if obj.head:
            return obj.head.user_type
        return None

    def get_manager(self, obj):
        """Retourne l'ID du head comme string (alias manager pour le frontend)"""
        return str(obj.head_id) if obj.head_id else None

    def get_parent_department_name(self, obj):
        """Retourne le nom du département parent"""
        return obj.parent_department.name if obj.parent_department else None

    def get_employee_count(self, obj):
        return obj.employees.filter(employment_status='active').count()

    def create(self, validated_data):
        """Gère la création avec le head (accepte head ou manager)"""
        # Accepte manager_input comme alias de head (rétrocompatibilité)
        manager_id = validated_data.pop('manager_input', None)
        if manager_id and 'head' not in validated_data:
            validated_data['head'] = BaseUser.objects.get(id=manager_id)
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        manager_id = validated_data.pop('manager_input', None)
        if manager_id is not None:
            if manager_id:
                instance.head = BaseUser.objects.get(id=manager_id)
            else:
                instance.head = None
        
        return super().update(instance, validated_data)


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
    """
    Serializer for Contract model
    
    Inclut des informations supplémentaires pour aider à gérer
    la contrainte d'un seul contrat actif par employé.
    """

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    contract_type_display = serializers.CharField(source='get_contract_type_display', read_only=True)
    salary_period_display = serializers.CharField(source='get_salary_period_display', read_only=True)
    
    # Informations supplémentaires pour la gestion des contrats
    is_expired = serializers.SerializerMethodField()
    employee_contract_count = serializers.SerializerMethodField()
    has_other_active_contract = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'employee', 'employee_name', 'contract_type',
            'contract_type_display', 'start_date', 'end_date',
            'base_salary', 'currency', 'salary_period', 'salary_period_display',
            'hours_per_week', 'description', 'contract_file_url',
            'is_active', 'is_expired', 'employee_contract_count', 
            'has_other_active_contract', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_expired', 
                           'employee_contract_count', 'has_other_active_contract']

    def get_is_expired(self, obj):
        """Vérifie si le contrat a expiré."""
        return obj.is_expired

    def get_employee_contract_count(self, obj):
        """Retourne le nombre total de contrats de l'employé."""
        return obj.employee.contracts.count()

    def get_has_other_active_contract(self, obj):
        """Vérifie si l'employé a un autre contrat actif (différent de celui-ci)."""
        return obj.employee.contracts.filter(is_active=True).exclude(pk=obj.pk).exists()

    def validate(self, attrs):
        """
        Validation personnalisée pour informer sur les contrats actifs existants.
        Note: Le modèle Contract.save() gère automatiquement la désactivation
        des autres contrats, donc on laisse juste passer avec un warning.
        """
        employee = attrs.get('employee') or (self.instance.employee if self.instance else None)
        is_active = attrs.get('is_active', True)
        
        if employee and is_active:
            # Vérifier s'il y a d'autres contrats actifs
            existing_active = Contract.objects.filter(
                employee=employee,
                is_active=True
            )
            if self.instance:
                existing_active = existing_active.exclude(pk=self.instance.pk)
            
            if existing_active.exists():
                # On ajoute un contexte pour le frontend mais on laisse passer
                # car la logique de save() gère la désactivation automatique
                pass
        
        return attrs


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


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest model"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_name = serializers.SerializerMethodField()
    leave_type_color = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'leave_type_color', 'title', 'start_date', 'end_date', 'start_half_day',
            'end_half_day', 'total_days', 'reason', 'attachment_url',
            'status', 'status_display', 'approver_name',
            'approval_date', 'approval_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'employee', 'status', 'approval_date',
            'approval_notes', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'leave_type': {'required': False, 'allow_null': True},
        }

    def get_leave_type_name(self, obj):
        return obj.leave_type.name if obj.leave_type else None

    def get_leave_type_color(self, obj):
        return obj.leave_type.color if obj.leave_type else None

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

        # Si pas de leave_type, le titre est obligatoire
        leave_type = attrs.get('leave_type')
        title = attrs.get('title', '').strip()
        if not leave_type and not title:
            raise serializers.ValidationError({
                'title': 'Le titre est obligatoire si aucun type de congé n\'est sélectionné.'
            })

        # Vérifier le solde de congés disponible
        # Note: employee sera ajouté dans perform_create, donc on doit vérifier dans le viewset
        # OU on peut vérifier ici si on a l'instance (update) ou le context (create)
        employee = self.context.get('employee') if hasattr(self, 'context') else None
        total_days = attrs.get('total_days')

        if employee and leave_type and total_days and start_date:
            from hr.models import LeaveBalance
            year = start_date.year
            can_take, message = LeaveBalance.check_balance(employee, leave_type, total_days, year)
            if not can_take:
                raise serializers.ValidationError({
                    'total_days': message
                })

        return attrs


class LeaveRequestApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting leave requests"""

    approval_notes = serializers.CharField(required=False, allow_blank=True)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance model - Global balance only"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    used_days = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    pending_days = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    remaining_days = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_name', 'year', 'allocated_days',
            'used_days', 'pending_days', 'remaining_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
        extra_kwargs = {
            'payment_date': {'required': False, 'allow_null': True},
        }

    def get_payslip_count(self, obj):
        return obj.payslips.count()

    def get_total_net_salary(self, obj):
        from django.db.models import Sum
        total = obj.payslips.aggregate(total=Sum('net_salary'))['total']
        return float(total) if total else 0.0

    def validate_name(self, value):
        """Valide que le nom de la période est unique pour cette organisation"""
        # Récupérer l'organisation depuis le contexte (sera fournie par le viewset)
        request = self.context.get('request')
        if request:
            # Essayer de récupérer l'organisation via subdomain ou query params
            org_subdomain = request.query_params.get('organization_subdomain')
            if org_subdomain:
                from core.models import Organization
                try:
                    organization = Organization.objects.get(subdomain=org_subdomain)
                    # Vérifier si une période avec ce nom existe déjà
                    existing = PayrollPeriod.objects.filter(
                        organization=organization,
                        name=value
                    )
                    # Exclure l'instance actuelle en cas de mise à jour
                    if self.instance:
                        existing = existing.exclude(pk=self.instance.pk)
                    
                    if existing.exists():
                        raise serializers.ValidationError(
                            f"Une période de paie avec le nom \"{value}\" existe déjà pour cette organisation."
                        )
                except Organization.DoesNotExist:
                    pass
        return value


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
    payroll_period_name = serializers.SerializerMethodField()
    period_start = serializers.SerializerMethodField()
    period_end = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    display_name = serializers.SerializerMethodField()

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
            'description', 'display_name',
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

    def get_payroll_period_name(self, obj):
        """Retourne le nom de la période ou None si pas de période"""
        return obj.payroll_period.name if obj.payroll_period else None

    def get_period_start(self, obj):
        """Retourne la date de début de la période ou None"""
        return obj.payroll_period.start_date if obj.payroll_period else None

    def get_period_end(self, obj):
        """Retourne la date de fin de la période ou None"""
        return obj.payroll_period.end_date if obj.payroll_period else None

    def get_display_name(self, obj):
        """Retourne un nom d'affichage pour la fiche de paie"""
        return obj.get_display_name()

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
    
    # IDs des avances à lier à cette fiche de paie
    advance_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
        help_text="Liste des IDs d'avances à déduire de cette fiche de paie"
    )

    class Meta:
        model = Payslip
        fields = [
            'employee', 'payroll_period', 'description', 'base_salary',
            'allowances', 'deductions', 'advance_ids',
            'currency', 'worked_hours', 'overtime_hours', 'leave_days_taken',
            'payment_method', 'notes'
        ]
        extra_kwargs = {
            'payroll_period': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        """Validate payroll data"""
        employee = attrs.get('employee') or (self.instance.employee if self.instance else None)
        payroll_period = attrs.get('payroll_period', self.instance.payroll_period if self.instance else None)
        description = attrs.get('description', self.instance.description if self.instance else '')

        # Si pas de période et pas de description, encourager une description
        if not payroll_period and not description:
            # Générer une description par défaut basée sur la date
            from django.utils import timezone
            now = timezone.now()
            attrs['description'] = f"Paie {now.strftime('%B %Y')}"

        # Valider que l'employé appartient à la même organisation que la période
        if employee and payroll_period:
            if employee.organization != payroll_period.organization:
                raise serializers.ValidationError({
                    'employee': "L'employé doit appartenir à la même organisation que la période de paie."
                })


        # Validate advance_ids if provided
        advance_ids = attrs.get('advance_ids', [])
        if advance_ids and employee:
            advances = PayrollAdvance.objects.filter(
                id__in=advance_ids,
                employee=employee,
                status=PayrollAdvance.AdvanceStatus.APPROVED
            )
            if advances.count() != len(advance_ids):
                raise serializers.ValidationError({
                    'advance_ids': "Certaines avances sont invalides ou ne sont pas dans le statut 'approuvé'."
                })

        return attrs

    def create(self, validated_data):
        # Extraire les items (primes et déductions)
        allowances_data = validated_data.pop('allowances', [])
        deductions_data = validated_data.pop('deductions', [])
        advance_ids = validated_data.pop('advance_ids', [])

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

        # Lier les avances au payslip et mettre à jour leur statut
        if advance_ids:
            PayrollAdvance.objects.filter(
                id__in=advance_ids,
                employee=payslip.employee,
                status=PayrollAdvance.AdvanceStatus.APPROVED
            ).update(
                payslip=payslip,
                status=PayrollAdvance.AdvanceStatus.DEDUCTED
            )

        # Calculer les totaux
        payslip.calculate_totals()

        return payslip

    def update(self, instance, validated_data):
        # Extraire les items
        allowances_data = validated_data.pop('allowances', None)
        deductions_data = validated_data.pop('deductions', None)
        advance_ids = validated_data.pop('advance_ids', [])

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

    id = serializers.UUIDField(read_only=True)
    employee = serializers.CharField(source='user_id', read_only=True)
    employee_name = serializers.ReadOnlyField(source='user_full_name')
    employee_id_number = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    is_on_break = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_number', 'department_name',
            'user', 'user_email', 'user_full_name',
            'date', 'check_in', 'check_in_location', 'check_in_notes',
            'check_out', 'check_out_location', 'check_out_notes',
            'break_start', 'break_end', 'is_on_break', 'total_hours', 'break_duration',
            'status', 'approval_status', 'is_approved',
            'approved_by', 'approved_by_name',
            'approval_date', 'rejection_reason', 'notes', 'is_overtime', 'overtime_hours',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_hours', 'break_duration', 'is_overtime',
            'overtime_hours', 'created_at', 'updated_at'
        ]

    def get_employee_id_number(self, obj):
        # Access employee_id if user is an Employee
        if hasattr(obj.user, 'employee_id'):
            return obj.user.employee_id
        return None

    def get_department_name(self, obj):
        # Access department name if user is an Employee
        if hasattr(obj.user, 'department') and obj.user.department:
            return obj.user.department.name
        return None

    def get_is_on_break(self, obj):
        """Check if currently on break"""
        return bool(obj.break_start and not obj.break_end)


class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records"""

    # Allow using 'employee' as an alias for 'user' in input
    employee = serializers.PrimaryKeyRelatedField(
        queryset=BaseUser.objects.all(),
        source='user',
        required=False
    )

    class Meta:
        model = Attendance
        fields = [
            'user', 'employee', 'date', 'check_in', 'check_in_location', 'check_in_notes',
            'check_out', 'check_out_location', 'check_out_notes',
            'break_start', 'break_end', 'status', 'notes'
        ]
        extra_kwargs = {
            'user': {'required': False},
        }

    def validate(self, attrs):
        # Handle employee/user alias
        if 'user' not in attrs and 'employee' in attrs:
            attrs['user'] = attrs.pop('employee')
        
        if 'user' not in attrs:
            raise serializers.ValidationError({'user': 'Ce champ est obligatoire.'})

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
    """Serializer for QRCodeSession model - supports single and multiple employees"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    qr_code_data = serializers.SerializerMethodField()
    
    # Multi-employee support
    all_employees = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()
    mode = serializers.SerializerMethodField()

    class Meta:
        model = QRCodeSession
        fields = [
            'id', 'organization', 'session_token', 'qr_code_data',
            'employee', 'employee_name', 'employee_email',
            'all_employees', 'employee_count', 'mode',
            'created_by', 'created_by_name',
            'expires_at', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_token', 'organization', 'created_by', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None

    def get_all_employees(self, obj):
        """Return list of all employees this QR is valid for"""
        if hasattr(obj, '_all_employees') and obj._all_employees:
            return [
                {
                    'id': str(emp.id),
                    'full_name': emp.get_full_name(),
                    'email': emp.email,
                    'employee_id': emp.employee_id,
                }
                for emp in obj._all_employees
            ]
        # Fallback for single employee
        return [
            {
                'id': str(obj.employee.id),
                'full_name': obj.employee.get_full_name(),
                'email': obj.employee.email,
                'employee_id': obj.employee.employee_id,
            }
        ] if obj.employee else []
    
    def get_employee_count(self, obj):
        """Return number of employees this QR is valid for"""
        if hasattr(obj, '_all_employees') and obj._all_employees:
            return len(obj._all_employees)
        return 1 if obj.employee else 0
    
    def get_mode(self, obj):
        """Return the attendance mode (auto, check_in, check_out)"""
        return getattr(obj, 'mode', 'auto')

    def get_qr_code_data(self, obj):
        """
        Generate QR code data - SIMPLIFIED to just session_token.
        Keeping it simple ensures the QR code is easy to scan.
        All other info (employees, mode) is fetched from API during check-in.
        """
        # Just return the session token - it's all we need!
        # The backend will look up all details from this token
        return obj.session_token


class QRCodeSessionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a QR code session.
    Supports both single employee and multiple employees (bulk mode).
    """

    # Single employee (backward compatible)
    employee = serializers.UUIDField(required=False, allow_null=True)
    
    # Multiple employees (new feature)
    employee_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text="Liste des IDs d'employés pour lesquels ce QR est valable"
    )
    
    expires_in_minutes = serializers.IntegerField(default=5, min_value=1, max_value=60)
    
    # Mode: 'auto' (default), 'check_in', 'check_out'
    mode = serializers.ChoiceField(
        choices=['auto', 'check_in', 'check_out'],
        default='auto',
        help_text="Mode de pointage: auto (détection automatique), check_in (arrivée uniquement), check_out (départ uniquement)"
    )

    def validate(self, attrs):
        employee = attrs.get('employee')
        employee_ids = attrs.get('employee_ids', [])
        
        # Ensure at least one employee is specified
        if not employee and not employee_ids:
            raise serializers.ValidationError({
                'employee_ids': "Au moins un employé doit être spécifié"
            })
        
        # Normalize: if single employee, add to list
        if employee and not employee_ids:
            employee_ids = [employee]
        
        # Validate all employees exist and are active
        from hr.models import Employee
        valid_employees = []
        
        for emp_id in employee_ids:
            try:
                emp = Employee.objects.get(
                    id=emp_id, 
                    organization=self.context['organization'],
                    is_active=True
                )
                valid_employees.append(emp)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    'employee_ids': f"Employé {emp_id} introuvable ou inactif"
                })
        
        attrs['validated_employees'] = valid_employees
        return attrs

    def create(self, validated_data):
        import secrets
        from datetime import timedelta
        from django.utils import timezone
        from hr.models import QRCodeSession
        
        employees = validated_data['validated_employees']
        expires_in_minutes = validated_data['expires_in_minutes']
        
        # Generate unique token
        session_token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)
        
        # Create session with first employee as primary (for backward compat)
        session = QRCodeSession.objects.create(
            organization=self.context['organization'],
            employee=employees[0],  # Primary employee
            session_token=session_token,
            expires_at=expires_at,
            mode=validated_data.get('mode', 'auto'),
            created_by=self.context['request'].user if hasattr(self.context['request'].user, 'email') else None,
            is_active=True
        )
        
        # Add all employees to allowed_employees M2M
        session.allowed_employees.set(employees)
        
        # Store for serialization
        session._all_employees = employees
        
        return session


class QRAttendanceCheckInSerializer(serializers.Serializer):
    """
    Serializer for QR code attendance - handles both check-in and check-out.
    Supports:
    - Single employee QR (backward compatible)
    - Multi-employee QR (employee must identify themselves)
    - Mode: auto (detect), check_in (force arrival), check_out (force departure)
    """

    session_token = serializers.CharField()
    employee_id = serializers.UUIDField(
        required=False, 
        allow_null=True,
        help_text="ID de l'employé qui pointe (requis pour QR multi-employés)"
    )
    location = serializers.CharField(required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        from hr.models import QRCodeSession, Employee
        from core.models import AdminUser
        
        session_token = attrs.get('session_token')
        request = self.context.get('request')
        
        # Validate session
        try:
            session = QRCodeSession.objects.select_related('employee', 'organization').prefetch_related('allowed_employees').get(
                session_token=session_token,
                is_active=True
            )

            if session.is_expired():
                session.is_active = False
                session.save()
                raise serializers.ValidationError({
                    'session_token': "Cette session QR a expiré. Demandez un nouveau QR code."
                })
                
            attrs['session'] = session
            
        except QRCodeSession.DoesNotExist:
            raise serializers.ValidationError({
                'session_token': "Session QR invalide ou expirée. Demandez un nouveau QR code."
            })
        
        # Get the logged-in user
        user = request.user if request else None
        
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({
                'session_token': "Vous devez être connecté pour pointer"
            })
        
        # Get user's email to find their employee record
        user_email = getattr(user, 'email', None)
        
        if not user_email:
            raise serializers.ValidationError({
                'session_token': "Impossible d'identifier votre compte"
            })
        
        # Find the employee record for this user
        try:
            employee = Employee.objects.get(
                organization=session.organization,
                email=user_email,
                is_active=True
            )
        except Employee.DoesNotExist:
            raise serializers.ValidationError({
                'session_token': f"Aucun employé trouvé avec l'email {user_email}"
            })
        
        # Get allowed employees from M2M relation
        allowed_employees = list(session.allowed_employees.all())
        
        # Fallback to legacy employee field if no allowed_employees
        if not allowed_employees and session.employee:
            allowed_employees = [session.employee]
        
        # Check if the logged-in employee is in the allowed list
        employee_ids = [str(emp.id) for emp in allowed_employees]
        
        if str(employee.id) not in employee_ids:
            raise serializers.ValidationError({
                'session_token': f"{employee.get_full_name()}, vous n'êtes pas autorisé à pointer avec ce QR code"
            })

        # Use mode from session (not hardcoded)
        attrs['mode'] = session.mode
        attrs['employee'] = employee
        return attrs

    def create(self, validated_data):
        from hr.models import Attendance
        from django.utils import timezone

        session = validated_data['session']
        employee = validated_data['employee']  # This is the Employee object
        mode = validated_data.get('mode', 'auto')
        location = validated_data.get('location', '')
        notes = validated_data.get('notes', '')
        organization = session.organization
        now = timezone.now()
        today = now.date()

        # Check for existing attendance today - use 'user' field
        existing_attendance = Attendance.objects.filter(
            user=employee,  # employee IS the user (Employee inherits from BaseUser)
            organization=organization,
            date=today
        ).first()

        action = None
        message = None

        if existing_attendance:
            if existing_attendance.check_out:
                # Already checked out
                raise serializers.ValidationError({
                    'session_token': f"{employee.get_full_name()}, vous avez déjà pointé votre départ aujourd'hui. À demain !"
                })
            elif existing_attendance.check_in:
                # Already checked in
                if mode == 'check_in':
                    # Mode is check_in only, but already checked in
                    raise serializers.ValidationError({
                        'session_token': f"{employee.get_full_name()}, vous avez déjà pointé votre arrivée aujourd'hui. Ce QR code est uniquement pour l'arrivée."
                    })
                else:
                    # Mode is auto or check_out - do CHECK-OUT
                    existing_attendance.check_out = now
                    existing_attendance.check_out_location = location
                    existing_attendance.check_out_notes = notes
                    existing_attendance.save()
                    action = 'check_out'
                    message = f"Départ enregistré à {now.strftime('%H:%M')}. Bonne soirée {employee.first_name} !"
                    attendance = existing_attendance
            else:
                # Record exists but no check-in (edge case)
                existing_attendance.check_in = now
                existing_attendance.check_in_location = location
                existing_attendance.check_in_notes = notes
                existing_attendance.status = 'present'
                existing_attendance.save()
                action = 'check_in'
                message = f"Arrivée enregistrée à {now.strftime('%H:%M')}. Bonne journée {employee.first_name} !"
                attendance = existing_attendance
        else:
            # No attendance record today
            if mode == 'check_out':
                # Mode is check_out only, but no check-in exists
                raise serializers.ValidationError({
                    'session_token': f"{employee.get_full_name()}, vous devez d'abord pointer votre arrivée. Ce QR code est uniquement pour le départ."
                })
            else:
                # Mode is auto or check_in - do CHECK-IN
                # Use 'user' field instead of 'employee'
                attendance = Attendance.objects.create(
                    user=employee,  # employee IS the user (Employee inherits from BaseUser)
                    organization=organization,
                    user_email=employee.email,
                    user_full_name=employee.get_full_name(),
                    date=today,
                    check_in=now,
                    check_in_location=location,
                    check_in_notes=notes,
                    status='present',
                    approval_status='pending'
                )
                action = 'check_in'
                message = f"Arrivée enregistrée à {now.strftime('%H:%M')}. Bienvenue {employee.first_name} et bonne journée !"

        # Store action and message on the attendance object for response
        attendance._qr_action = action
        attendance._qr_message = message

        # Keep session active for other employees/check-out
        return attendance


# ===============================
# PAYROLL ADVANCE SERIALIZERS
# ===============================

class PayrollAdvanceSerializer(serializers.ModelSerializer):
    """Serializer complet pour les demandes d'avance sur salaire"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_number = serializers.CharField(source='employee.employee_id', read_only=True)
    employee_details = EmployeeListSerializer(source='employee', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    payslip_reference = serializers.CharField(source='payslip.id', read_only=True, allow_null=True)

    class Meta:
        model = PayrollAdvance
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_number', 'employee_details',
            'amount', 'reason', 'request_date', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_date', 'rejection_reason',
            'payment_date', 'payslip', 'payslip_reference', 'deduction_month',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['request_date', 'approved_date', 'created_at', 'updated_at']


class PayrollAdvanceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une demande d'avance"""

    class Meta:
        model = PayrollAdvance
        fields = ['employee', 'amount', 'reason', 'notes']

    def validate_amount(self, value):
        """Valider que le montant est positif et raisonnable"""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être supérieur à 0")

        # Optionnel : vérifier que l'avance ne dépasse pas le salaire mensuel
        employee = self.initial_data.get('employee')
        if employee:
            from hr.models import Employee
            try:
                emp = Employee.objects.get(id=employee)
                # Vous pouvez ajouter une logique pour vérifier le salaire de base
                # if value > emp.base_salary:
                #     raise serializers.ValidationError("L'avance ne peut pas dépasser le salaire mensuel")
            except Employee.DoesNotExist:
                pass

        return value


class PayrollAdvanceApprovalSerializer(serializers.Serializer):
    """Serializer pour approuver ou rejeter une demande d'avance"""

    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    payment_date = serializers.DateField(required=False, allow_null=True)
    deduction_month = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': "Une raison de rejet est requise"
            })

        if data['action'] == 'approve' and not data.get('payment_date'):
            # Par défaut, la date de paiement est aujourd'hui
            from django.utils import timezone
            data['payment_date'] = timezone.now().date()

        return data


class PayrollAdvanceListSerializer(serializers.ModelSerializer):
    """Serializer light pour les listes d'avances"""

    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id_number = serializers.CharField(source='employee.employee_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = PayrollAdvance
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_number',
            'amount', 'reason', 'request_date', 'status', 'status_display','rejection_reason',
            'approved_by_name', 'approved_date', 'payment_date', 'payslip', 'created_at'
        ]
