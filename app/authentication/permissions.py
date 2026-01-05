"""
Authentication Permissions
==========================
Classes de permission pour l'authentification.
Utilise user_type au lieu de isinstance() pour le polymorphisme BaseUser.
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Vérifie que l'utilisateur est un Admin."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'user_type', None) == 'admin'


class IsEmployee(BasePermission):
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
        user_type = getattr(request.user, 'user_type', None)
        return user_type in ('admin', 'employee')


class IsActiveUser(BasePermission):
    """Vérifie que l'utilisateur est actif."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_active', True)


class HasValidOrganization(BasePermission):
    """Vérifie que l'Employee a une organisation valide et active."""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_type = getattr(request.user, 'user_type', None)
        
        # Admin: toujours OK
        if user_type == 'admin':
            return True
        
        # Employee: vérifier l'organisation
        if user_type == 'employee':
            user = request.user.get_concrete_user() if hasattr(request.user, 'get_concrete_user') else request.user
            org = getattr(user, 'organization', None)
            return org is not None and getattr(org, 'is_active', False)

        return False
