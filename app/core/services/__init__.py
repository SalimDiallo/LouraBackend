"""
Core Services - Service Layer pour les opérations métier

Ce module implémente le Service Layer Pattern pour séparer la logique métier
des vues et des modèles. Chaque service encapsule une responsabilité unique.
"""
from .organization_service import OrganizationService

__all__ = ['OrganizationService']
