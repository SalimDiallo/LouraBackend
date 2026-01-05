"""
Core Permissions
================
Classes de permission DRF pour l'authentification et l'autorisation.
Admin = toutes les permissions
Employee = vérification des permissions via rôle
"""

from rest_framework.permissions import BasePermission
from core.models import AdminUser, BaseUser
from hr.models import Employee


class IsAuthenticated(BasePermission):
    """Vérifie que l'utilisateur est authentifié"""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUser(BasePermission):
    """Vérifie que l'utilisateur est un AdminUser"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'admin'


class IsEmployeeUser(BasePermission):
    """Vérifie que l'utilisateur est un Employee"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'employee'


class HasPermission(BasePermission):
    """
    Vérifie qu'un utilisateur a une permission spécifique.
    
    - AdminUser: TOUJOURS autorisé (toutes les permissions)
    - Employee: Vérifie via assigned_role + custom_permissions
    
    Usage dans une vue:
        permission_classes = [HasPermission]
        required_permission = 'hr.view_employees'
    
    Ou dynamiquement:
        def get_permissions(self):
            if self.action == 'create':
                return [HasPermission('hr.create_employees')]
            return [HasPermission('hr.view_employees')]
    """
    
    def __init__(self, permission_code=None):
        self.permission_code = permission_code

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        
        # Déterminer le code de permission
        permission_code = self.permission_code or getattr(view, 'required_permission', None)

        # Si pas de permission requise, autoriser
        if not permission_code:
            return True

        # AdminUser = toutes les permissions
        if getattr(user, 'user_type', None) == 'admin':
            return True

        # Employee = vérifier les permissions
        if getattr(user, 'user_type', None) == 'employee':
            return user.has_permission(permission_code)

        return False


class HasAnyPermission(BasePermission):
    """
    Vérifie qu'un utilisateur a AU MOINS UNE des permissions spécifiées.
    
    Usage:
        permission_classes = [HasAnyPermission]
        required_permissions = ['hr.view_employees', 'hr.view_departments']
    """
    
    def __init__(self, permission_codes=None):
        self.permission_codes = permission_codes or []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        permission_codes = self.permission_codes or getattr(view, 'required_permissions', [])

        if not permission_codes:
            return True

        # AdminUser = toutes les permissions
        if getattr(user, 'user_type', None) == 'admin':
            return True

        # Employee = vérifier au moins une permission
        if getattr(user, 'user_type', None) == 'employee':
            for code in permission_codes:
                if user.has_permission(code):
                    return True
            return False

        return False


class HasAllPermissions(BasePermission):
    """
    Vérifie qu'un utilisateur a TOUTES les permissions spécifiées.
    
    Usage:
        permission_classes = [HasAllPermissions]
        required_permissions = ['hr.view_employees', 'hr.create_employees']
    """
    
    def __init__(self, permission_codes=None):
        self.permission_codes = permission_codes or []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        permission_codes = self.permission_codes or getattr(view, 'required_permissions', [])

        if not permission_codes:
            return True

        # AdminUser = toutes les permissions
        if getattr(user, 'user_type', None) == 'admin':
            return True

        # Employee = vérifier toutes les permissions
        if getattr(user, 'user_type', None) == 'employee':
            for code in permission_codes:
                if not user.has_permission(code):
                    return False
            return True

        return False


class IsOrganizationMember(BasePermission):
    """
    Vérifie que l'utilisateur appartient à l'organisation demandée.
    
    - AdminUser: doit être admin de l'organisation
    - Employee: doit appartenir à l'organisation
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        
        # Récupérer l'ID ou subdomain de l'organisation depuis la requête
        org_id = request.query_params.get('organization') or request.data.get('organization')
        org_subdomain = request.query_params.get('organization_subdomain') or \
                       request.headers.get('X-Organization-Subdomain')

        if not org_id and not org_subdomain:
            return True  # Pas de filtre organisation requis

        # AdminUser
        if getattr(user, 'user_type', None) == 'admin':
            if org_id:
                return user.organizations.filter(id=org_id).exists()
            if org_subdomain:
                return user.organizations.filter(subdomain=org_subdomain).exists()
            return True

        # Employee
        if getattr(user, 'user_type', None) == 'employee':
            if org_id:
                return str(user.organization_id) == str(org_id)
            if org_subdomain:
                return user.organization.subdomain == org_subdomain
            return True

        return False


class CanManageResource(BasePermission):
    """
    Permission générique pour gérer les ressources CRUD.
    Configure automatiquement les permissions selon l'action.
    
    Usage dans un ViewSet:
        permission_classes = [CanManageResource]
        permission_prefix = 'hr'  # Préfixe des permissions
        permission_resource = 'employees'  # Nom de la ressource
    
    Génère automatiquement:
        - list/retrieve: {prefix}.view_{resource}
        - create: {prefix}.create_{resource}
        - update/partial_update: {prefix}.update_{resource}
        - destroy: {prefix}.delete_{resource}
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

        # AdminUser = toutes les permissions
        if getattr(user, 'user_type', None) == 'admin':
            return True

        # Déterminer la permission requise
        action = getattr(view, 'action', None)
        prefix = getattr(view, 'permission_prefix', 'core')
        resource = getattr(view, 'permission_resource', 'resource')

        if action in self.ACTION_MAPPING:
            permission_code = f"{prefix}.{self.ACTION_MAPPING[action]}_{resource}"
            return user.has_permission(permission_code)

        # Actions personnalisées: vérifier required_permission sur l'action
        action_func = getattr(view, action, None) if action else None
        if action_func and hasattr(action_func, 'required_permission'):
            return user.has_permission(action_func.required_permission)

        return True


def require_permission(permission_code):
    """
    Décorateur pour les actions personnalisées de ViewSet.
    
    Usage:
        @action(detail=True, methods=['post'])
        @require_permission('hr.approve_leave_requests')
        def approve(self, request, pk=None):
            ...
    """
    def decorator(func):
        func.required_permission = permission_code
        return func
    return decorator
