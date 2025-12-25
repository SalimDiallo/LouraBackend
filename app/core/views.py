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
    RegisterSerializer,
    UserSerializer,
    OrganizationSerializer,
    OrganizationCreateSerializer,
    CategorySerializer
)
from authentication.utils import set_jwt_cookies, clear_jwt_cookies


# -------------------------------
# Authentication Views
# -------------------------------

class RegisterView(APIView):
    """API endpoint for user registration with JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Return user data
            user_data = UserSerializer(user).data

            # Create response
            response = Response({
                'user': user_data,
                'message': 'Inscription reussie',
                'access': access_token,  # Also return in body for flexibility
                'refresh': refresh_token,
            }, status=status.HTTP_201_CREATED)

            # Set tokens in HTTP-only cookies
            set_jwt_cookies(response, access_token, refresh_token)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login, Logout, Refresh and CurrentUser views have been moved to authentication app


# -------------------------------
# Organization Views
# -------------------------------

class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing organizations"""
    permission_classes = [IsAuthenticated]
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        """Return only organizations owned by the current user"""
        # Import Employee to check user type
        from hr.models import Employee

        user = self.request.user

        # If user is an Employee, return their organization
        if isinstance(user, Employee):
            if user.organization_id:
                return Organization.objects.filter(id=user.organization_id)
            # Employee without organization - return empty queryset
            return Organization.objects.none()

        # If user is AdminUser, return organizations they own
        return Organization.objects.filter(admin=user)

    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def perform_create(self, serializer):
        """Set the admin to the current user when creating an organization"""
        serializer.save(admin=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to return OrganizationSerializer for response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Use OrganizationSerializer for the response to include all fields
        instance = serializer.instance
        response_serializer = OrganizationSerializer(instance)

        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

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
        
        # Validate file size (max 5MB)
        if logo_file.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'Le fichier est trop volumineux (max 5 Mo)'},
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

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing categories (read-only)"""
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
