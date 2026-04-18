"""
Authentication personnalisée pour supporter AdminUser et Employee
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from hr.models import Employee


class MultiUserJWTAuthentication(JWTAuthentication):
    """
    Authentification JWT personnalisée qui supporte à la fois AdminUser et Employee

    Le token JWT contient un claim 'user_type' qui peut être:
    - 'admin' pour les AdminUser
    - 'employee' pour les Employee

    La méthode get_user() retourne le bon type d'utilisateur en fonction du claim.
    """

    def get_user(self, validated_token):
        """
        Retourne l'utilisateur (AdminUser ou Employee) basé sur le token
        """
        try:
            user_id = validated_token.get('user_id')
            user_type = validated_token.get('user_type', 'admin')

            # Charger le BaseUser pour éviter les conflits de types avec OutstandingToken
            from core.models import BaseUser
            try:
                user = BaseUser.objects.get(id=user_id)
                user.is_employee = (user_type == 'employee')
                return user
            except BaseUser.DoesNotExist:
                raise InvalidToken(f'{user_type.capitalize()} not found')

        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')
