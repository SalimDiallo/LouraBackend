from rest_framework import permissions
from core.models import AdminUser

def user_has_permission(user, perm_code):
    """
    Vérifie si un utilisateur (Employee ou AdminUser) possède un code de permission donné.
    - AdminUser : toujours True (super admin, cf. views.py).
    - Employee : vérifie d'abord custom_permissions, puis les permissions du rôle assigné.
    """
    if isinstance(user, AdminUser):
        return True

    # Lazy import pour éviter les issues de circular import
    from hr.models import Employee
    if not isinstance(user, Employee):
        return False

    # custom_permissions (ManyToMany)
    if hasattr(user, "custom_permissions") and user.custom_permissions.filter(code=perm_code).exists():
        return True

    # Par rôle
    if hasattr(user, "assigned_role") and user.assigned_role:
        return user.assigned_role.permissions.filter(code=perm_code).exists()
    return False

class RequiresPermission(permissions.BasePermission):
    """
    Permission générique basée sur un code "hr.permissions".
    Voir usages dans views.py.
    Utilisation :
        permission_classes = [RequiresPermission.with_permission("can_approve_leave")]
    """
    required_permission = None

    @classmethod
    def with_permission(cls, permission_code):
        class _WithPerm(cls):
            required_permission = permission_code
        _WithPerm.__name__ = f"Requires_{permission_code}"
        return _WithPerm

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if self.required_permission is None:
            return False
        return user_has_permission(request.user, self.required_permission)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsEmployeeOfOrganization(permissions.BasePermission):
    """
    Permission : vérifie que l'employé appartient bien à l'organisation de l'objet.
    (cf. filtrages dans les viewsets Employee, LeaveType...)
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        return bool(request.user and request.user.is_authenticated and isinstance(request.user, Employee))

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee
        if not isinstance(request.user, Employee):
            return False
        if hasattr(obj, "organization"):
            return obj.organization == request.user.organization
        if hasattr(obj, "employee"):
            return obj.employee.organization == request.user.organization
        return False

class IsHRAdminOrReadOnly(permissions.BasePermission):
    """
    Écriture : requiert la permission 'can_manage_employee_permissions' (HR ADMIN au sens views.py).
    Lecture : tout AdminUser/Employee authentifié autorisé.
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if not isinstance(u, (AdminUser, Employee)):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return user_has_permission(u, "can_manage_employee_permissions")

class IsHRAdmin(permissions.BasePermission):
    """
    Autorisé : 'can_manage_employee_permissions' (HR Admin flag cf. views.py) ou AdminUser.
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        return (
            request.user
            and request.user.is_authenticated
            and user_has_permission(request.user, "can_manage_employee_permissions")
        )

class IsManagerOrHRAdmin(permissions.BasePermission):
    """
    Autorisé :
     - AdminUser
     - HR Admin (cf. can_manage_employee_permissions)
     - Employee ayant role.code == "manager"
     - Employee ayant des subordonnés
    Cf. viewsets LeaveRequestViewSet (approbation/droits)
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if isinstance(u, AdminUser):
            return True
        if isinstance(u, Employee):
            if user_has_permission(u, "can_manage_employee_permissions"):
                return True
            if getattr(u, "assigned_role", None) and u.assigned_role.code == "manager":
                return True
            # manager via subordinates attribute (voir views.py)
            if hasattr(u, "subordinates") and u.subordinates.exists():
                return True
        return False

class IsOwnerOrHRAdmin(permissions.BasePermission):
    """
    Autorisé :
     - Propriétaire de l'objet (Employee == obj ou obj.employee)
     - HR Admin (can_manage_employee_permissions)
     - AdminUser d'une organisation liée à l'objet
    Utilisé pour les endpoints sensibles (modification profil, etc.)
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        u = request.user
        return bool(u and u.is_authenticated and isinstance(u, (AdminUser, Employee)))

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee
        user = request.user
        # AdminUser, accès total pour sa/leurs orgs
        if isinstance(user, AdminUser):
            if hasattr(obj, "organization"):
                return obj.organization.admin == user
            elif hasattr(obj, "employee"):
                return obj.employee.organization.admin == user
            return True
        if not isinstance(user, Employee):
            return False
        # Propriétaire ?
        if hasattr(obj, "employee"):
            if obj.employee == user:
                return True
        if obj == user:
            return True
        # Droit HR admin
        return user_has_permission(user, "can_manage_employee_permissions")

class IsAdminUserOrEmployee(permissions.BasePermission):
    """
    Seuls AdminUser et Employee authentifiés autorisés.
    
    NOTE: Cette classe est un alias de authentication.permissions.IsAdminOrEmployee
    pour maintenir la rétrocompatibilité. Dans le futur, privilégier l'import direct
    depuis authentication.permissions.
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        u = request.user
        return bool(u and u.is_authenticated and isinstance(u, (AdminUser, Employee)))

# ===============================
# CRUD PERMISSION CLASSES
# ===============================

class RequiresCRUDPermission(permissions.BasePermission):
    """
    Permission CRUD dynamique basée sur l'action et la ressource.
    Vérifie automatiquement can_view_{resource}, can_create_{resource}, etc.
    selon l'action du viewset.
    
    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAdminUserOrEmployee, RequiresCRUDPermission.for_resource('employee')]
    """
    resource = None

    ACTION_MAP = {
        'list': 'can_view_{resource}',
        'retrieve': 'can_view_{resource}',
        'create': 'can_create_{resource}',
        'update': 'can_update_{resource}',
        'partial_update': 'can_update_{resource}',
        'destroy': 'can_delete_{resource}',
    }

    @classmethod
    def for_resource(cls, resource_name):
        """Factory method pour créer une classe de permission pour une ressource spécifique"""
        class ResourcePermission(cls):
            resource = resource_name
        ResourcePermission.__name__ = f"Requires{resource_name.title().replace('_', '')}Permission"
        return ResourcePermission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # AdminUser a toujours accès
        if isinstance(request.user, AdminUser):
            return True

        action = getattr(view, 'action', None)
        if not action or not self.resource:
            return False

        # Vérifier si l'action a une permission mappée
        perm_template = self.ACTION_MAP.get(action)
        if not perm_template:
            # Actions personnalisées - vérifier si elles sont définies dans la vue
            return True  # Déléguer aux permissions spécifiques de l'action

        perm_code = perm_template.format(resource=self.resource)
        return user_has_permission(request.user, perm_code)

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanAccessOwnOrManage(permissions.BasePermission):
    """
    Autorise l'accès à ses propres ressources OU si l'utilisateur peut gérer cette ressource.
    Utile pour les endpoints où un employé peut voir ses propres données 
    mais un HR admin peut voir toutes les données.
    
    Usage:
        - LeaveBalance (employé voit son solde, HR voit tous les soldes)
        - LeaveRequest (employé voit ses demandes, manager/HR voit celles de son équipe)
        - Payslip (employé voit ses fiches, HR voit toutes les fiches)
    """
    resource = None
    manage_permission = None

    @classmethod
    def for_resource(cls, resource_name, perm_code=None):
        _resource = resource_name
        _perm = perm_code or f"can_view_{resource_name}"
        
        class ResourceAccess(cls):
            resource = _resource
            manage_permission = _perm
        ResourceAccess.__name__ = f"CanAccessOwnOr{resource_name.title().replace('_', '')}Manager"
        return ResourceAccess

    def has_permission(self, request, view):
        from hr.models import Employee
        if not request.user or not request.user.is_authenticated:
            return False

        if isinstance(request.user, AdminUser):
            return True

        if isinstance(request.user, Employee):
            # Si l'employé a la permission de gestion, autoriser
            if self.manage_permission and user_has_permission(request.user, self.manage_permission):
                return True
            # Sinon, l'employé peut toujours accéder à ses propres ressources (filtré dans get_queryset)
            return True

        return False

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee
        if isinstance(request.user, AdminUser):
            return True

        if not isinstance(request.user, Employee):
            return False

        # Vérifier si l'utilisateur peut gérer cette ressource
        if self.manage_permission and user_has_permission(request.user, self.manage_permission):
            return True

        # Vérifier si c'est sa propre ressource
        if hasattr(obj, 'employee') and obj.employee == request.user:
            return True
        if obj == request.user:
            return True

        return False


class IsDepartmentHeadOrHR(permissions.BasePermission):
    """
    Autorise si l'utilisateur est chef de département pour l'objet concerné,
    ou s'il a les permissions HR.
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        if not request.user or not request.user.is_authenticated:
            return False
        return isinstance(request.user, (AdminUser, Employee))

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee
        if isinstance(request.user, AdminUser):
            return True

        if not isinstance(request.user, Employee):
            return False

        # HR Admin a accès
        if user_has_permission(request.user, "can_manage_employee_permissions"):
            return True

        # Vérifier si l'utilisateur est chef du département de l'objet
        if hasattr(obj, 'department') and obj.department:
            if obj.department.head == request.user:
                return True

        # Vérifier si c'est un employé et que l'utilisateur est chef de son département
        if hasattr(obj, 'employee') and obj.employee and obj.employee.department:
            if obj.employee.department.head == request.user:
                return True

        return False


class IsManagerOfEmployee(permissions.BasePermission):
    """
    Autorise si l'utilisateur est le manager direct de l'employé concerné.
    """
    def has_permission(self, request, view):
        from hr.models import Employee
        if not request.user or not request.user.is_authenticated:
            return False
        return isinstance(request.user, (AdminUser, Employee))

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee
        if isinstance(request.user, AdminUser):
            return True

        if not isinstance(request.user, Employee):
            return False

        # Récupérer l'employé concerné
        target_employee = None
        if isinstance(obj, Employee):
            target_employee = obj
        elif hasattr(obj, 'employee'):
            target_employee = obj.employee

        if target_employee:
            # Vérifier si l'utilisateur est le manager direct
            if target_employee.manager == request.user:
                return True
            # Vérifier si l'utilisateur a des subordonnés incluant cet employé
            if request.user.subordinates.filter(id=target_employee.id).exists():
                return True

        return False


# ===============================
# RESOURCE-SPECIFIC PERMISSIONS
# ===============================

# Employee permissions
RequiresEmployeePermission = RequiresCRUDPermission.for_resource('employee')

# Department permissions
RequiresDepartmentPermission = RequiresCRUDPermission.for_resource('department')

# Position permissions
RequiresPositionPermission = RequiresCRUDPermission.for_resource('position')

# Contract permissions
RequiresContractPermission = RequiresCRUDPermission.for_resource('contract')

# Leave permissions
RequiresLeavePermission = RequiresCRUDPermission.for_resource('leave')

# Payroll permissions
RequiresPayrollPermission = RequiresCRUDPermission.for_resource('payroll')

# Attendance permissions
RequiresAttendancePermission = RequiresCRUDPermission.for_resource('attendance')

# Role permissions
RequiresRolePermission = RequiresCRUDPermission.for_resource('role')

# Reports permissions
RequiresReportPermission = RequiresPermission.with_permission('can_view_reports')


# ===============================
# LEGACY ALIASES (for backward compatibility)
# ===============================
RequiresCanViewEmployee        = RequiresPermission.with_permission("can_view_employee")
RequiresCanManageEmployeePerms = RequiresPermission.with_permission("can_manage_employee_permissions")
RequiresCanApproveLeave        = RequiresPermission.with_permission("can_approve_leave")
RequiresCanViewPayroll         = RequiresPermission.with_permission("can_view_payroll")
