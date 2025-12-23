"""
Permissions personnalisées pour l'authentification
"""
from rest_framework.permissions import BasePermission
from hr.models import Employee
from core.models import AdminUser


class IsAdminUser(BasePermission):
    """
    Permission pour vérifier que l'utilisateur est un admin
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and isinstance(request.user, AdminUser)


class IsEmployee(BasePermission):
    """
    Permission pour vérifier que l'utilisateur est un employé
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and isinstance(request.user, Employee)


class IsAdminOrEmployee(BasePermission):
    """
    Permission pour vérifier que l'utilisateur est soit un admin soit un employé
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            isinstance(request.user, AdminUser) or isinstance(request.user, Employee)
        )


class IsActiveUser(BasePermission):
    """
    Permission pour vérifier que l'utilisateur est actif
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has is_active attribute
        if hasattr(request.user, 'is_active'):
            return request.user.is_active

        return True


class HasValidOrganization(BasePermission):
    """
    Permission pour vérifier que l'employé a une organisation valide et active
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Only check for employees
        if isinstance(request.user, Employee):
            return (
                hasattr(request.user, 'organization') and
                request.user.organization is not None and
                request.user.organization.is_active
            )

        # Admins always pass this check
        return True
