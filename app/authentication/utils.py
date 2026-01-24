"""
Utilitaires pour l'authentification

Ce module centralise toutes les fonctions utilitaires liées à l'authentification :
- Génération de tokens JWT
- Gestion des cookies JWT (set/clear)
- Conversion des UUID en strings
- Validation des tokens
"""
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import timedelta
from uuid import UUID
from django.conf import settings


# =================================
# JWT COOKIE HELPERS
# =================================

def set_jwt_cookies(response, access_token, refresh_token):
    """
    Set JWT tokens in HTTP-only cookies.
    
    Args:
        response: Django/DRF Response object
        access_token: JWT access token string
        refresh_token: JWT refresh token string
    
    Returns:
        None (modifies response in place)
    """
    # Access token cookie
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )

    # Refresh token cookie
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )


def clear_jwt_cookies(response):
    """
    Clear JWT cookies from the response.
    
    Args:
        response: Django/DRF Response object
    
    Returns:
        None (modifies response in place)
    """
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )


# =================================
# TOKEN GENERATION
# =================================


def generate_tokens_for_user(user, user_type='admin'):
    """
    Générer des tokens JWT pour un utilisateur (Admin ou Employee)

    Args:
        user: Instance de AdminUser ou Employee
        user_type: 'admin' ou 'employee'

    Returns:
        dict: {'access': str, 'refresh': str}
    """
    if user_type == 'admin':
        # Pour les admins, utiliser RefreshToken standard
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
    else:
        # Pour les employés, créer des tokens manuels
        access_token_obj = AccessToken()
        access_token_obj['user_id'] = str(user.id)
        access_token_obj['email'] = user.email
        access_token_obj['user_type'] = 'employee'
        access_token_obj.set_exp(lifetime=timedelta(minutes=15))
        access_token = str(access_token_obj)

        refresh_token_obj = AccessToken()
        refresh_token_obj['user_id'] = str(user.id)
        refresh_token_obj['email'] = user.email
        refresh_token_obj['user_type'] = 'employee'
        refresh_token_obj['token_type'] = 'refresh'
        refresh_token_obj.set_exp(lifetime=timedelta(days=7))
        refresh_token = str(refresh_token_obj)

    return {
        'access': access_token,
        'refresh': refresh_token
    }


def convert_uuids_to_strings(data):
    """
    Convertir récursivement les UUID en strings dans un dict ou une liste

    Args:
        data: dict, list, ou autre type

    Returns:
        data avec les UUID convertis en strings
    """
    if isinstance(data, dict):
        return {key: convert_uuids_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_uuids_to_strings(item) for item in data]
    elif isinstance(data, UUID):
        return str(data)
    else:
        return data


def get_user_from_token(token_string):
    """
    Extraire les informations utilisateur d'un token JWT

    Args:
        token_string: Le token JWT sous forme de string

    Returns:
        dict: {'user_id': str, 'email': str, 'user_type': str}

    Raises:
        TokenError: Si le token est invalide
    """
    import jwt
    from rest_framework_simplejwt.exceptions import TokenError

    try:
        decoded = jwt.decode(
            token_string,
            settings.SIMPLE_JWT['SIGNING_KEY'],
            algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
        )

        return {
            'user_id': decoded.get('user_id'),
            'email': decoded.get('email'),
            'user_type': decoded.get('user_type', 'admin')
        }
    except jwt.ExpiredSignatureError:
        raise TokenError('Token expired')
    except jwt.InvalidTokenError:
        raise TokenError('Invalid token')

