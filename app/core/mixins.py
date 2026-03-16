"""
Core Mixins - Patterns réutilisables pour les ViewSets
======================================================

Ces mixins sont adaptés au nouveau système BaseUser avec user_type.
Admin a toutes les permissions, Employee vérifie via son rôle.
"""

from rest_framework.pagination import PageNumberPagination
import logging
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class OrganizationResolverMixin:
    """
    Mixin pour résoudre l'organisation courante selon le contexte.
    Utilise user_type au lieu d'isinstance() pour le polymorphisme.
    """
    
    def get_organization_from_request(self, raise_exception=True):
        """
        Résout l'organisation depuis la requête.
        
        Stratégie:
        - Admin: Lit organization_subdomain ou organization depuis query params/data
        - Employee: Utilise son organisation assignée
        """
        from core.models import Organization
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        
        if user_type == 'admin':
            return self._resolve_organization_for_admin(user, raise_exception)
        elif user_type == 'employee':
            return self._resolve_organization_for_employee(user)
        
        if raise_exception:
            raise serializers.ValidationError({'user': 'Type utilisateur non autorisé'})
        return None
    
    def _resolve_organization_for_admin(self, user, raise_exception=True):
        """Stratégie de résolution d'organisation pour Admin."""
        from core.models import Organization
        
        # Récupérer l'AdminUser concret
        admin = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user

        # 1. organization_subdomain depuis query params
        org_subdomain = self.request.query_params.get('organization_subdomain')
        if org_subdomain:
            try:
                org = Organization.objects.get(subdomain=org_subdomain, admin=admin)
                return org
            except Organization.DoesNotExist:
                if raise_exception:
                    raise serializers.ValidationError({
                        'organization': f'Organisation "{org_subdomain}" non trouvée'
                    })
                return None
        
        # 2. organization depuis query params
        org_id = self.request.query_params.get('organization')
        if org_id:
            org = Organization.objects.filter(id=org_id, admin=admin).first()
            if org:
                return org
            if raise_exception:
                raise serializers.ValidationError({
                    'organization': 'Organisation non trouvée'
                })
            return None
        
        # 3. organization depuis request data
        org_id = self.request.data.get('organization')
        if org_id:
            org = Organization.objects.filter(id=org_id, admin=admin).first()
            if org:
                return org
            if raise_exception:
                raise serializers.ValidationError({
                    'organization': 'Organisation non trouvée'
                })
            return None
        
        if raise_exception:
            raise serializers.ValidationError({
                'organization': 'Organisation requise'
            })
        return None
    
    def _resolve_organization_for_employee(self, user):
        """Stratégie de résolution d'organisation pour Employee."""
        concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
        return getattr(concrete, 'organization', None)
    
    def get_accessible_organizations(self):
        """Retourne les organisations accessibles par l'utilisateur."""
        from core.models import Organization
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        
        if user_type == 'admin':
            admin = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            return admin.organizations.all()
        elif user_type == 'employee':
            employee = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            org = getattr(employee, 'organization', None)
            if org:
                return Organization.objects.filter(id=org.id)
        
        return Organization.objects.none()


class OrganizationQuerySetMixin(OrganizationResolverMixin):
    """
    Mixin pour filtrer les querysets par organisation.
    Utilise user_type pour le polymorphisme.
    """
    
    # Champ FK vers Organization
    organization_field = 'organization'
    
    # Permission requise (Admin = bypass, Employee = vérification)
    view_permission = None
    
    # Si True, permet le LIST sans vérifier view_permission (utile pour les dropdowns)
    allow_list_without_permission = False
    
    def get_base_queryset(self):
        """Point d'extension pour les sous-classes."""
        return super().get_queryset()
    
    def get_queryset(self):
        """Filtre le queryset par organisation selon user_type."""
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        base_queryset = self.get_base_queryset()
        
        if user_type == 'admin':
            return self._filter_for_admin(user, base_queryset)
        elif user_type == 'employee':
            return self._filter_for_employee(user, base_queryset)
        
        return base_queryset.none()
    
    def _filter_for_admin(self, user, queryset):
        """Filtre pour Admin - a accès à toutes ses organisations."""
        from core.models import Organization
        
        admin = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
        
        org_subdomain = self.request.query_params.get('organization_subdomain')
        org_id = self.request.query_params.get('organization')
        
        if org_subdomain:
            try:
                organization = Organization.objects.get(subdomain=org_subdomain, admin=admin)
                return queryset.filter(**{self.organization_field: organization})
            except Organization.DoesNotExist:
                return queryset.none()
        elif org_id:
            try:
                organization = Organization.objects.get(id=org_id, admin=admin)
                return queryset.filter(**{self.organization_field: organization})
            except Organization.DoesNotExist:
                return queryset.none()
        else:
            # Toutes les organisations de l'admin
            org_ids = admin.organizations.values_list('id', flat=True)
            if '__' in self.organization_field:
                filter_key = f'{self.organization_field}__id__in'
            else:
                filter_key = f'{self.organization_field}__in'
            return queryset.filter(**{filter_key: org_ids})
    
    def _filter_for_employee(self, user, queryset):
        """Filtre pour Employee - accès à son organisation seulement."""
        employee = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
        
        # Vérifier la permission (sauf pour list si allow_list_without_permission=True)
        action = getattr(self, 'action', None)
        skip_permission_check = (
            self.allow_list_without_permission and 
            action == 'list'
        )
        
        if self.view_permission and not skip_permission_check:
            if not employee.has_permission(self.view_permission):
                return queryset.none()
        
        org = getattr(employee, 'organization', None)
        if org:
            return queryset.filter(**{self.organization_field: org})
        return queryset.none()


class OrganizationCreateMixin(OrganizationResolverMixin):
    """
    Mixin pour créer des objets avec l'organisation automatiquement assignée.
    """
    
    # Permission requise (Admin = bypass, Employee = vérification)
    create_permission = None
    
    def perform_create(self, serializer):
        """Crée l'objet avec l'organisation automatique."""
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        
        # Vérifier la permission pour Employee
        if user_type == 'employee' and self.create_permission:
            employee = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            if not employee.has_permission(self.create_permission):
                raise serializers.ValidationError({'permission': 'Permission refusée'})
        
        # Résoudre l'organisation
        organization = self.get_organization_from_request()
        serializer.save(organization=organization)


class ActivationMixin:
    """
    Mixin pour les actions activate/deactivate.
    """
    
    activation_permission = None
    
    def _check_activation_permission(self, user):
        """Vérifie la permission d'activation."""
        user_type = getattr(user, 'user_type', None)
        
        # Admin a toutes les permissions
        if user_type == 'admin':
            return True
        
        # Employee vérifie la permission
        if user_type == 'employee' and self.activation_permission:
            employee = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            return employee.has_permission(self.activation_permission)
        
        return True
    
    def activate(self, request, pk=None):
        """Active l'objet."""
        if not self._check_activation_permission(request.user):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        obj = self.get_object()
        obj.is_active = True
        obj.save(update_fields=['is_active'])
        
        name = getattr(obj, 'name', None) or getattr(obj, 'get_full_name', lambda: str(obj))()
        return Response({'message': f'{name} activé'}, status=status.HTTP_200_OK)
    
    def deactivate(self, request, pk=None):
        """Désactive l'objet."""
        if not self._check_activation_permission(request.user):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        obj = self.get_object()
        obj.is_active = False
        obj.save(update_fields=['is_active'])
        
        name = getattr(obj, 'name', None) or getattr(obj, 'get_full_name', lambda: str(obj))()
        return Response({'message': f'{name} désactivé'}, status=status.HTTP_200_OK)


class BaseOrganizationViewSetMixin(
    OrganizationQuerySetMixin,
    OrganizationCreateMixin,
    ActivationMixin,
):
    """
    Mixin combiné principal pour les ViewSets multi-tenant.
    
    Usage:
        class MyViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
            organization_field = 'organization'
            view_permission = 'hr.view_mymodel'
            create_permission = 'hr.create_mymodel'
            activation_permission = 'hr.activate_mymodel'
    """
    pass
