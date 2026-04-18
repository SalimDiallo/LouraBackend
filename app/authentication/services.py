"""
Services d'authentification
============================
Centralise la logique métier séparée des vues et serializers.
Suit le principe Single Responsibility.
"""
import logging
from typing import Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import BaseUser, AdminUser, Organization
from hr.models import Employee

logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service principal d'authentification.
    Gère l'authentification, l'inscription et la génération de tokens.
    """

    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[BaseUser, str, Optional[Organization]]:
        """
        Authentifie un utilisateur et détermine son type.

        Args:
            email: Email de l'utilisateur
            password: Mot de passe

        Returns:
            Tuple (utilisateur concret, type_utilisateur, organisation_principale)
        """
        email = email.lower().strip()

        # Rechercher l'utilisateur avec optimisation des requêtes
        try:
            user = BaseUser.objects.select_related(
                'adminuser'
            ).prefetch_related(
                'employee__memberships__organization',
                'employee__memberships__department',
                'employee__memberships__position',
                'employee__memberships__assigned_role'
            ).get(email=email)
        except BaseUser.DoesNotExist:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise ValidationError({
                'email': 'Identifiants invalides.'
            })

        # Vérifier le mot de passe
        if not user.check_password(password):
            logger.warning(f"Invalid password attempt for user: {email}")
            raise ValidationError({
                'password': 'Identifiants invalides.'
            })

        # Vérifier si le compte est actif
        if not user.is_active:
            logger.warning(f"Login attempt with inactive account: {email}")
            raise ValidationError({
                'non_field_errors': 'Ce compte est désactivé.'
            })

        # Déterminer le type et récupérer l'utilisateur concret
        if user.user_type == 'employee':
            try:
                employee = user.employee
                # Trouver l'organisation principale
                primary_membership = employee.memberships.filter(is_primary=True).first()
                if not primary_membership:
                    primary_membership = employee.memberships.first()
                
                organization = primary_membership.organization if primary_membership else employee.organization

                if organization and not organization.is_active:
                    logger.warning(f"Employee {email} tried to login with inactive organization {organization.name}")
                    # Si l'organisation principale est inactive, on essaie d'en trouver une autre active
                    active_membership = employee.memberships.filter(organization__is_active=True).first()
                    if active_membership:
                        organization = active_membership.organization
                    else:
                        raise ValidationError({
                            'non_field_errors': "Aucune de vos organisations n'est active."
                        })

                return employee, 'employee', organization
            except Employee.DoesNotExist:
                logger.error(f"User {email} has employee type but no Employee instance")
                raise ValidationError({
                    'non_field_errors': 'Compte employé invalide.'
                })
        else:
            # AdminUser
            try:
                admin = user.adminuser
                # Un admin peut avoir plusieurs orgs, on prend la première active par défaut
                organization = admin.organizations.filter(is_active=True).first()
                return admin, 'admin', organization
            except AdminUser.DoesNotExist:
                logger.warning(f"User {email} has admin type but no AdminUser instance")
                return user, 'admin', None

    @staticmethod
    def update_last_login(user: BaseUser) -> None:
        """
        Met à jour la date de dernière connexion.

        Args:
            user: L'utilisateur qui vient de se connecter
        """
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

    @staticmethod
    @transaction.atomic
    def register_admin(data: Dict) -> AdminUser:
        """
        Inscrit un nouvel administrateur.

        Args:
            data: Données d'inscription (email, password, first_name, last_name, phone)

        Returns:
            AdminUser créé

        Raises:
            ValidationError: Si l'email existe déjà
        """
        email = data['email'].lower().strip()

        # Vérifier l'unicité de l'email
        if BaseUser.objects.filter(email=email).exists():
            raise ValidationError({
                'email': 'Cet email est déjà utilisé.'
            })

        # Créer l'admin
        admin = AdminUser.objects.create_user(
            email=email,
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
        )

        # Log l'inscription
        admin.last_login = timezone.now()
        admin.save(update_fields=['last_login'])

        logger.info(f"New admin registered: {email}")

        return admin

    @staticmethod
    def handle_logout(refresh_token: Optional[str]) -> None:
        """
        Gère la déconnexion et blacklist le token de rafraîchissement.

        Args:
            refresh_token: Token de rafraîchissement à blacklister
        """
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.debug("Refresh token blacklisted successfully")
            except Exception as e:
                # Token déjà blacklisté ou invalide, on ignore
                logger.debug(f"Could not blacklist token: {str(e)}")


class ProfileService:
    """
    Service de gestion du profil utilisateur.
    Gère les mises à jour du profil et le changement de mot de passe.
    """

    # Champs modifiables du profil
    COMMON_FIELDS = [
        'first_name',
        'last_name',
        'phone',
        'avatar_url',
        'language',
        'timezone',
        'date_of_birth',
        'address',
        'city',
        'country',
        'emergency_contact'
    ]

    @staticmethod
    @transaction.atomic
    def update_profile(user: BaseUser, data: Dict) -> BaseUser:
        """
        Met à jour le profil utilisateur.

        Args:
            user: L'utilisateur à mettre à jour
            data: Données du profil à mettre à jour

        Returns:
            Utilisateur mis à jour

        Raises:
            ValueError: Si tentative de modification de champs non autorisés
        """
        # Récupérer l'utilisateur concret (AdminUser ou Employee)
        concrete_user = user.get_concrete_user() if hasattr(user, 'get_concrete_user') else user

        # Filtrer uniquement les champs autorisés
        updates = {}
        for field in ProfileService.COMMON_FIELDS:
            if field in data:
                value = data[field]

                # Validation spécifique pour certains champs
                if field == 'phone' and value and len(value) > 20:
                    raise ValidationError({
                        'phone': 'Le numéro de téléphone est trop long (max 20 caractères).'
                    })

                updates[field] = value
                setattr(concrete_user, field, value)

        if updates:
            concrete_user.save(update_fields=list(updates.keys()))
            logger.info(f"Profile updated for user {concrete_user.email}: {list(updates.keys())}")
        else:
            logger.debug(f"No profile updates for user {concrete_user.email}")

        return concrete_user

    @staticmethod
    def change_password(user: BaseUser, old_password: str, new_password: str, confirm_password: str) -> None:
        """
        Change le mot de passe de l'utilisateur.

        Args:
            user: L'utilisateur
            old_password: Ancien mot de passe
            new_password: Nouveau mot de passe
            confirm_password: Confirmation du nouveau mot de passe

        Raises:
            ValidationError: Si validation échouée
        """
        # Validations
        if not old_password:
            raise ValidationError({
                'old_password': 'Mot de passe actuel requis'
            })

        if not new_password:
            raise ValidationError({
                'new_password': 'Nouveau mot de passe requis'
            })

        if new_password != confirm_password:
            raise ValidationError({
                'confirm_password': 'Les mots de passe ne correspondent pas'
            })

        if len(new_password) < 8:
            raise ValidationError({
                'new_password': 'Le mot de passe doit contenir au moins 8 caractères'
            })

        if not user.check_password(old_password):
            logger.warning(f"Invalid old password for user {user.email}")
            raise ValidationError({
                'old_password': 'Mot de passe actuel incorrect'
            })

        # Vérifier que le nouveau mot de passe est différent de l'ancien
        if new_password == old_password:
            raise ValidationError({
                'new_password': 'Le nouveau mot de passe doit être différent de l\'ancien'
            })

        # Changer le mot de passe
        user.set_password(new_password)
        user.save(update_fields=['password'])

        logger.info(f"Password changed for user {user.email}")


class TokenService:
    """
    Service de gestion des tokens JWT.
    Centralise la création et la validation des tokens.
    """

    @staticmethod
    def generate_tokens_for_user(user: BaseUser, user_type: str, organization: Optional[Organization] = None) -> Dict[str, str]:
        """
        Génère des tokens JWT pour un utilisateur.

        Args:
            user: L'utilisateur (AdminUser ou Employee)
            user_type: Type d'utilisateur ('admin' ou 'employee')
            organization: Organisation contextuelle
        """
        # S'assurer qu'on utilise l'instance de base pour éviter les problèmes de FK
        # si OutstandingToken est lié à BaseUser
        base_user = user
        if hasattr(user, 'baseuser_ptr'):
            base_user = user.baseuser_ptr

        refresh = RefreshToken.for_user(base_user)

        # Ajouter des claims personnalisés
        refresh['user_type'] = user_type
        refresh['email'] = base_user.email

        # Déterminer l'organisation à utiliser
        org = organization
        if not org and user_type == 'employee' and hasattr(user, 'organization'):
            org = user.organization

        if org:
            refresh['organization_id'] = str(org.id)
            refresh['organization_subdomain'] = org.subdomain

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    @staticmethod
    def get_user_from_refresh_token(refresh_token: str) -> Tuple[str, str]:
        """
        Extrait l'ID utilisateur et le type depuis un refresh token.

        Args:
            refresh_token: Le refresh token

        Returns:
            Tuple (user_id, user_type)

        Raises:
            TokenError: Si le token est invalide ou expiré
        """
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            token = RefreshToken(refresh_token)
            return str(token['user_id']), token.get('user_type', 'admin')
        except Exception as e:
            logger.error(f"Error decoding refresh token: {str(e)}")
            raise TokenError('Token invalide ou expiré')

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """
        Rafraîchit l'access token à partir du refresh token.

        Args:
            refresh_token: Le refresh token

        Returns:
            Dict avec nouveaux 'access' et 'refresh' tokens

        Raises:
            TokenError: Si le token est invalide
        """
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            token = RefreshToken(refresh_token)

            # Vérifier que l'utilisateur existe toujours et est actif
            user_id = token['user_id']
            user = BaseUser.objects.get(id=user_id)

            if not user.is_active:
                raise TokenError('Compte désactivé')

            # Créer de nouveaux tokens
            new_refresh = RefreshToken.for_user(user)

            # Préserver les claims personnalisés
            for key in ['user_type', 'email', 'organization_id', 'organization_subdomain']:
                if key in token:
                    new_refresh[key] = token[key]

            # Blacklister l'ancien token
            token.blacklist()

            return {
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh)
            }

        except BaseUser.DoesNotExist:
            logger.error(f"User not found for token refresh: {user_id}")
            raise TokenError('Utilisateur introuvable')
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise TokenError('Erreur lors du rafraîchissement du token')