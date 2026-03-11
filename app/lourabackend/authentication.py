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

            if user_type == 'employee':
                # Chercher un Employee
                try:
                    user = Employee.objects.get(id=user_id)
                    # Ajouter un attribut pour identifier le type
                    user.is_employee = True
                    return user
                except Employee.DoesNotExist:
                    raise InvalidToken('Employee not found')
            else:
                # Chercher un AdminUser (comportement par défaut)
                AdminUser = get_user_model()
                try:
                    user = AdminUser.objects.get(id=user_id)
                    # Ajouter un attribut pour identifier le type
                    user.is_employee = False
                    return user
                except AdminUser.DoesNotExist:
                    raise InvalidToken('AdminUser not found')

        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')
