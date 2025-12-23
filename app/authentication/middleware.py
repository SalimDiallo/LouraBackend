"""
Middleware pour l'authentification
"""
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request
from hr.models import Employee
from core.models import AdminUser


class UserTypeMiddleware(MiddlewareMixin):
    """
    Middleware pour ajouter le type d'utilisateur à la requête
    """
    def process_request(self, request):
        # Ajouter le type d'utilisateur si authentifié
        if hasattr(request, 'user') and request.user.is_authenticated:
            if isinstance(request.user, Employee):
                request.user_type = 'employee'
            elif isinstance(request.user, AdminUser):
                request.user_type = 'admin'
            else:
                request.user_type = 'unknown'
        else:
            request.user_type = None

        return None
