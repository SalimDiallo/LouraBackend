"""
Authentication Permissions
==========================

Ce module gère les permissions liées à l'authentification.
Il ré-exporte les classes de base depuis core.permissions.

Note : L'authentification n'a pas de permissions métier propres
car elle gère l'accès au système lui-même.
"""

# Ré-export des classes de base depuis core
from core.permissions import (
    # Classes d'authentification
    IsAuthenticated,
    IsAdminUser,
    IsEmployeeUser,
    IsAdminOrEmployee,
    # Classes de permission
    BaseHasPermission,
    BaseHasAnyPermission,
    BaseCRUDPermission,
    # Organisation
    IsOrganizationMember,
    # Décorateur
    require_permission,
)


# ===============================
# PERMISSIONS AUTH (vide)
# ===============================
# L'authentification ne définit pas de permissions métier
# Elle gère l'accès au système (login/logout/token)

PERMISSIONS = []


# ===============================
# ALIAS POUR COMPATIBILITÉ
# ===============================

IsEmployee = IsEmployeeUser


# ===============================
# EXPORTS PUBLICS
# ===============================

__all__ = [
    # Données
    'PERMISSIONS',
    # Classes de base (ré-exportées)
    'IsAuthenticated',
    'IsAdminUser',
    'IsEmployee',
    'IsEmployeeUser',
    'IsAdminOrEmployee',
    # Classes de permission
    'BaseHasPermission',
    'BaseHasAnyPermission',
    'BaseCRUDPermission',
    # Organisation
    'IsOrganizationMember',
    # Décorateur
    'require_permission',
]
