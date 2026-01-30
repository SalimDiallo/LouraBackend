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


class TokenFromQueryParamMiddleware(MiddlewareMixin):
    """
    Middleware pour permettre l'authentification via token dans les query params.
    Utilisé principalement pour les téléchargements de fichiers (PDF) où l'on ne peut
    pas utiliser les headers Authorization dans les liens <a>.
    
    Usage: ?token=<jwt_access_token>
    """
    
    def process_request(self, request):
        # Vérifie si un token est présent dans les query params
        token = request.GET.get('token')
        
        if token and 'HTTP_AUTHORIZATION' not in request.META:
            # Ajoute le token comme header Authorization
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        
        return None
