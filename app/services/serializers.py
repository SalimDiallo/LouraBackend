"""
Serializers for Services Module API
"""

from rest_framework import serializers
from django.db import transaction
from .models import (
    BusinessProfile,
    ServiceType,
    ServiceField,
    ServiceStatus,
    Service,
    ServiceStatusHistory,
    ServiceActivity,
    ServiceComment,
    ServiceTemplate
)
from core.models import BaseUser


# ===============================
# Business Profile Serializers
# ===============================

class BusinessProfileSerializer(serializers.ModelSerializer):
    """Serializer for BusinessProfile"""

    service_types_count = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'organization', 'name', 'code', 'description',
            'icon', 'color', 'is_active', 'settings',
            'service_types_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_service_types_count(self, obj):
        return obj.service_types.filter(is_active=True).count()


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing business profiles"""

    class Meta:
        model = BusinessProfile
        fields = ['id', 'name', 'code', 'icon', 'color', 'is_active']


# ===============================
# Service Field Serializers
# ===============================

class ServiceFieldSerializer(serializers.ModelSerializer):
    """Serializer for ServiceField"""

    class Meta:
        model = ServiceField
        fields = [
            'id', 'service_type', 'name', 'field_key', 'field_type',
            'description', 'is_required', 'is_unique', 'is_searchable',
            'is_visible_in_list', 'order', 'default_value',
            'validation_rules', 'options', 'settings', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceFieldListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing service fields"""

    class Meta:
        model = ServiceField
        fields = [
            'id', 'name', 'field_key', 'field_type',
            'is_required', 'is_visible_in_list', 'order'
        ]


# ===============================
# Service Status Serializers
# ===============================

class ServiceStatusSerializer(serializers.ModelSerializer):
    """Serializer for ServiceStatus"""

    allowed_next_statuses_data = serializers.SerializerMethodField()

    class Meta:
        model = ServiceStatus
        fields = [
            'id', 'service_type', 'name', 'code', 'description',
            'color', 'icon', 'order', 'status_type', 'is_initial',
            'is_final', 'requires_comment', 'allowed_next_statuses',
            'allowed_next_statuses_data', 'required_permission',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_allowed_next_statuses_data(self, obj):
        return ServiceStatusListSerializer(
            obj.allowed_next_statuses.filter(is_active=True),
            many=True
        ).data


class ServiceStatusListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing service statuses"""

    class Meta:
        model = ServiceStatus
        fields = ['id', 'name', 'code', 'color', 'icon', 'status_type']


# ===============================
# Service Type Serializers
# ===============================

class ServiceTypeSerializer(serializers.ModelSerializer):
    """Serializer for ServiceType"""

    business_profile_data = BusinessProfileListSerializer(
        source='business_profile',
        read_only=True
    )
    fields_data = ServiceFieldListSerializer(
        source='fields',
        many=True,
        read_only=True
    )
    statuses_data = ServiceStatusListSerializer(
        source='statuses',
        many=True,
        read_only=True
    )
    initial_status = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceType
        fields = [
            'id', 'business_profile', 'business_profile_data',
            'name', 'code', 'description', 'icon', 'color',
            'requires_approval', 'allow_nested_services',
            'allowed_child_types', 'has_pricing', 'pricing_model',
            'default_values', 'settings', 'is_active',
            'fields_data', 'statuses_data', 'initial_status',
            'services_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_initial_status(self, obj):
        status = obj.statuses.filter(is_initial=True, is_active=True).first()
        return ServiceStatusListSerializer(status).data if status else None

    def get_services_count(self, obj):
        return obj.services.filter(is_archived=False).count()


class ServiceTypeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing service types"""

    business_profile_name = serializers.CharField(
        source='business_profile.name',
        read_only=True
    )

    class Meta:
        model = ServiceType
        fields = [
            'id', 'name', 'code', 'icon', 'color',
            'business_profile_name', 'allow_nested_services'
        ]


# ===============================
# Service Template Serializers
# ===============================

class ServiceTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ServiceTemplate"""

    service_type_data = ServiceTypeListSerializer(
        source='service_type',
        read_only=True
    )

    class Meta:
        model = ServiceTemplate
        fields = [
            'id', 'service_type', 'service_type_data',
            'name', 'description', 'default_field_values',
            'default_title_template', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===============================
# Service Activity Serializers
# ===============================

class ServiceActivitySerializer(serializers.ModelSerializer):
    """Serializer for ServiceActivity"""

    user_data = serializers.SerializerMethodField()

    class Meta:
        model = ServiceActivity
        fields = [
            'id', 'service', 'activity_type', 'user', 'user_data',
            'title', 'description', 'data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_user_data(self, obj):
        if obj.user:
            return {
                'id': str(obj.user.id),
                'name': obj.user.get_full_name(),
                'email': obj.user.email
            }
        return None


# ===============================
# Service Comment Serializers
# ===============================

class ServiceCommentSerializer(serializers.ModelSerializer):
    """Serializer for ServiceComment"""

    user_data = serializers.SerializerMethodField()
    replies_data = serializers.SerializerMethodField()

    class Meta:
        model = ServiceComment
        fields = [
            'id', 'service', 'user', 'user_data', 'content',
            'parent_comment', 'attachments', 'is_internal',
            'replies_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_data(self, obj):
        if obj.user:
            return {
                'id': str(obj.user.id),
                'name': obj.user.get_full_name(),
                'email': obj.user.email
            }
        return None

    def get_replies_data(self, obj):
        if obj.parent_comment is None:
            replies = obj.replies.all().order_by('created_at')
            return ServiceCommentSerializer(replies, many=True, context=self.context).data
        return []


# ===============================
# Service Status History Serializers
# ===============================

class ServiceStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for ServiceStatusHistory"""

    from_status_data = ServiceStatusListSerializer(
        source='from_status',
        read_only=True
    )
    to_status_data = ServiceStatusListSerializer(
        source='to_status',
        read_only=True
    )
    changed_by_data = serializers.SerializerMethodField()

    class Meta:
        model = ServiceStatusHistory
        fields = [
            'id', 'service', 'from_status', 'from_status_data',
            'to_status', 'to_status_data', 'changed_by',
            'changed_by_data', 'comment', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_changed_by_data(self, obj):
        if obj.changed_by:
            return {
                'id': str(obj.changed_by.id),
                'name': obj.changed_by.get_full_name(),
                'email': obj.changed_by.email
            }
        return None


# ===============================
# Service Serializers
# ===============================

class ServiceSerializer(serializers.ModelSerializer):
    """Full serializer for Service"""

    service_type_data = ServiceTypeListSerializer(
        source='service_type',
        read_only=True
    )
    current_status_data = ServiceStatusListSerializer(
        source='current_status',
        read_only=True
    )
    assigned_to_data = serializers.SerializerMethodField()
    client_user_data = serializers.SerializerMethodField()
    parent_service_data = serializers.SerializerMethodField()
    child_services_data = serializers.SerializerMethodField()
    status_history_data = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'organization', 'service_type', 'service_type_data',
            'reference', 'title', 'description', 'client_type',
            'client_name', 'client_email', 'client_phone',
            'client_user', 'client_user_data', 'assigned_to',
            'assigned_to_data', 'parent_service', 'parent_service_data',
            'child_services_data', 'current_status', 'current_status_data',
            'field_values', 'start_date', 'end_date', 'completed_at',
            'estimated_amount', 'actual_amount', 'currency', 'priority',
            'tags', 'metadata', 'attachments', 'is_archived',
            'status_history_data', 'comments_count', 'activities_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_assigned_to_data(self, obj):
        if obj.assigned_to:
            return {
                'id': str(obj.assigned_to.id),
                'name': obj.assigned_to.get_full_name(),
                'email': obj.assigned_to.email
            }
        return None

    def get_client_user_data(self, obj):
        if obj.client_user:
            return {
                'id': str(obj.client_user.id),
                'name': obj.client_user.get_full_name(),
                'email': obj.client_user.email
            }
        return None

    def get_parent_service_data(self, obj):
        if obj.parent_service:
            return {
                'id': str(obj.parent_service.id),
                'reference': obj.parent_service.reference,
                'title': obj.parent_service.title
            }
        return None

    def get_child_services_data(self, obj):
        children = obj.child_services.filter(is_archived=False)
        return ServiceListSerializer(children, many=True, context=self.context).data

    def get_status_history_data(self, obj):
        history = obj.status_history.all().order_by('-created_at')[:10]
        return ServiceStatusHistorySerializer(history, many=True, context=self.context).data

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_activities_count(self, obj):
        return obj.activities.count()


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing services"""

    service_type_name = serializers.CharField(
        source='service_type.name',
        read_only=True
    )
    current_status_data = ServiceStatusListSerializer(
        source='current_status',
        read_only=True
    )
    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Service
        fields = [
            'id', 'reference', 'title', 'service_type_name',
            'client_name', 'current_status_data', 'assigned_to_name',
            'priority', 'start_date', 'estimated_amount', 'currency',
            'is_archived', 'created_at'
        ]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating services"""

    class Meta:
        model = Service
        fields = [
            'organization', 'service_type', 'title', 'description',
            'client_type', 'client_name', 'client_email', 'client_phone',
            'client_user', 'assigned_to', 'parent_service', 'current_status',
            'field_values', 'start_date', 'end_date', 'estimated_amount',
            'actual_amount', 'currency', 'priority', 'tags', 'metadata'
        ]

    def validate(self, data):
        """Validate service creation data"""

        # Vérifier que le statut appartient au bon service type
        if 'current_status' in data and 'service_type' in data:
            if data['current_status'].service_type != data['service_type']:
                raise serializers.ValidationError({
                    'current_status': 'Le statut doit appartenir au type de service sélectionné.'
                })

        # Si le statut n'est pas fourni, utiliser le statut initial
        if 'current_status' not in data and 'service_type' in data:
            initial_status = data['service_type'].statuses.filter(
                is_initial=True,
                is_active=True
            ).first()

            if initial_status:
                data['current_status'] = initial_status
            else:
                raise serializers.ValidationError({
                    'current_status': 'Aucun statut initial défini pour ce type de service.'
                })

        # Vérifier les champs requis
        if 'service_type' in data and 'field_values' in data:
            service_type = data['service_type']
            field_values = data['field_values']

            required_fields = service_type.fields.filter(
                is_required=True,
                is_active=True
            )

            for field in required_fields:
                if field.field_key not in field_values or not field_values[field.field_key]:
                    raise serializers.ValidationError({
                        'field_values': f'Le champ "{field.name}" est obligatoire.'
                    })

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create service and log activity"""
        service = Service.objects.create(**validated_data)

        # Créer une activité
        user = self.context.get('request').user if self.context.get('request') else None
        ServiceActivity.objects.create(
            service=service,
            activity_type='created',
            user=user,
            title=f'Service créé: {service.reference}',
            description=f'Le service "{service.title}" a été créé.',
            data={'initial_status': service.current_status.code}
        )

        return service


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating services"""

    class Meta:
        model = Service
        fields = [
            'title', 'description', 'client_type', 'client_name',
            'client_email', 'client_phone', 'client_user', 'assigned_to',
            'field_values', 'start_date', 'end_date', 'completed_at',
            'estimated_amount', 'actual_amount', 'priority', 'tags',
            'metadata', 'attachments', 'is_archived'
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update service and log changes"""

        # Détecter les changements
        changes = {}
        for field, value in validated_data.items():
            old_value = getattr(instance, field)
            if old_value != value:
                changes[field] = {'old': old_value, 'new': value}

        # Mettre à jour l'instance
        service = super().update(instance, validated_data)

        # Logger l'activité si des changements ont été faits
        if changes:
            user = self.context.get('request').user if self.context.get('request') else None
            ServiceActivity.objects.create(
                service=service,
                activity_type='updated',
                user=user,
                title=f'Service modifié: {service.reference}',
                description=f'{len(changes)} champ(s) modifié(s).',
                data={'changes': changes}
            )

        return service


class ServiceStatusChangeSerializer(serializers.Serializer):
    """Serializer for changing service status"""

    new_status_id = serializers.UUIDField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate status change"""
        service = self.context['service']

        try:
            new_status = ServiceStatus.objects.get(id=data['new_status_id'])
        except ServiceStatus.DoesNotExist:
            raise serializers.ValidationError({
                'new_status_id': 'Statut introuvable.'
            })

        # Vérifier que le statut appartient au bon service type
        if new_status.service_type != service.service_type:
            raise serializers.ValidationError({
                'new_status_id': 'Le statut doit appartenir au type de service.'
            })

        # Vérifier les transitions autorisées
        current_status = service.current_status
        allowed_next = current_status.allowed_next_statuses.filter(is_active=True)

        if allowed_next.exists() and new_status not in allowed_next.all():
            raise serializers.ValidationError({
                'new_status_id': f'Transition non autorisée depuis "{current_status.name}".'
            })

        # Vérifier si un commentaire est requis
        if new_status.requires_comment and not data.get('comment'):
            raise serializers.ValidationError({
                'comment': 'Un commentaire est requis pour ce statut.'
            })

        data['new_status'] = new_status
        return data

    @transaction.atomic
    def save(self):
        """Apply status change"""
        service = self.context['service']
        new_status = self.validated_data['new_status']
        comment = self.validated_data.get('comment', '')
        user = self.context.get('request').user if self.context.get('request') else None

        old_status = service.current_status
        service.current_status = new_status

        # Marquer comme complété si statut final
        if new_status.is_final and new_status.status_type == 'completed':
            from django.utils import timezone
            service.completed_at = timezone.now()

        service.save()

        # Créer l'historique
        ServiceStatusHistory.objects.create(
            service=service,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            comment=comment
        )

        # Logger l'activité
        ServiceActivity.objects.create(
            service=service,
            activity_type='status_changed',
            user=user,
            title=f'Statut changé: {old_status.name} → {new_status.name}',
            description=comment,
            data={
                'from_status': old_status.code,
                'to_status': new_status.code
            }
        )

        return service
