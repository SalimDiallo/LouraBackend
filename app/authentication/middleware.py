"""
Authentication Middleware
=========================
Middleware pour enrichir la requête avec des informations utilisateur.
"""

from django.utils.deprecation import MiddlewareMixin


class UserTypeMiddleware(MiddlewareMixin):
    """
    Middleware pour ajouter le type d'utilisateur à la requête.
    Utilise user_type de BaseUser au lieu de isinstance().
    """
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Utilise le champ user_type de BaseUser
            request.user_type = getattr(request.user, 'user_type', 'unknown')
        else:
            request.user_type = None
        return None
