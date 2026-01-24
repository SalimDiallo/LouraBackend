from rest_framework import serializers
from .models import AdminUser, Organization, Category, OrganizationSettings


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
        fields = ['country', 'currency', 'contact_email', ]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for organization"""
    settings = OrganizationSettingsSerializer(read_only=True)
    category_details = CategorySerializer(source='category', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'subdomain', 'logo_url', 'logo', 'category',
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
        fields = ['name', 'subdomain', 'logo_url', 'logo', 'category', 'settings']

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
