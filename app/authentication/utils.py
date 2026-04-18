"""
Utilitaires pour l'authentification
======================================
Ce module contient les fonctions utilitaires pour :
- Gestion des cookies JWT (set/clear)
- Conversion des UUID en strings

Note: La logique de génération/validation des tokens a été
déplacée vers TokenService dans services.py (SRP)
"""
import logging
from uuid import UUID
from django.conf import settings

logger = logging.getLogger(__name__)


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
# UUID CONVERSION
# ================================="


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


# Note: get_user_from_token a été déplacé vers TokenService.get_user_from_refresh_token()
# pour respecter le principe Single Responsibility

