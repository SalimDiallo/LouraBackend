"""
HR API Permissions
==================
Classes de permission DRF pour le module HR.
Admin = toutes les permissions, Employee = vérification via rôle.
"""

from rest_framework import permissions


class IsAuthenticated(permissions.BasePermission):
    """Vérifie que l'utilisateur est authentifié."""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUserOrEmployee(permissions.BasePermission):
    """Autorise Admin et Employee authentifiés."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsAdminUser(permissions.BasePermission):
    """Autorise uniquement les AdminUser."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'admin'


class HasPermission(permissions.BasePermission):
    """
    Vérifie une permission spécifique.
    Admin = TOUJOURS autorisé (bypass)
    Employee = vérifie via assigned_role + custom_permissions
    
    Usage dans une vue:
        permission_classes = [HasPermission]
        required_permission = 'hr.view_employees'
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)
        permission_code = getattr(view, 'required_permission', None)

        # Pas de permission requise = autorisé
        if not permission_code:
            return True

        # Admin = toutes les permissions
        if user_type == 'admin':
            return True

        # Employee = vérifier via has_permission()
        if user_type == 'employee':
            return user.has_permission(permission_code)

        return False


class HasCRUDPermission(permissions.BasePermission):
    """
    Permission automatique basée sur l'action CRUD.
    Utilise permission_prefix et permission_resource de la vue.
    
    Usage:
        class EmployeeViewSet(viewsets.ModelViewSet):
            permission_classes = [HasCRUDPermission]
            permission_prefix = 'hr'
            permission_resource = 'employees'
    
    Génère:
        - list/retrieve: hr.view_employees
        - create: hr.create_employees
        - update/partial_update: hr.update_employees
        - destroy: hr.delete_employees
    """
    
    ACTION_MAPPING = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'create',
        'update': 'update',
        'partial_update': 'update',
        'destroy': 'delete',
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)

        # Admin = toutes les permissions
        if user_type == 'admin':
            return True

        # Déterminer la permission requise
        action = getattr(view, 'action', None)
        prefix = getattr(view, 'permission_prefix', 'hr')
        resource = getattr(view, 'permission_resource', 'resource')

        if action in self.ACTION_MAPPING:
            permission_code = f"{prefix}.{self.ACTION_MAPPING[action]}_{resource}"
            return user.has_permission(permission_code)

        # Actions personnalisées
        return True


# ===============================
# PERMISSIONS SPÉCIFIQUES HR
# ===============================

class RequiresEmployeePermission(HasCRUDPermission):
    """Permission pour les opérations sur les employés."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'employees'
        return super().has_permission(request, view)


class RequiresDepartmentPermission(HasCRUDPermission):
    """Permission pour les opérations sur les départements."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'departments'
        return super().has_permission(request, view)


class RequiresPositionPermission(HasCRUDPermission):
    """Permission pour les opérations sur les postes."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'positions'
        return super().has_permission(request, view)


class RequiresContractPermission(HasCRUDPermission):
    """Permission pour les opérations sur les contrats."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'contracts'
        return super().has_permission(request, view)


class RequiresLeavePermission(HasCRUDPermission):
    """Permission pour les opérations sur les congés."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'leave_requests'
        return super().has_permission(request, view)


class RequiresPayrollPermission(HasCRUDPermission):
    """Permission pour les opérations sur la paie."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'payroll'
        return super().has_permission(request, view)


class RequiresAttendancePermission(HasCRUDPermission):
    """Permission pour les opérations sur les pointages."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'attendance'
        return super().has_permission(request, view)


class RequiresRolePermission(HasCRUDPermission):
    """Permission pour les opérations sur les rôles."""
    
    def has_permission(self, request, view):
        view.permission_prefix = 'hr'
        view.permission_resource = 'roles'
        return super().has_permission(request, view)


# ===============================
# LEGACY ALIASES
# ===============================

class IsHRAdmin(IsAdminUser):
    """Alias pour rétrocompatibilité."""
    pass


class IsHRAdminOrReadOnly(permissions.BasePermission):
    """Read-only pour tous, write pour Admin."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, 'user_type', None) == 'admin'


class IsManagerOrHRAdmin(permissions.BasePermission):
    """Admin ou manager de l'employé."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_type = getattr(request.user, 'user_type', None)
        if user_type == 'admin':
            return True
        
        # TODO: Vérifier si l'utilisateur est manager
        return True


class RequiresPermission(HasPermission):
    """Alias pour rétrocompatibilité."""
    required_permission = None
    
    def has_permission(self, request, view):
        if self.required_permission:
            view.required_permission = self.required_permission
        return super().has_permission(request, view)


class RequiresCRUDPermission(HasCRUDPermission):
    """Alias pour rétrocompatibilité."""
    pass


class CanAccessOwnOrManage(permissions.BasePermission):
    """Placeholder pour accès aux propres données."""
    
    @staticmethod
    def for_resource(resource, permission):
        return CanAccessOwnOrManage


class IsDepartmentHeadOrHR(permissions.BasePermission):
    """Placeholder pour chef de département."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsManagerOfEmployee(permissions.BasePermission):
    """Placeholder pour manager d'un employé."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
