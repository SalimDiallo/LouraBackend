"""
Organization Service - Service Layer pour les opérations sur les organisations

Ce service encapsule toute la logique métier liée aux organisations.
Il applique le principe Single Responsibility.
"""
import logging
from typing import Optional, List
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Service pour les opérations métier sur les organisations.
    
    Ce service est indépendant des vues et peut être utilisé par :
    - Les ViewSets
    - Les commandes management
    - Les tâches Celery
    - Les tests
    
    Principe: Single Responsibility - Ce service ne gère QUE les organisations.
    """
    
    @staticmethod
    def get_organizations_for_admin(admin_user) -> QuerySet:
        """
        Retourne les organisations gérées par un admin.
        
        Args:
            admin_user: Instance de AdminUser
            
        Returns:
            QuerySet d'organisations
        """
        from .models import Organization
        return Organization.objects.filter(admin=admin_user)
    
    @staticmethod
    def get_organization_by_subdomain(subdomain: str, admin_user=None):
        """
        Récupère une organisation par son subdomain.
        
        Args:
            subdomain: Le subdomain de l'organisation
            admin_user: Si fourni, vérifie que l'admin a accès
            
        Returns:
            Organization ou None
        """
        from .models import Organization
        
        filters = {'subdomain': subdomain}
        if admin_user:
            filters['admin'] = admin_user
            
        return Organization.objects.filter(**filters).first()
    
    @staticmethod
    def get_organization_by_id(org_id: str, admin_user=None):
        """
        Récupère une organisation par son ID.
        
        Args:
            org_id: L'ID de l'organisation
            admin_user: Si fourni, vérifie que l'admin a accès
            
        Returns:
            Organization ou None
        """
        from .models import Organization
        
        filters = {'id': org_id}
        if admin_user:
            filters['admin'] = admin_user
            
        return Organization.objects.filter(**filters).first()
    
    @staticmethod
    def create_organization(admin_user, name: str, subdomain: str, **kwargs):
        """
        Crée une nouvelle organisation.
        
        Args:
            admin_user: L'admin qui sera propriétaire
            name: Nom de l'organisation
            subdomain: Subdomain unique
            **kwargs: Autres champs (category, logo_url, etc.)
            
        Returns:
            Organization créée
        """
        from .models import Organization, OrganizationSettings
        
        org = Organization.objects.create(
            admin=admin_user,
            name=name,
            subdomain=subdomain,
            **kwargs
        )
        
        # Créer les settings par défaut
        OrganizationSettings.objects.create(organization=org)
        
        logger.info(f"Organization '{name}' created by {admin_user.email}")
        return org
    
    @staticmethod
    def activate_organization(organization) -> bool:
        """Active une organisation."""
        organization.is_active = True
        organization.save(update_fields=['is_active'])
        logger.info(f"Organization '{organization.name}' activated")
        return True
    
    @staticmethod
    def deactivate_organization(organization) -> bool:
        """Désactive une organisation."""
        organization.is_active = False
        organization.save(update_fields=['is_active'])
        logger.info(f"Organization '{organization.name}' deactivated")
        return True
    
    @staticmethod
    def can_access_organization(user, organization) -> bool:
        """
        Vérifie si un utilisateur a accès à une organisation.
        
        Args:
            user: AdminUser ou Employee
            organization: L'organisation à vérifier
            
        Returns:
            bool
        """
        from .models import AdminUser
        from hr.models import Employee
        
        if isinstance(user, AdminUser):
            return organization.admin == user
        elif isinstance(user, Employee):
            return user.organization_id == organization.id
        
        return False
