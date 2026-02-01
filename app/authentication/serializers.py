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
    Serializer unifié pour la connexion Admin et Employee.
    Recherche l'utilisateur dans BaseUser et détermine son type.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, data):
        email = data.get('email').lower().strip()
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError({
                'non_field_errors': 'Email et mot de passe sont requis'
            })

        # Rechercher dans BaseUser (parent de AdminUser et Employee)
        try:
            user = BaseUser.objects.get(email=email)
        except BaseUser.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'Identifiants invalides.'
            })

        # Vérifier le mot de passe
        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Identifiants invalides.'
            })

        # Vérifier si le compte est actif
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': 'Ce compte est désactivé.'
            })

        # Si c'est un Employee, vérifier l'organisation
        if user.user_type == 'employee':
            try:
                employee = user.employee
                if not employee.organization.is_active:
                    raise serializers.ValidationError({
                        'non_field_errors': "Votre organisation n'est pas active."
                    })
                data['user'] = employee
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    'non_field_errors': 'Compte employé invalide.'
                })
        else:
            # AdminUser
            try:
                data['user'] = user.adminuser
            except AdminUser.DoesNotExist:
                data['user'] = user

        data['user_type'] = user.user_type
        return data


class AdminRegistrationSerializer(serializers.Serializer):
    """
    Serializer pour l'inscription d'un Admin avec création d'organisation.
    Crée simultanément un AdminUser et son Organisation.
    """
    # Données Admin
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=True, max_length=100)
    last_name = serializers.CharField(required=True, max_length=100)
    phone = serializers.CharField(required=False, max_length=20, allow_blank=True)

 
    def validate_email(self, value):
        email = value.lower().strip()
        if BaseUser.objects.filter(email=email).exists():
            raise serializers.ValidationError('Cet email est déjà utilisé.')
        return email

    def create(self, validated_data):
        admin = AdminUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
        )

        return {
            'admin': admin,
        }


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer pour la réponse utilisateur après connexion"""
    
    class Meta:
        model = BaseUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'avatar_url', 'user_type', 'language', 'timezone',
            'is_active', 'email_verified', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields


class AdminUserResponseSerializer(UserResponseSerializer):
    """Serializer pour AdminUser avec ses organisations"""
    organizations = serializers.SerializerMethodField()

    class Meta(UserResponseSerializer.Meta):
        model = AdminUser
        fields = UserResponseSerializer.Meta.fields + ['organizations']

    def get_organizations(self, obj):
        return [{
            'id': str(org.id),
            'name': org.name,
            'subdomain': org.subdomain,
            'logo_url': org.logo_url,
            'is_active': org.is_active
        } for org in obj.organizations.all()]


class EmployeeUserResponseSerializer(UserResponseSerializer):
    """Serializer pour Employee avec son organisation"""
    organization = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta(UserResponseSerializer.Meta):
        model = Employee
        fields = UserResponseSerializer.Meta.fields + [
            'employee_id',
            'organization',
            'department',
            'position',
            'employment_status',
            'permissions',
            'date_of_birth',
            'address',
            'is_active',
            'city',
            'country',
            'emergency_contact',
            'contract',
            'hire_date',
            'termination_date',
            'manager',
        ]

    def get_organization(self, obj):
        return {
            'id': str(obj.organization.id),
            'name': obj.organization.name,
            'subdomain': obj.organization.subdomain,
            'logo_url': obj.organization.logo_url
        }

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

    def get_permissions(self, obj):
        """Retourne la liste des permissions de l'employé"""
        return list(obj.get_all_permissions().values_list('code', flat=True))
