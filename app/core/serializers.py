from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import AdminUser, Organization, Category, OrganizationSettings


# -------------------------------
# Authentication Serializers
# -------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = AdminUser
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        """Validate that passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password': 'Les mots de passe ne correspondent pas'
            })
        return data

    def create(self, validated_data):
        """Create a new user"""
        validated_data.pop('password_confirm')
        user = AdminUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, data):
        """Validate and authenticate user"""
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Email ou mot de passe incorrect',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'Ce compte est desactive',
                    code='authorization'
                )

            data['user'] = user
            return data
        else:
            raise serializers.ValidationError(
                'Email et mot de passe sont requis',
                code='authorization'
            )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    organizations_count = serializers.SerializerMethodField()

    class Meta:
        model = AdminUser
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'is_active', 'created_at', 'organizations_count'
        ]
        read_only_fields = ['id', 'created_at']

    def get_organizations_count(self, obj):
        """Return the number of organizations managed by this user"""
        return obj.organizations.count()


# -------------------------------
# Organization Serializers
# -------------------------------

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for category"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for organization settings"""
    class Meta:
        model = OrganizationSettings
        fields = ['country', 'currency', 'theme', 'contact_email']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization"""
    settings = OrganizationSettingsSerializer(read_only=True)
    category_details = CategorySerializer(source='category', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'subdomain', 'logo_url', 'category',
            'category_details', 'admin', 'admin_email', 'is_active',
            'created_at', 'updated_at', 'settings'
        ]
        read_only_fields = ['id', 'admin', 'created_at', 'updated_at']

    def validate_subdomain(self, value):
        """Validate subdomain uniqueness and format"""
        if not value.isalnum() and '-' not in value:
            raise serializers.ValidationError(
                'Le sous-domaine ne peut contenir que des lettres, chiffres et tirets'
            )
        return value.lower()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an organization"""
    settings = OrganizationSettingsSerializer(required=False)

    class Meta:
        model = Organization
        fields = ['name', 'subdomain', 'logo_url', 'category', 'settings']

    def validate_subdomain(self, value):
        """Validate subdomain format"""
        if not value.replace('-', '').isalnum():
            raise serializers.ValidationError(
                'Le sous-domaine ne peut contenir que des lettres, chiffres et tirets'
            )
        return value.lower()

    def create(self, validated_data):
        """Create organization with settings"""
        settings_data = validated_data.pop('settings', {})

        # Admin is set from the request context
        organization = Organization.objects.create(**validated_data)

        # Create settings if provided
        if settings_data:
            OrganizationSettings.objects.create(
                organization=organization,
                **settings_data
            )

        return organization
