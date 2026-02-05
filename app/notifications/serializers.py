"""
Notifications — Serializers
============================
Sérialiseurs pour Notification et NotificationPreference.

On réutilise le même pattern UUIDSerializerMixin utilisé par le module inventory
pour garantir la cohérence de l'API (UUIDs en string, champs relationnels
lisibles en lecture, validations en écriture).
"""

from rest_framework import serializers

from .models import Notification, NotificationPreference


# ---------------------------------------------------------------------------
# Notification — Lecture (list / detail)
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur principal pour la lecture d'une notification.

    Expose les UUIDs en string et ajoute des champs lisibles pour les FK.
    """

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'organization',
            'recipient',
            'sender',
            'sender_name',
            'notification_type',
            'priority',
            'title',
            'message',
            'entity_type',
            'entity_id',
            'action_url',
            'is_read',
            'read_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'organization', 'recipient', 'sender',
            'created_at', 'updated_at',
        ]

    # --- SerializerMethodFields (UUID → string) ----------------------------
    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization_id) if obj.organization_id else None

    def get_recipient(self, obj):
        return str(obj.recipient_id) if obj.recipient_id else None

    def get_sender(self, obj):
        return str(obj.sender_id) if obj.sender_id else None

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.get_full_name()
        return None


# ---------------------------------------------------------------------------
# Notification — Création (POST)
# ---------------------------------------------------------------------------

class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une notification via l'API.

    `organization` et `recipient` sont injectés automatiquement par le ViewSet
    donc ils ne sont pas exposés en écriture ici.
    """

    class Meta:
        model = Notification
        fields = [
            'notification_type',
            'priority',
            'title',
            'message',
            'entity_type',
            'entity_id',
            'action_url',
        ]

    # Validation des choix
    def validate_notification_type(self, value):
        valid = [c[0] for c in Notification.TYPE_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"Type invalide. Choisissez parmi : {', '.join(valid)}"
            )
        return value

    def validate_priority(self, value):
        valid = [c[0] for c in Notification.PRIORITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"Priorité invalide. Choisissez parmi : {', '.join(valid)}"
            )
        return value


# ---------------------------------------------------------------------------
# NotificationPreference — Lecture + Mise à jour
# ---------------------------------------------------------------------------

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les préférences de notification."""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'organization',
            'user',
            'receive_alerts',
            'receive_system',
            'receive_user',
            'min_priority',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organization', 'user', 'created_at', 'updated_at']

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization_id) if obj.organization_id else None

    def get_user(self, obj):
        return str(obj.user_id) if obj.user_id else None


class NotificationPreferenceUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour des préférences (PATCH)."""

    class Meta:
        model = NotificationPreference
        fields = [
            'receive_alerts',
            'receive_system',
            'receive_user',
            'min_priority',
        ]

    def validate_min_priority(self, value):
        valid = [c[0] for c in NotificationPreference.PRIORITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f"Priorité invalide. Choisissez parmi : {', '.join(valid)}"
            )
        return value
