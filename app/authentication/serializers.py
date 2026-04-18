"""
Authentication Serializers
==========================
Serializers unifiés pour l'authentification Admin et Employee.
"""

from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from core.models import BaseUser, AdminUser, Organization, Category
from hr.models import Employee


class UnifiedLoginSerializer(serializers.Serializer):
    """
    Serializer simplifié pour la connexion.
    Valide uniquement le format des données, la logique d'authentification
    est déléguée au service AuthenticationService.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        min_length=1
    )

    def validate_email(self, value):
        """Normalise l'email en minuscules et supprime les espaces."""
        return value.lower().strip()

    def validate(self, data):
        """Validation basique des champs requis."""
        if not data.get('email'):
            raise serializers.ValidationError({
                'email': 'Email requis'
            })
        if not data.get('password'):
            raise serializers.ValidationError({
                'password': 'Mot de passe requis'
            })
        return data


class AdminRegistrationSerializer(serializers.Serializer):
    """
    Serializer simplifié pour l'inscription d'un Admin.
    Valide uniquement les données, la création est déléguée
    au service AuthenticationService.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Minimum 8 caractères"
    )
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    phone = serializers.CharField(
        required=False,
        max_length=20,
        allow_blank=True,
        default=''
    )

    def validate_email(self, value):
        """Normalise et valide l'unicité de l'email."""
        email = value.lower().strip()
        if BaseUser.objects.filter(email=email).exists():
            raise serializers.ValidationError('Cet email est déjà utilisé.')
        return email

    def validate_password(self, value):
        """Validation basique du mot de passe."""
        if len(value) < 8:
            raise serializers.ValidationError(
                'Le mot de passe doit contenir au moins 8 caractères.'
            )
        # On pourrait ajouter d'autres validations ici
        # (majuscules, chiffres, caractères spéciaux, etc.)
        return value


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer pour la réponse utilisateur après connexion"""

    class Meta:
        model = BaseUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'avatar_url', 'user_type', 'language', 'timezone',
            'is_active', 'email_verified', 'last_login',
            'created_at', 'updated_at',
            # Champs personnels ajoutés à BaseUser
            'date_of_birth', 'address', 'city', 'country', 'emergency_contact'
        ]
        read_only_fields = fields


class AdminUserResponseSerializer(UserResponseSerializer):
    """Serializer pour AdminUser avec ses organisations"""
    organizations = serializers.SerializerMethodField()

    class Meta(UserResponseSerializer.Meta):
        model = AdminUser
        fields = UserResponseSerializer.Meta.fields + ['organizations']

    def get_organizations(self, obj):
        # Organisations owned by the admin
        admin_orgs = [{
            'id': str(org.id),
            'name': org.name,
            'subdomain': org.subdomain,
            'logo_url': org.logo_url,
            'is_active': org.is_active,
            'role': 'admin'
        } for org in obj.organizations.all()]

        # Organisations the admin is invited to as an employee
        employee_orgs = []
        if hasattr(obj, 'employee'):
            employee_orgs = [{
                'id': str(m.organization.id),
                'name': m.organization.name,
                'subdomain': m.organization.subdomain,
                'logo_url': m.organization.logo_url,
                'is_active': m.organization.is_active,
                'role': 'employee'
            } for m in obj.employee.memberships.all()]

        # Combine and remove duplicates based on id
        seen = set()
        combined = []
        for org in admin_orgs + employee_orgs:
            if org['id'] not in seen:
                seen.add(org['id'])
                combined.append(org)
                
        return combined


class EmployeeUserResponseSerializer(UserResponseSerializer):
    """Serializer pour Employee avec son organisation"""
    organization = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    organizations = serializers.SerializerMethodField()

    class Meta(UserResponseSerializer.Meta):
        model = Employee
        fields = UserResponseSerializer.Meta.fields + [
            'employee_id',
            'organization',
            'department',
            'position',
            'employment_status',
            'permissions',
            # Note: date_of_birth, address, city, country, emergency_contact sont maintenant dans UserResponseSerializer (BaseUser)
            'contract',
            'hire_date',
            'termination_date',
            'manager',
            'organizations',
        ]

    def _get_current_membership(self, obj):
        """
        Helper pour récupérer le membership correspondant à l'organisation du JWT.
        Cache le résultat pour éviter des requêtes multiples.

        Priority:
            1. Organisation passée directement dans le context (pour login)
            2. Organisation extraite du JWT
            3. None (utilisera membership primaire en fallback)
        """
        if hasattr(self, '_cached_membership'):
            return self._cached_membership

        # 1. Vérifier si une organisation est passée directement dans le context
        organization = self.context.get('organization')
        if organization:
            from hr.models import EmployeeMembership
            try:
                membership = EmployeeMembership.objects.select_related(
                    'organization', 'department', 'position', 'assigned_role'
                ).prefetch_related('assigned_role__permissions').get(
                    employee=obj,
                    organization=organization
                )
                self._cached_membership = membership
                return membership
            except EmployeeMembership.DoesNotExist:
                pass

        # 2. Essayer d'extraire l'organisation du JWT
        request = self.context.get('request')
        org_id = None

        if request and hasattr(request, 'auth') and request.auth:
            org_id = request.auth.get('organization_id')

        if org_id:
            from hr.models import EmployeeMembership
            try:
                membership = EmployeeMembership.objects.select_related(
                    'organization', 'department', 'position', 'assigned_role'
                ).prefetch_related('assigned_role__permissions').get(
                    employee=obj,
                    organization_id=org_id
                )
                self._cached_membership = membership
                return membership
            except EmployeeMembership.DoesNotExist:
                pass

        self._cached_membership = None
        return None

    def get_organization(self, obj):
        """
        Retourne l'organisation depuis le JWT si disponible,
        sinon fallback sur l'organisation du modèle Employee
        """
        request = self.context.get('request')

        # Si on a le request, essayer de récupérer l'organisation du JWT
        if request and hasattr(request, 'auth') and request.auth:
            org_id = request.auth.get('organization_id')

            if org_id:
                # Récupérer l'organisation depuis la DB avec l'ID du JWT
                from core.models import Organization
                try:
                    org = Organization.objects.get(id=org_id)
                    return {
                        'id': str(org.id),
                        'name': org.name,
                        'subdomain': org.subdomain,
                        'logo_url': org.logo_url,
                        'settings': {
                            'currency': org.settings.currency,
                            'country': org.settings.country,
                        }
                    }
                except Organization.DoesNotExist:
                    pass

        # Fallback sur l'organisation du modèle
        if obj.organization:
            return {
                'id': str(obj.organization.id),
                'name': obj.organization.name,
                'subdomain': obj.organization.subdomain,
                'logo_url': obj.organization.logo_url,
                'settings': {
                    'currency': obj.organization.settings.currency,
                    'country': obj.organization.settings.country,
                }
            }
        return None

    def get_department(self, obj):
        """
        Retourne le département de l'employé pour l'organisation courante.
        Si un JWT est présent, utilise le département du membership correspondant.
        """
        membership = self._get_current_membership(obj)

        if membership and membership.department:
            return {
                'id': str(membership.department.id),
                'name': membership.department.name
            }

        # Fallback sur le département de l'organisation par défaut
        if obj.department:
            return {
                'id': str(obj.department.id),
                'name': obj.department.name
            }
        return None

    def get_position(self, obj):
        """
        Retourne la position de l'employé pour l'organisation courante.
        Si un JWT est présent, utilise la position du membership correspondant.
        """
        membership = self._get_current_membership(obj)

        if membership and membership.position:
            return {
                'id': str(membership.position.id),
                'title': membership.position.title
            }

        # Fallback sur la position de l'organisation par défaut
        if obj.position:
            return {
                'id': str(obj.position.id),
                'title': obj.position.title
            }
        return None

    def get_permissions(self, obj):
        """
        Retourne la liste des permissions de l'employé pour l'organisation courante.
        Si un JWT est présent, utilise l'organisation du JWT pour déterminer les permissions.
        """
        permission_codes = set()
        membership = self._get_current_membership(obj)

        if membership:
            # Permissions du rôle dans cette organisation
            if membership.assigned_role:
                permission_codes.update(
                    membership.assigned_role.permissions.values_list('code', flat=True)
                )
        else:
            # Fallback: utiliser le rôle de l'organisation par défaut
            if obj.assigned_role:
                permission_codes.update(
                    obj.assigned_role.permissions.values_list('code', flat=True)
                )

        # Ajouter les permissions custom (globales à l'employé)
        permission_codes.update(
            obj.custom_permissions.values_list('code', flat=True)
        )

        return list(permission_codes)

    def get_organizations(self, obj):
        """Retourne la liste des organisations de l'employé via ses memberships"""
        return [{
            'id': str(m.organization.id),
            'name': m.organization.name,
            'subdomain': m.organization.subdomain,
            'logo_url': m.organization.logo_url,
            'is_active': m.organization.is_active
        } for m in obj.memberships.all()]


# ===============================
# MULTI-ORGANIZATION SERIALIZERS
# ===============================

class OrganizationMembershipSerializer(serializers.Serializer):
    """
    Serializer pour un membership d'organisation (employee multi-org).
    Retourne les détails de l'organisation + le membership.
    """
    id = serializers.UUIDField(source='organization.id', read_only=True)
    name = serializers.CharField(source='organization.name', read_only=True)
    subdomain = serializers.CharField(source='organization.subdomain', read_only=True)
    logo_url = serializers.URLField(source='organization.logo_url', read_only=True, allow_null=True)
    is_active = serializers.BooleanField(source='organization.is_active', read_only=True)
    is_primary = serializers.BooleanField(read_only=True)

    # Membership details
    employment_status = serializers.CharField(read_only=True)
    hire_date = serializers.DateField(read_only=True, allow_null=True)

    # Nested objects
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    assigned_role = serializers.SerializerMethodField()

    def get_department(self, obj):
        if obj.department:
            return {
                'id': str(obj.department.id),
                'name': obj.department.name
            }
        return None

    def get_position(self, obj):
        if obj.position:
            return {
                'id': str(obj.position.id),
                'title': obj.position.title
            }
        return None

    def get_assigned_role(self, obj):
        if obj.assigned_role:
            return {
                'id': str(obj.assigned_role.id),
                'code': obj.assigned_role.code,
                'name': obj.assigned_role.name
            }
        return None


class SelectOrganizationSerializer(serializers.Serializer):
    """
    Serializer pour sélectionner une organisation.
    Utilisé après login ou acceptation d'invitation.
    """
    organization_id = serializers.UUIDField(required=True)

    def validate_organization_id(self, value):
        """Valide que l'organisation existe et est active"""
        from core.models import Organization
        try:
            org = Organization.objects.get(id=value, is_active=True)
            return value
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organisation introuvable ou inactive")


class SwitchOrganizationSerializer(serializers.Serializer):
    """
    Serializer pour changer d'organisation en cours de session.
    Identique à SelectOrganizationSerializer mais utilisé dans un contexte différent.
    """
    organization_id = serializers.UUIDField(required=True)

    def validate_organization_id(self, value):
        """Valide que l'organisation existe et est active"""
        from core.models import Organization
        try:
            org = Organization.objects.get(id=value, is_active=True)
            return value
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organisation introuvable ou inactive")
