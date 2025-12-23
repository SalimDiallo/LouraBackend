from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from core.models import AdminUser
from core.serializers import UserSerializer
from hr.models import Employee
from hr.serializers import EmployeeSerializer
from .serializers import AdminLoginSerializer, EmployeeLoginSerializer
from .utils import (
    generate_tokens_for_user,
    convert_uuids_to_strings,
    get_user_from_token,
    set_jwt_cookies,
    clear_jwt_cookies,
)


# -------------------------------
# Admin Authentication Views
# -------------------------------

class AdminLoginView(APIView):
    """API endpoint for admin user login with JWT"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate JWT tokens using utility
            tokens = generate_tokens_for_user(user, user_type='admin')

            # Return user data
            user_data = UserSerializer(user).data

            # Create response
            response = Response({
                'user': user_data,
                'message': 'Connexion reussie',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
            }, status=status.HTTP_200_OK)

            # Set tokens in HTTP-only cookies
            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Employee Authentication Views
# -------------------------------

class EmployeeLoginView(APIView):
    """API endpoint for employee login"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.validated_data['employee']

            # Generate JWT tokens using utility
            tokens = generate_tokens_for_user(employee, user_type='employee')

            # Update last login
            employee.last_login = timezone.now()
            employee.save(update_fields=['last_login'])

            # Return employee data
            employee_data = EmployeeSerializer(employee).data
            employee_data = convert_uuids_to_strings(employee_data)

            response = Response({
                'employee': employee_data,
                'message': 'Connexion reussie',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
            }, status=status.HTTP_200_OK)

            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Common Authentication Views
# -------------------------------

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
    """API endpoint to refresh access token using refresh token (supports both admin and employee)"""
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
            # Get user info from token to determine type
            token_data = get_user_from_token(refresh_token)
            user_type = token_data.get('user_type', 'admin')

            if user_type == 'employee':
                # Handle employee token refresh
                user_id = token_data.get('user_id')
                employee = Employee.objects.get(id=user_id)

                # Check if employee is active
                if not employee.is_active:
                    return Response({
                        'error': 'Compte desactive'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Generate new tokens
                tokens = generate_tokens_for_user(employee, user_type='employee')
                access_token = tokens['access']
                new_refresh_token = tokens['refresh']

            else:
                # Handle admin token refresh (standard way)
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token)
                new_refresh_token = str(refresh) if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False) else refresh_token

            # Create response
            response = Response({
                'access': access_token,
                'refresh': new_refresh_token,
                'message': 'Token rafraichi avec succes'
            }, status=status.HTTP_200_OK)

            # Set new tokens in cookies
            set_jwt_cookies(response, access_token, new_refresh_token)

            return response

        except Employee.DoesNotExist:
            return Response({
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except TokenError as e:
            return Response({
                'error': 'Token invalide ou expire'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'error': 'Erreur lors du rafraichissement du token'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CurrentUserView(APIView):
    """API endpoint to get current authenticated user (supports both admin and employee)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if user is an Employee
        if isinstance(user, Employee):
            # Use Employee serializer
            serializer = EmployeeSerializer(user)
            user_data = serializer.data
            user_data = convert_uuids_to_strings(user_data)

            return Response({
                'user_type': 'employee',
                'employee': user_data,
            }, status=status.HTTP_200_OK)
        else:
            # Use AdminUser serializer
            serializer = UserSerializer(user)

            return Response({
                'user_type': 'admin',
                'user': serializer.data,
            }, status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    """API endpoint to update current user profile (supports both admin and employee)"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        data = request.data

        # Check if user is an Employee
        if isinstance(user, Employee):
            # Update employee fields
            allowed_fields = ['phone', 'address', 'emergency_contact', 'emergency_phone']
            
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            try:
                user.save()
                serializer = EmployeeSerializer(user)
                user_data = serializer.data
                user_data = convert_uuids_to_strings(user_data)

                return Response({
                    'user_type': 'employee',
                    'employee': user_data,
                    'message': 'Profil mis à jour avec succès'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': f'Erreur lors de la mise à jour: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Update admin user fields
            allowed_fields = ['first_name', 'last_name']
            
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            try:
                user.save()
                serializer = UserSerializer(user)

                return Response({
                    'user_type': 'admin',
                    'user': serializer.data,
                    'message': 'Profil mis à jour avec succès'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': f'Erreur lors de la mise à jour: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """API endpoint to change password (supports both admin and employee)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        # Validate required fields
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        new_password_confirm = data.get('new_password_confirm')

        if not old_password:
            return Response({
                'error': 'Le mot de passe actuel est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({
                'error': 'Le nouveau mot de passe est requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != new_password_confirm:
            return Response({
                'error': 'Les mots de passe ne correspondent pas'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({
                'error': 'Le mot de passe doit contenir au moins 8 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is an Employee
        if isinstance(user, Employee):
            # Verify old password for employee
            if not user.check_password(old_password):
                return Response({
                    'error': 'Le mot de passe actuel est incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Set new password
            user.set_password(new_password)
            user.save()

            return Response({
                'message': 'Mot de passe modifié avec succès'
            }, status=status.HTTP_200_OK)
        else:
            # Verify old password for admin
            if not user.check_password(old_password):
                return Response({
                    'error': 'Le mot de passe actuel est incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Set new password
            user.set_password(new_password)
            user.save()

            return Response({
                'message': 'Mot de passe modifié avec succès'
            }, status=status.HTTP_200_OK)

