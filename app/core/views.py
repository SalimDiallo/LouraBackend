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


# -------------------------------
# Category Views
# -------------------------------

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing categories (read-only)"""
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
