from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

from .models import Organization, Category
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    CategorySerializer
)


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