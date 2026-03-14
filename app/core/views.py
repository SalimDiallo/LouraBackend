from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

from .models import Organization, Category, Module, OrganizationModule
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    CategorySerializer,
    ModuleSerializer,
    OrganizationModuleSerializer
)
from .modules import ModuleRegistry


# -------------------------------
# Organization Views
# -------------------------------

class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing organizations and their settings"""
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        """Return only organizations accessible by the current user"""
        user = self.request.user
        user_type = getattr(user, 'user_type', None)

        # Employee: retourne son organisation
        if user_type == 'employee':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            org = getattr(concrete, 'organization', None)
            if org:
                return Organization.objects.filter(id=org.id)
            return Organization.objects.none()

        # Admin: retourne ses organisations
        if user_type == 'admin':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            return Organization.objects.filter(admin=concrete)

        return Organization.objects.none()

    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def perform_create(self, serializer):
        """Set the admin to the current user when creating an organization"""
        serializer.save(admin=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create to handle organization creation and associated settings (if provided).
        """
        data = request.data.copy()
        settings_data = data.pop("settings", None)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance

        # Create settings if provided
        if settings_data:
            from .models import OrganizationSettings
            settings_serializer = None
            # settings_data may be dict or string (eg, via multipart/form). Force dict.
            if isinstance(settings_data, str):
                import json
                settings_data = json.loads(settings_data)
            try:
                org_settings = instance.organization_settings
                # should not happen on create, but just in case, update
                for k, v in settings_data.items():
                    setattr(org_settings, k, v)
                org_settings.save()
            except AttributeError:
                OrganizationSettings.objects.create(organization=instance, **settings_data)

        # Use OrganizationSerializer for the response to include all fields
        response_serializer = OrganizationSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        Update the organization and create or update OrganizationSettings if 'settings' in payload
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        data = request.data.copy()
        settings_data = data.pop("settings", None)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Handle settings create or update
        if settings_data is not None:
            from .models import OrganizationSettings
            # Accept settings_data as dict or JSON string
            if isinstance(settings_data, str):
                import json
                settings_data = json.loads(settings_data)
            try:
                org_settings = instance.organization_settings
                # Update existing OrganizationSettings
                for k, v in settings_data.items():
                    setattr(org_settings, k, v)
                org_settings.save()
            except OrganizationSettings.DoesNotExist:
                # Create new OrganizationSettings
                OrganizationSettings.objects.create(organization=instance, **settings_data)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        response_serializer = OrganizationSerializer(instance)
        return Response(response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Ensure settings property can be passed when partially updating organization.
        """
        return self.update(request, *args, partial=True, **kwargs)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an organization"""
        organization = self.get_object()
        organization.is_active = True
        organization.save()
        serializer = self.get_serializer(organization)
        return Response({
            'message': f'Organisation "{organization.name}" activee',
            'organization': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an organization"""
        organization = self.get_object()
        organization.is_active = False
        organization.save()
        serializer = self.get_serializer(organization)
        return Response({
            'message': f'Organisation "{organization.name}" desactivee',
            'organization': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='logo')
    def upload_logo(self, request, pk=None):
        """Upload or delete organization logo"""
        organization = self.get_object()

        if request.method == 'DELETE':
            # Delete logo
            if organization.logo:
                organization.logo.delete(save=False)
            organization.logo = None
            organization.save()
            return Response({'message': 'Logo supprimé'}, status=status.HTTP_200_OK)

        # Upload logo
        logo_file = request.FILES.get('logo')
        if not logo_file:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
        if logo_file.content_type not in allowed_types:
            return Response(
                {'error': 'Type de fichier non autorisé. Formats acceptés: JPG, PNG, GIF, WebP, SVG'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (max 10MB)
        if logo_file.size > 10 * 1024 * 1024:
            return Response(
                {'error': 'Le fichier est trop volumineux (max 10 Mo)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete old logo if exists
        if organization.logo:
            organization.logo.delete(save=False)

        organization.logo = logo_file
        organization.save()

        serializer = self.get_serializer(organization)
        return Response({
            'message': 'Logo mis à jour avec succès',
            'organization': serializer.data
        }, status=status.HTTP_200_OK)


# -------------------------------
# Category Views
# -------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for viewing categories (read-only)"""
    # permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# -------------------------------
# Module Views
# -------------------------------

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing available modules.
    Read-only: modules are managed via management commands.
    """
    permission_classes = [IsAuthenticated]
    queryset = Module.objects.filter(is_active=True)
    serializer_class = ModuleSerializer

    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """
        Get default modules for a specific category.
        Query params: category_id or category_name
        """
        category_id = request.query_params.get('category_id')
        category_name = request.query_params.get('category_name')

        if not category_id and not category_name:
            return Response(
                {'error': 'Veuillez fournir category_id ou category_name'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get category
        try:
            if category_id:
                category = Category.objects.get(id=category_id)
            else:
                category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            return Response(
                {'error': 'Catégorie introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get default modules for this category
        default_module_defs = ModuleRegistry.get_default_modules_for_category(category.name)
        default_module_codes = [m.code for m in default_module_defs]

        # Get modules from database
        modules = Module.objects.filter(
            code__in=default_module_codes,
            is_active=True
        )

        serializer = self.get_serializer(modules, many=True)
        return Response({
            'category': CategorySerializer(category).data,
            'default_modules': serializer.data,
            'count': len(serializer.data)
        })

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get all modules grouped by category"""
        modules = Module.objects.filter(is_active=True).order_by('category', 'order', 'name')

        # Group by category
        grouped = {}
        for module in modules:
            if module.category not in grouped:
                grouped[module.category] = []
            grouped[module.category].append(ModuleSerializer(module).data)

        return Response(grouped)

    @action(detail=False, methods=['get'])
    def active_for_user(self, request):
        """
        Retourne les modules activés pour l'organisation de l'utilisateur connecté.
        Pour les admins, utilise le paramètre 'organization_subdomain' pour filtrer.
        Retourne seulement les codes de modules pour minimiser la taille de la réponse.
        """
        user = request.user
        user_type = getattr(user, 'user_type', None)

        # Récupérer le subdomain depuis les query params (pour les admins)
        organization_subdomain = request.query_params.get('organization_subdomain', None)

        # Récupérer l'organisation de l'utilisateur
        organization = None
        if user_type == 'employee':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            organization = getattr(concrete, 'organization', None)
        elif user_type == 'admin':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            orgs = Organization.objects.filter(admin=concrete)

            # Filtrer par subdomain si fourni
            if organization_subdomain:
                organization = orgs.filter(subdomain=organization_subdomain).first()
            else:
                organization = orgs.first()

        if not organization:
            return Response({
                'active_modules': [],
                'organization_id': None,
                'organization_name': None,
                'message': 'Aucune organisation trouvée pour cet utilisateur'
            })

        # Récupérer les modules actifs
        active_org_modules = OrganizationModule.objects.filter(
            organization=organization,
            is_enabled=True
        ).select_related('module')

        active_module_codes = [om.module.code for om in active_org_modules]

        return Response({
            'active_modules': active_module_codes,
            'organization_id': str(organization.id),
            'organization_name': organization.name
        })


class OrganizationModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organization modules.
    Allows enabling/disabling modules for an organization.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationModuleSerializer

    def get_queryset(self):
        """Return modules for organizations accessible by the current user"""
        user = self.request.user
        user_type = getattr(user, 'user_type', None)

        # Get organization filter from query params
        org_filter = self.request.query_params.get('organization', None)

        if user_type == 'employee':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            org = getattr(concrete, 'organization', None)
            if org:
                queryset = OrganizationModule.objects.filter(organization=org).select_related('module', 'organization')
                # Apply organization filter if provided
                if org_filter:
                    queryset = queryset.filter(organization_id=org_filter)
                return queryset.distinct()
            return OrganizationModule.objects.none()

        if user_type == 'admin':
            concrete = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user
            org_ids = Organization.objects.filter(admin=concrete).values_list('id', flat=True)
            queryset = OrganizationModule.objects.filter(organization_id__in=org_ids).select_related('module', 'organization')

            # Apply organization filter if provided
            if org_filter:
                queryset = queryset.filter(organization_id=org_filter)

            return queryset.distinct()

        return OrganizationModule.objects.none()

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable a module for an organization"""
        org_module = self.get_object()
        org_module.is_enabled = True
        org_module.save()

        serializer = self.get_serializer(org_module)
        return Response({
            'message': f'Module "{org_module.module.name}" activé',
            'organization_module': serializer.data
        })

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable a module for an organization"""
        org_module = self.get_object()

        # Check if module is core (cannot be disabled)
        if org_module.module.is_core:
            return Response(
                {'error': 'Ce module core ne peut pas être désactivé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        org_module.is_enabled = False
        org_module.save()

        serializer = self.get_serializer(org_module)
        return Response({
            'message': f'Module "{org_module.module.name}" désactivé',
            'organization_module': serializer.data
        })