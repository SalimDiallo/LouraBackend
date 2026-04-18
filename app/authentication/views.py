"""
Authentication Views
====================
Endpoints unifiés pour l'authentification Admin et Employee.
Refactorisé pour utiliser les services et respecter SRP.
"""

import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings

from .services import (
    AuthenticationService,
    ProfileService,
    TokenService
)
from .serializers import (
    UnifiedLoginSerializer,
    AdminRegistrationSerializer,
    AdminUserResponseSerializer,
    EmployeeUserResponseSerializer,
)
from .utils import (
    convert_uuids_to_strings,
    set_jwt_cookies,
    clear_jwt_cookies,
)

logger = logging.getLogger(__name__)


# ===============================
# UNIFIED LOGIN
# ===============================

class LoginView(APIView):
    """
    Endpoint unifié de connexion.
    Délègue la logique métier au service AuthenticationService.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UnifiedLoginSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Utiliser le service pour l'authentification
                user, user_type, organization = AuthenticationService.authenticate_user(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password']
                )

                # Mettre à jour last_login
                AuthenticationService.update_last_login(user)

                # Générer les tokens via le service
                tokens = TokenService.generate_tokens_for_user(user, user_type, organization)

                # Sérialiser selon le type
                if user_type == 'employee':
                    # Passer l'organisation dans le context pour que le serializer l'utilise
                    user_data = EmployeeUserResponseSerializer(
                        user,
                        context={'request': request, 'organization': organization}
                    ).data
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

            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                if hasattr(e, 'detail'):
                    return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {'error': 'Erreur lors de la connexion'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# ADMIN REGISTRATION
# ===============================

class RegisterAdminView(APIView):
    """
    Inscription d'un Admin.
    Utilise AuthenticationService pour la création de compte.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Utiliser le service pour l'inscription
                admin = AuthenticationService.register_admin(serializer.validated_data)

                # Générer les tokens via le service
                tokens = TokenService.generate_tokens_for_user(admin, 'admin')

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

            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                if hasattr(e, 'detail'):
                    return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                return Response(
                    {'error': 'Erreur lors de l\'inscription'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# LOGOUT
# ===============================

class LogoutView(APIView):
    """
    Déconnexion avec blacklist du refresh token.
    Utilise AuthenticationService pour la gestion du logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Récupérer le refresh token
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
        if not refresh_token:
            refresh_token = request.data.get('refresh')

        # Utiliser le service pour gérer le logout
        AuthenticationService.handle_logout(refresh_token)

        # Toujours retourner succès, même si le blacklist échoue
        response = Response({
            'message': 'Déconnexion réussie'
        }, status=status.HTTP_200_OK)

        clear_jwt_cookies(response)
        return response


# ===============================
# TOKEN REFRESH
# ===============================

class RefreshTokenView(APIView):
    """
    Rafraîchissement du token d'accès.
    Utilise TokenService pour la gestion des tokens.
    """
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
            # Utiliser le service pour rafraîchir le token
            tokens = TokenService.refresh_access_token(refresh_token)

            response = Response({
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'message': 'Token rafraîchi'
            }, status=status.HTTP_200_OK)

            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        except TokenError as e:
            logger.warning(f"Token refresh error: {str(e)}")
            return Response({
                'error': 'Token invalide ou expiré'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
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
            # Passer le request au contexte pour que le serializer puisse accéder au JWT
            serializer = EmployeeUserResponseSerializer(concrete_user, context={'request': request})
        else:
            serializer = AdminUserResponseSerializer(concrete_user)

        user_data = convert_uuids_to_strings(serializer.data)

        return Response(user_data, status=status.HTTP_200_OK)


# ===============================
# PROFILE UPDATE
# ===============================

class UpdateProfileView(APIView):
    """
    Mise à jour du profil utilisateur.
    Utilise ProfileService pour la gestion du profil.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        user_type = getattr(user, 'user_type', 'unknown')

        try:
            # Utiliser le service pour mettre à jour le profil
            updated_user = ProfileService.update_profile(user, request.data)

            # Sérialiser l'utilisateur mis à jour
            if user_type == 'employee':
                serializer = EmployeeUserResponseSerializer(updated_user)
            else:
                serializer = AdminUserResponseSerializer(updated_user)

            user_data = convert_uuids_to_strings(serializer.data)

            return Response({
                'user': user_data,
                'message': 'Profil mis à jour'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Profile update error for user {user.email}: {str(e)}")
            if hasattr(e, 'detail'):
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'error': f'Erreur: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# PASSWORD CHANGE
# ===============================

class ChangePasswordView(APIView):
    """
    Changement de mot de passe.
    Utilise ProfileService pour la gestion du mot de passe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('new_password_confirm', data.get('confirm_password'))

        try:
            # Utiliser le service pour changer le mot de passe
            ProfileService.change_password(
                user=user,
                old_password=old_password,
                new_password=new_password,
                confirm_password=confirm_password
            )

            logger.info(f"Password changed successfully for user {user.email}")

            return Response({
                'message': 'Mot de passe modifié avec succès'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.warning(f"Password change failed for user {user.email}: {str(e)}")
            if hasattr(e, 'detail'):
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ===============================
# MULTI-ORGANIZATION VIEWS
# ===============================

class MyOrganizationsView(APIView):
    """
    Liste des organisations d'un employé.
    Retourne tous les memberships actifs de l'employé.

    GET /api/auth/my-organizations/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Vérifier que c'est un employé ou qu'il a un profil employé
        if getattr(user, 'user_type', None) != 'employee' and not hasattr(user, 'employee'):
            return Response({
                'error': 'Vous n\'avez pas de profil employé pour accéder à l\'organisation.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Obtenir l'objet Employee concret. Si admin, on extrait son profil employé
            employee = user.employee if hasattr(user, 'employee') else user.get_concrete_user()

            # Récupérer tous les memberships actifs avec prefetch
            from hr.models import EmployeeMembership
            memberships = EmployeeMembership.objects.filter(
                employee=employee,
                organization__is_active=True
            ).select_related(
                'organization',
                'department',
                'position',
                'assigned_role'
            ).order_by('-is_primary', 'organization__name')

            # Sérialiser
            from authentication.serializers import OrganizationMembershipSerializer
            serializer = OrganizationMembershipSerializer(memberships, many=True)

            return Response({
                'organizations': serializer.data,
                'count': memberships.count()
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching organizations for user {user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Erreur lors de la récupération des organisations'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SelectOrganizationView(APIView):
    """
    Sélectionne une organisation après login ou acceptation d'invitation.
    Génère de nouveaux JWT avec l'organisation sélectionnée.

    POST /api/auth/select-organization/
    Body: { "organization_id": "uuid" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Vérifier que c'est un employé ou qu'il a un profil employé
        if getattr(user, 'user_type', None) != 'employee' and not hasattr(user, 'employee'):
            return Response({
                'error': 'Vous n\'avez pas de profil employé pour accéder à l\'organisation.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Valider les données
        from authentication.serializers import SelectOrganizationSerializer
        serializer = SelectOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data['organization_id']

        try:
            # Obtenir l'objet Employee concret
            employee = user.employee if hasattr(user, 'employee') else user.get_concrete_user()

            # Vérifier que l'employé a un membership actif pour cette organisation
            from hr.models import EmployeeMembership
            from core.models import Organization

            membership = EmployeeMembership.objects.filter(
                employee=employee,
                organization_id=organization_id,
                organization__is_active=True
            ).select_related('organization').first()

            if not membership:
                return Response({
                    'error': "Vous n'êtes pas membre de cette organisation ou elle est inactive"
                }, status=status.HTTP_403_FORBIDDEN)

            organization = membership.organization

            # Générer de nouveaux JWT avec cette organisation
            tokens = TokenService.generate_tokens_for_user(
                employee,
                user_type='employee',
                organization=organization
            )

            # Sérialiser l'organisation
            from authentication.serializers import OrganizationMembershipSerializer
            org_data = OrganizationMembershipSerializer(membership).data

            logger.info(f"Employee {employee.email} selected organization {organization.name}")

            response = Response({
                'message': 'Organisation sélectionnée',
                'organization': org_data,
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }, status=status.HTTP_200_OK)

            # Mettre à jour les cookies
            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        except Exception as e:
            logger.error(f"Error selecting organization for user {user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Erreur lors de la sélection de l\'organisation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SwitchOrganizationView(APIView):
    """
    Change d'organisation en cours de session.
    Génère de nouveaux JWT avec la nouvelle organisation.

    POST /api/auth/switch-organization/
    Body: { "organization_id": "uuid" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Vérifier que c'est un employé ou qu'il a un profil employé
        if getattr(user, 'user_type', None) != 'employee' and not hasattr(user, 'employee'):
            return Response({
                'error': 'Vous n\'avez pas de profil employé pour accéder à cette fonctionnalité'
            }, status=status.HTTP_403_FORBIDDEN)

        # Valider les données
        from authentication.serializers import SwitchOrganizationSerializer
        serializer = SwitchOrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data['organization_id']

        try:
            # Obtenir l'objet Employee concret
            employee = user.employee if hasattr(user, 'employee') else user.get_concrete_user()

            # Vérifier que l'employé a un membership actif pour cette organisation
            from hr.models import EmployeeMembership
            from core.models import Organization

            membership = EmployeeMembership.objects.filter(
                employee=employee,
                organization_id=organization_id,
                organization__is_active=True,
                employment_status='active'
            ).select_related('organization').first()

            if not membership:
                return Response({
                    'error': "Vous n'êtes pas membre actif de cette organisation"
                }, status=status.HTTP_403_FORBIDDEN)

            organization = membership.organization

            # Générer de nouveaux JWT avec cette organisation
            tokens = TokenService.generate_tokens_for_user(
                employee,
                user_type='employee',
                organization=organization
            )

            # Sérialiser l'organisation
            from authentication.serializers import OrganizationMembershipSerializer
            org_data = OrganizationMembershipSerializer(membership).data

            logger.info(f"Employee {employee.email} switched to organization {organization.name}")

            response = Response({
                'message': 'Basculement réussi',
                'organization': org_data,
                'access': tokens['access'],
                'refresh': tokens['refresh']
            }, status=status.HTTP_200_OK)

            # Mettre à jour les cookies
            set_jwt_cookies(response, tokens['access'], tokens['refresh'])
            return response

        except Exception as e:
            logger.error(f"Error switching organization for user {user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'error': 'Erreur lors du changement d\'organisation'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
