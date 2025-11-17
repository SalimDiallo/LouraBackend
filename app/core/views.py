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
    LoginSerializer,
    UserSerializer,
    OrganizationSerializer,
    OrganizationCreateSerializer,
    CategorySerializer
)


# -------------------------------
# JWT Cookie Helper Functions
# -------------------------------

def set_jwt_cookies(response, access_token, refresh_token):
    """Set JWT tokens in HTTP-only cookies"""
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
    """Clear JWT cookies"""
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )


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


class LoginView(APIView):
    """API endpoint for user login with JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Return user data
            user_data = UserSerializer(user).data

            # Create response
            response = Response({
                'user': user_data,
                'message': 'Connexion reussie',
                'access': access_token,  # Also return in body for flexibility
                'refresh': refresh_token,
            }, status=status.HTTP_200_OK)

            # Set tokens in HTTP-only cookies
            set_jwt_cookies(response, access_token, refresh_token)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API endpoint for user logout - blacklist refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get refresh token from cookie or request body
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if not refresh_token:
                refresh_token = request.data.get('refresh')

            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Create response
            response = Response({
                'message': 'Deconnexion reussie'
            }, status=status.HTTP_200_OK)

            # Clear cookies
            clear_jwt_cookies(response)

            return response

        except Exception as e:
            response = Response({
                'error': 'Erreur lors de la deconnexion'
            }, status=status.HTTP_400_BAD_REQUEST)

            # Still clear cookies even if blacklist fails
            clear_jwt_cookies(response)

            return response


class RefreshTokenView(APIView):
    """API endpoint to refresh access token using refresh token"""
    permission_classes = [AllowAny]

    def post(self, request):
        # Get refresh token from cookie or request body
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token manquant'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate and refresh token
            refresh = RefreshToken(refresh_token)

            # Get new access token
            access_token = str(refresh.access_token)

            # If rotation is enabled, get new refresh token
            new_refresh_token = str(refresh) if settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS'] else refresh_token

            # Create response
            response = Response({
                'access': access_token,
                'refresh': new_refresh_token,
                'message': 'Token rafraichi avec succes'
            }, status=status.HTTP_200_OK)

            # Set new tokens in cookies
            set_jwt_cookies(response, access_token, new_refresh_token)

            return response

        except TokenError as e:
            return Response({
                'error': 'Token invalide ou expire'
            }, status=status.HTTP_401_UNAUTHORIZED)


class CurrentUserView(APIView):
    """API endpoint to get current authenticated user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        return Organization.objects.filter(admin=self.request.user)

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
