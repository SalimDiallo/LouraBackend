"""
Authentication Views
====================
Endpoints unifiés pour l'authentification Admin et Employee.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.utils import timezone

from core.models import BaseUser, AdminUser
from hr.models import Employee
from .serializers import (
    UnifiedLoginSerializer,
    AdminRegistrationSerializer,
    AdminUserResponseSerializer,
    EmployeeUserResponseSerializer,
    UserResponseSerializer,
)
from .utils import (
    generate_tokens_for_user,
    convert_uuids_to_strings,
    get_user_from_token,
    set_jwt_cookies,
    clear_jwt_cookies,
)


# ===============================
# UNIFIED LOGIN
# ===============================

class LoginView(APIView):
    """
    Endpoint unifié de connexion.
    Fonctionne pour Admin et Employee.
    Retourne user_type pour la redirection frontend.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user_type = serializer.validated_data['user_type']

            # Générer les tokens JWT
            tokens = generate_tokens_for_user(user, user_type=user_type)

            # Mettre à jour last_login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Sérialiser selon le type
            if user_type == 'employee':
                user_data = EmployeeUserResponseSerializer(user).data
            else:
                user_data = AdminUserResponseSerializer(user).data

            user_data = convert_uuids_to_strings(user_data)

            response = Response({
                'user': user_data,
                'user_type': user_type,
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'message': 'Connexion réussie'
            }, status=status.HTTP_200_OK)

            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# ADMIN REGISTRATION
# ===============================

class RegisterAdminView(APIView):
    """
    Inscription d'un Admin avec création d'organisation.
    Crée simultanément AdminUser + Organization.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            result = serializer.save()
            admin = result['admin']

            # Générer les tokens JWT
            tokens = generate_tokens_for_user(admin, user_type='admin')

            # Sérialiser
            user_data = AdminUserResponseSerializer(admin).data
            user_data = convert_uuids_to_strings(user_data)

            response = Response({
                'user': user_data,
                'user_type': 'admin',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'message': 'Inscription réussie'
            }, status=status.HTTP_201_CREATED)

            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# LOGOUT
# ===============================

class LogoutView(APIView):
    """Déconnexion avec blacklist du refresh token"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if not refresh_token:
                refresh_token = request.data.get('refresh')

            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            response = Response({
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
            clear_jwt_cookies(response)
            return response

        except Exception:
            response = Response({
                'message': 'Déconnexion réussie'
            }, status=status.HTTP_200_OK)
            clear_jwt_cookies(response)
            return response


# ===============================
# TOKEN REFRESH
# ===============================

class RefreshTokenView(APIView):
    """Rafraîchissement du token d'accès"""
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token manquant'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_data = get_user_from_token(refresh_token)
            user_id = token_data.get('user_id')
            user_type = token_data.get('user_type', 'admin')

            # Récupérer l'utilisateur
            user = BaseUser.objects.get(id=user_id)

            if not user.is_active:
                return Response({
                    'error': 'Compte désactivé'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Générer nouveaux tokens
            tokens = generate_tokens_for_user(user.get_concrete_user(), user_type=user_type)

            response = Response({
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'message': 'Token rafraîchi'
            }, status=status.HTTP_200_OK)

            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        except BaseUser.DoesNotExist:
            return Response({
                'error': 'Utilisateur introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        except TokenError:
            return Response({
                'error': 'Token invalide ou expiré'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({
                'error': 'Erreur lors du rafraîchissement'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===============================
# CURRENT USER
# ===============================

class CurrentUserView(APIView):
    """Retourne l'utilisateur connecté avec ses permissions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_type = getattr(user, 'user_type', 'unknown')

        # Récupérer l'utilisateur concret
        concrete_user = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user

        if user_type == 'employee':
            serializer = EmployeeUserResponseSerializer(concrete_user)
        else:
            serializer = AdminUserResponseSerializer(concrete_user)

        user_data = convert_uuids_to_strings(serializer.data)

        return Response(user_data, status=status.HTTP_200_OK)


# ===============================
# PROFILE UPDATE
# ===============================

class UpdateProfileView(APIView):
    """Mise à jour du profil utilisateur"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        data = request.data
        print(data)
        # Champs modifiables par tous
        common_fields = ['first_name', 'last_name', 'phone', 'avatar_url', 'language', 'timezone']
        
        # Champs supplémentaires pour Employee
        employee_fields = [
            'date_of_birth',
            'address',
            'city',
            'country',
            'emergency_contact',
        ]


        try:
            # Mettre à jour les champs communs
            for field in common_fields:
                if field in data:
                    setattr(user, field, data[field])

            # Si c'est un Employee, mettre à jour les champs spécifiques
            if hasattr(user, 'user_type') and user.user_type == 'employee':
                for field in employee_fields:
                    if field in data:
                        setattr(user, field, data[field])

            user.save()

            # Sérialiser
            if hasattr(user, 'user_type') and user.user_type == 'employee':
                serializer = EmployeeUserResponseSerializer(user)
            else:
                serializer = AdminUserResponseSerializer(user)

            return Response({
                'user': convert_uuids_to_strings(serializer.data),
                'message': 'Profil mis à jour'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': f'Erreur: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# PASSWORD CHANGE
# ===============================

class ChangePasswordView(APIView):
    """Changement de mot de passe"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('new_password_confirm', data.get('confirm_password'))

        # Validations
        if not old_password:
            return Response({
                'error': 'Mot de passe actuel requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not new_password:
            return Response({
                'error': 'Nouveau mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({
                'error': 'Les mots de passe ne correspondent pas'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({
                'error': 'Le mot de passe doit contenir au moins 8 caractères'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({
                'error': 'Mot de passe actuel incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({
            'message': 'Mot de passe modifié avec succès'
        }, status=status.HTTP_200_OK)
