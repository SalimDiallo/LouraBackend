from rest_framework import serializers
from .models import AdminUser, Organization, Category, OrganizationSettings, Module, OrganizationModule


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
    settings = OrganizationSettingsSerializer()
    category_details = CategorySerializer(source='category', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    modules = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'subdomain', 'logo_url', 'logo', 'category',
            'category_details', 'admin', 'admin_email', 'is_active',
            'created_at', 'updated_at', 'settings', 'modules'
        ]
        read_only_fields = ['id', 'admin', 'created_at', 'updated_at']

    def get_modules(self, obj):
        """Return enabled modules for this organization"""
        org_modules = obj.organization_modules.filter(is_enabled=True).select_related('module')
        return OrganizationModuleSerializer(org_modules, many=True).data

    def validate_subdomain(self, value):
        """Validate subdomain uniqueness and format"""
        if not value.isalnum() and '-' not in value:
            raise serializers.ValidationError(
                'Le sous-domaine ne peut contenir que des lettres, chiffres et tirets'
            )
        return value.lower()


# -------------------------------
# Module Serializers
# -------------------------------

class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for module"""
    class Meta:
        model = Module
        fields = [
            'id', 'code', 'name', 'description', 'app_name', 'icon',
            'category', 'default_for_all', 'default_categories',
            'requires_subscription_tier', 'depends_on', 'is_core',
            'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationModuleSerializer(serializers.ModelSerializer):
    """Serializer for organization module relationship"""
    module_details = ModuleSerializer(source='module', read_only=True)

    class Meta:
        model = OrganizationModule
        fields = [
            'id', 'module', 'module_details', 'is_enabled',
            'settings', 'enabled_at', 'enabled_by'
        ]
        read_only_fields = ['id', 'enabled_at', 'enabled_by']


class OrganizationModuleCreateSerializer(serializers.Serializer):
    """Serializer for adding modules during organization creation"""
    module_code = serializers.CharField(max_length=100)
    is_enabled = serializers.BooleanField(default=True)
    settings = serializers.JSONField(required=False, default=dict)


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an organization"""
    settings = OrganizationSettingsSerializer(required=False)
    modules = OrganizationModuleCreateSerializer(many=True, required=False)

    class Meta:
        model = Organization
        fields = ['name', 'subdomain', 'logo_url', 'logo', 'category', 'settings', 'modules']

    def validate_subdomain(self, value):
        """Validate subdomain format"""
        if not value.replace('-', '').isalnum():
            raise serializers.ValidationError(
                'Le sous-domaine ne peut contenir que des lettres, chiffres et tirets'
            )
        return value.lower()

    def validate_modules(self, value):
        """Validate that all module codes exist"""
        if not value:
            return value

        module_codes = [m['module_code'] for m in value]
        existing_modules = Module.objects.filter(code__in=module_codes, is_active=True)
        existing_codes = set(existing_modules.values_list('code', flat=True))

        invalid_codes = set(module_codes) - existing_codes
        if invalid_codes:
            raise serializers.ValidationError(
                f"Modules invalides ou inactifs: {', '.join(invalid_codes)}"
            )

        return value

    def create(self, validated_data):
        """Create organization with settings and modules"""
        settings_data = validated_data.pop('settings', {})
        modules_data = validated_data.pop('modules', [])

        # Admin is set from the request context
        organization = Organization.objects.create(**validated_data)

        # Create settings if provided
        if settings_data:
            OrganizationSettings.objects.create(
                organization=organization,
                **settings_data
            )

        # Create organization modules
        if modules_data:
            admin_user = self.context.get('request').user if self.context.get('request') else None
            for module_data in modules_data:
                module_code = module_data.pop('module_code')
                try:
                    module = Module.objects.get(code=module_code, is_active=True)
                    OrganizationModule.objects.create(
                        organization=organization,
                        module=module,
                        enabled_by=admin_user,
                        **module_data
                    )
                except Module.DoesNotExist:
                    pass  # Already validated, should not happen

        # If no modules provided, activate default modules based on category
        elif organization.category:
            self._activate_default_modules(organization)

        return organization

    def _activate_default_modules(self, organization):
        """Activate default modules based on organization category"""
        from core.modules import ModuleRegistry

        category_name = organization.category.name
        default_module_defs = ModuleRegistry.get_default_modules_for_category(category_name)

        admin_user = self.context.get('request').user if self.context.get('request') else None

        for module_def in default_module_defs:
            try:
                module = Module.objects.get(code=module_def.code, is_active=True)
                OrganizationModule.objects.get_or_create(
                    organization=organization,
                    module=module,
                    defaults={
                        'is_enabled': True,
                        'enabled_by': admin_user
                    }
                )
            except Module.DoesNotExist:
                pass  # Module not yet in database
