"""
Core Mixins - Patterns réutilisables pour les ViewSets

Ce module implémente les design patterns suivants :
- Mixin Pattern : Code réutilisable pour les ViewSets
- Strategy Pattern : Résolution d'organisation selon le type d'utilisateur
- Template Method : Structure commune avec points d'extension

Ces mixins sont conçus pour être indépendants et réutilisables par toutes les apps.
"""
import logging
from rest_framework import serializers
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class OrganizationResolverMixin:
    """
    Mixin pour résoudre l'organisation courante selon le contexte.
    
    Implémente le Strategy Pattern pour différencier AdminUser et Employee.
    
    Usage:
        class MyViewSet(OrganizationResolverMixin, viewsets.ModelViewSet):
            pass
    """
    
    def get_organization_from_request(self, raise_exception=True):
        """
        Résout l'organisation depuis la requête.
        
        Stratégie:
        1. AdminUser : Lit organization_subdomain ou organization depuis query params/data
        2. Employee : Utilise son organisation assignée
        
        Args:
            raise_exception: Si True, lève une exception si l'organisation n'est pas trouvée
            
        Returns:
            Organization ou None
        """
        from core.models import AdminUser, Organization
        from hr.models import Employee
        
        user = self.request.user
        
        if isinstance(user, AdminUser):
            return self._resolve_organization_for_admin(user, raise_exception)
        elif isinstance(user, Employee):
            return self._resolve_organization_for_employee(user)
        
        if raise_exception:
            raise serializers.ValidationError({'user': 'Type utilisateur non autorisé'})
        return None
    
    def _resolve_organization_for_admin(self, user, raise_exception=True):
        """Stratégie de résolution d'organisation pour AdminUser."""
        from core.models import Organization

        # 1. Essayer organization_subdomain depuis query params
        org_subdomain = self.request.query_params.get('organization_subdomain')
        if org_subdomain:
            logger.info(f"Searching for organization with subdomain: {org_subdomain}")
            logger.info(f"Current user: {user.email} (ID: {user.id})")

            try:
                # Chercher d'abord sans filtre admin pour voir si l'org existe
                org_exists = Organization.objects.filter(subdomain=org_subdomain).first()
                if org_exists:
                    logger.info(f"Organization found: {org_exists.name}, Admin: {org_exists.admin.email if org_exists.admin else 'None'}")
                else:
                    logger.error(f"No organization with subdomain '{org_subdomain}' exists at all")

                # Maintenant chercher avec le filtre admin
                org = Organization.objects.get(subdomain=org_subdomain, admin=user)
                logger.info(f"Organization matched for user: {org.name} (ID: {org.id})")
                return org
            except Organization.DoesNotExist:
                if raise_exception:
                    logger.error(f"Organization with subdomain {org_subdomain} not found for user {user.email}")
                    raise serializers.ValidationError({
                        'organization': f'Organisation avec le subdomain "{org_subdomain}" non trouvée ou accès refusé'
                    })
                return None
        
        # 2. Essayer organization ID depuis query params
        org_id = self.request.query_params.get('organization')
        if org_id:
            org = Organization.objects.filter(id=org_id, admin=user).first()
            if org:
                return org
            if raise_exception:
                raise serializers.ValidationError({
                    'organization': 'Organisation non trouvée ou accès refusé'
                })
            return None
        
        # 3. Essayer organization depuis request data
        org_id = self.request.data.get('organization')
        if org_id:
            org = Organization.objects.filter(id=org_id, admin=user).first()
            if org:
                return org
            if raise_exception:
                raise serializers.ValidationError({
                    'organization': 'Organisation non trouvée ou accès refusé'
                })
            return None
        
        if raise_exception:
            raise serializers.ValidationError({
                'organization': 'Organisation requise (organization_subdomain ou organization)'
            })
        return None
    
    def _resolve_organization_for_employee(self, user):
        """Stratégie de résolution d'organisation pour Employee."""
        return user.organization
    
    def get_accessible_organizations(self):
        """
        Retourne les organisations accessibles par l'utilisateur courant.
        
        Returns:
            QuerySet d'organisations
        """
        from core.models import AdminUser, Organization
        from hr.models import Employee
        
        user = self.request.user
        
        if isinstance(user, AdminUser):
            return user.organizations.all()
        elif isinstance(user, Employee):
            return Organization.objects.filter(id=user.organization_id)
        
        return Organization.objects.none()


class OrganizationQuerySetMixin(OrganizationResolverMixin):
    """
    Mixin pour filtrer les querysets par organisation.
    
    Implémente le Template Method Pattern :
    - get_queryset() est la méthode template
    - get_base_queryset() est le point d'extension
    
    Usage:
        class MyViewSet(OrganizationQuerySetMixin, viewsets.ModelViewSet):
            model_class = MyModel  # Le modèle doit avoir un champ 'organization'
    """
    
    # Champ FK vers Organization (peut être 'organization' ou 'employee__organization')
    organization_field = 'organization'
    
    # Permission requise pour les employés (None = pas de vérification)
    view_permission = None
    
    def get_base_queryset(self):
        """
        Point d'extension pour les sous-classes.
        Retourne le queryset de base avant filtrage par organisation.
        """
        return super().get_queryset()
    
    def get_queryset(self):
        """
        Template Method qui filtre le queryset par organisation.
        """
        from core.models import AdminUser
        from hr.models import Employee
        
        user = self.request.user
        base_queryset = self.get_base_queryset()
        
        if isinstance(user, AdminUser):
            return self._filter_for_admin(user, base_queryset)
        elif isinstance(user, Employee):
            return self._filter_for_employee(user, base_queryset)
        
        return base_queryset.none()
    
    def _filter_for_admin(self, user, queryset):
        """Filtre le queryset pour un AdminUser."""
        from core.models import Organization
        
        org_subdomain = self.request.query_params.get('organization_subdomain')
        org_id = self.request.query_params.get('organization')
        
        if org_subdomain:
            try:
                organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                return queryset.filter(**{self.organization_field: organization})
            except Organization.DoesNotExist:
                return queryset.none()
        elif org_id:
            try:
                organization = Organization.objects.get(id=org_id, admin=user)
                return queryset.filter(**{self.organization_field: organization})
            except Organization.DoesNotExist:
                return queryset.none()
        else:
            # Retourner les objets de toutes les organisations de l'admin
            org_ids = user.organizations.values_list('id', flat=True)
            filter_key = f'{self.organization_field}_id__in' if self.organization_field == 'organization' else f'{self.organization_field}__id__in'
            return queryset.filter(**{filter_key.replace('_id__in', '__in') if '__' in self.organization_field else filter_key: org_ids})
    
    def _filter_for_employee(self, user, queryset):
        """Filtre le queryset pour un Employee."""
        # Vérifier la permission si spécifiée
        if self.view_permission and not user.has_permission(self.view_permission):
            return queryset.none()
        
        return queryset.filter(**{self.organization_field: user.organization})


class OrganizationCreateMixin(OrganizationResolverMixin):
    """
    Mixin pour créer des objets avec l'organisation automatiquement assignée.
    
    Usage:
        class MyViewSet(OrganizationCreateMixin, viewsets.ModelViewSet):
            create_permission = 'can_create_mymodel'  # Permission requise pour les employés
    """
    
    # Permission requise pour les employés (None = pas de vérification)
    create_permission = None
    
    def perform_create(self, serializer):
        """
        Crée l'objet avec l'organisation automatiquement assignée.
        """
        from hr.models import Employee
        
        user = self.request.user
        
        # Vérifier la permission pour les employés
        if isinstance(user, Employee):
            if self.create_permission and not user.has_permission(self.create_permission):
                logger.warning(f"Employee {user.email} lacks permission: {self.create_permission}")
                raise serializers.ValidationError({'permission': 'Permission refusée'})
        
        # Résoudre l'organisation
        organization = self.get_organization_from_request()

        # Obtenir le nom du modèle pour le log
        serializer_class = self.get_serializer_class() if hasattr(self, 'get_serializer_class') else self.serializer_class
        model_name = serializer_class.Meta.model.__name__ if serializer_class else "Unknown"

        logger.info(f"Creating {model_name} for organization: {organization.name}")
        serializer.save(organization=organization)


class ActivationMixin:
    """
    Mixin pour les actions activate/deactivate.
    
    Usage:
        class MyViewSet(ActivationMixin, viewsets.ModelViewSet):
            activation_permission = 'can_activate_mymodel'
    """
    
    activation_permission = None
    
    def _check_activation_permission(self, user):
        """Vérifie si l'utilisateur a la permission d'activation."""
        from hr.models import Employee
        
        if isinstance(user, Employee):
            if self.activation_permission and not user.has_permission(self.activation_permission):
                return False
        return True
    
    def activate(self, request, pk=None):
        """Active l'objet."""
        from rest_framework.response import Response
        from rest_framework import status
        
        if not self._check_activation_permission(request.user):
            return Response({
                'message': 'Vous n\'avez pas accès à cette permission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        obj = self.get_object()
        obj.is_active = True
        obj.save(update_fields=['is_active'])
        
        name = getattr(obj, 'name', None) or getattr(obj, 'get_full_name', lambda: str(obj))()
        return Response({
            'message': f'{name} activé'
        }, status=status.HTTP_200_OK)
    
    def deactivate(self, request, pk=None):
        """Désactive l'objet."""
        from rest_framework.response import Response
        from rest_framework import status
        
        if not self._check_activation_permission(request.user):
            return Response({
                'message': 'Vous n\'avez pas accès à cette permission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        obj = self.get_object()
        obj.is_active = False
        obj.save(update_fields=['is_active'])
        
        name = getattr(obj, 'name', None) or getattr(obj, 'get_full_name', lambda: str(obj))()
        return Response({
            'message': f'{name} désactivé'
        }, status=status.HTTP_200_OK)


class BaseOrganizationViewSetMixin(
    OrganizationQuerySetMixin,
    OrganizationCreateMixin,
    ActivationMixin
):
    """
    Mixin combiné pour les ViewSets avec filtrage et création par organisation.
    
    C'est le mixin principal à utiliser pour la plupart des ViewSets.
    
    Usage:
        class MyViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
            organization_field = 'organization'  # ou 'employee__organization'
            view_permission = 'can_view_mymodel'
            create_permission = 'can_create_mymodel'
            activation_permission = 'can_activate_mymodel'
    """
    pass
