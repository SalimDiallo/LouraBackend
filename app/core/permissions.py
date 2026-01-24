"""
Core Permissions - Classes de base pour le système de permissions
=================================================================

Ce module définit les classes de permission DRF de base.
Les apps peuvent hériter de ces classes pour créer leurs propres permissions.

Principe Open/Closed :
- Fermé à la modification : Ces classes de base ne doivent pas être modifiées
- Ouvert à l'extension : Les apps héritent et étendent ces classes

Usage dans une app :
    from core.permissions import BaseHasPermission, BaseCRUDPermission
    
    class MyAppPermission(BaseCRUDPermission):
        permission_prefix = 'myapp'
        permission_resource = 'myresource'
"""

from rest_framework.permissions import BasePermission


# ===============================
# CLASSES DE BASE (Abstraites)
# ===============================

class IsAuthenticated(BasePermission):
    """Vérifie que l'utilisateur est authentifié."""
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminUser(BasePermission):
    """Vérifie que l'utilisateur est un AdminUser."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'admin'


class IsEmployeeUser(BasePermission):
    """Vérifie que l'utilisateur est un Employee."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'employee'


class IsAdminOrEmployee(BasePermission):
    """Vérifie que l'utilisateur est authentifié (Admin ou Employee)."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) in ('admin', 'employee')


# ===============================
# PERMISSIONS AVEC VÉRIFICATION DE CODE
# ===============================

class BaseHasPermission(BasePermission):
    """
    Classe de base pour vérifier une permission spécifique.
    
    - AdminUser : TOUJOURS autorisé (bypass)
    - Employee : Vérifie via assigned_role + custom_permissions
    
    Usage :
        class MyPermission(BaseHasPermission):
            required_permission = 'myapp.do_something'
    
    Ou dynamiquement via l'attribut `required_permission` de la vue.
    """
    
    required_permission = None
    
    def get_required_permission(self, view):
        """Retourne le code de permission requis."""
        return self.required_permission or getattr(view, 'required_permission', None)
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)
        permission_code = self.get_required_permission(view)

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


class BaseHasAnyPermission(BasePermission):
    """
    Vérifie qu'un utilisateur a AU MOINS UNE des permissions spécifiées.
    
    Usage :
        class MyPermission(BaseHasAnyPermission):
            required_permissions = ['myapp.perm1', 'myapp.perm2']
    """
    
    required_permissions = []
    
    def get_required_permissions(self, view):
        """Retourne la liste des codes de permission."""
        return self.required_permissions or getattr(view, 'required_permissions', [])
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)
        permission_codes = self.get_required_permissions(view)

        if not permission_codes:
            return True

        if user_type == 'admin':
            return True

        if user_type == 'employee':
            for code in permission_codes:
                if user.has_permission(code):
                    return True
            return False

        return False


# ===============================
# PERMISSION CRUD AUTOMATIQUE
# ===============================

class BaseCRUDPermission(BasePermission):
    """
    Classe de base pour permissions CRUD automatiques.
    
    Configure automatiquement les permissions selon l'action :
        - list/retrieve: {prefix}.view_{resource}
        - create: {prefix}.create_{resource}
        - update/partial_update: {prefix}.update_{resource}
        - destroy: {prefix}.delete_{resource}
    
    Usage :
        class MyResourcePermission(BaseCRUDPermission):
            permission_prefix = 'myapp'
            permission_resource = 'myresources'
    
    Ou via les attributs de la vue :
        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [BaseCRUDPermission]
            permission_prefix = 'myapp'
            permission_resource = 'myresources'
    """
    
    permission_prefix = None
    permission_resource = None
    
    ACTION_MAPPING = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'create',
        'update': 'update',
        'partial_update': 'update',
        'destroy': 'delete',
    }
    
    def get_permission_prefix(self, view):
        """Retourne le préfixe de permission."""
        return self.permission_prefix or getattr(view, 'permission_prefix', 'core')
    
    def get_permission_resource(self, view):
        """Retourne le nom de la ressource."""
        return self.permission_resource or getattr(view, 'permission_resource', 'resource')
    
    def get_permission_code(self, view, action):
        """Génère le code de permission pour une action."""
        prefix = self.get_permission_prefix(view)
        resource = self.get_permission_resource(view)
        action_verb = self.ACTION_MAPPING.get(action, 'view')
        return f"{prefix}.{action_verb}_{resource}"
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)

        # Admin = toutes les permissions
        if user_type == 'admin':
            return True

        action = getattr(view, 'action', None)
        
        # Si allow_list_without_permission et action list, permettre
        allow_list = getattr(view, 'allow_list_without_permission', False)
        if allow_list and action == 'list':
            return True

        # Générer et vérifier la permission
        if action in self.ACTION_MAPPING:
            permission_code = self.get_permission_code(view, action)
            return user.has_permission(permission_code)

        # Actions personnalisées : vérifier required_permission sur l'action
        action_func = getattr(view, action, None) if action else None
        if action_func and hasattr(action_func, 'required_permission'):
            return user.has_permission(action_func.required_permission)

        return True


# ===============================
# PERMISSION ORGANISATION
# ===============================

class IsOrganizationMember(BasePermission):
    """
    Vérifie que l'utilisateur appartient à l'organisation demandée.
    
    - AdminUser : doit être admin de l'organisation
    - Employee : doit appartenir à l'organisation
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        user_type = getattr(user, 'user_type', None)
        
        # Récupérer l'ID ou subdomain de l'organisation depuis la requête
        org_id = request.query_params.get('organization') or request.data.get('organization')
        org_subdomain = (
            request.query_params.get('organization_subdomain') or 
            request.headers.get('X-Organization-Subdomain')
        )

        if not org_id and not org_subdomain:
            return True  # Pas de filtre organisation requis

        if user_type == 'admin':
            if org_id:
                return user.organizations.filter(id=org_id).exists()
            if org_subdomain:
                return user.organizations.filter(subdomain=org_subdomain).exists()
            return True

        if user_type == 'employee':
            if org_id:
                return str(user.organization_id) == str(org_id)
            if org_subdomain:
                return user.organization.subdomain == org_subdomain
            return True

        return False


# ===============================
# DÉCORATEUR POUR ACTIONS CUSTOM
# ===============================

def require_permission(permission_code):
    """
    Décorateur pour les actions personnalisées de ViewSet.
    
    Usage :
        @action(detail=True, methods=['post'])
        @require_permission('myapp.approve_something')
        def approve(self, request, pk=None):
            ...
    """
    def decorator(func):
        func.required_permission = permission_code
        return func
    return decorator


# ===============================
# PERMISSIONS CORE (pour le registry)
# ===============================
# Core ne définit pas de permissions métier
# Il fournit les classes de base pour les autres apps

PERMISSIONS = []  # Core n'a pas de permissions propres


# ===============================
# EXPORTS PUBLICS
# ===============================

__all__ = [
    # Liste des permissions Core (vide)
    'PERMISSIONS',
    # Classes de base
    'IsAuthenticated',
    'IsAdminUser',
    'IsEmployeeUser',
    'IsAdminOrEmployee',
    # Permissions avec code
    'BaseHasPermission',
    'BaseHasAnyPermission',
    # CRUD automatique
    'BaseCRUDPermission',
    # Organisation
    'IsOrganizationMember',
    # Décorateur
    'require_permission',
]

