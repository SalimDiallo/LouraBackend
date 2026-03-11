"""
Helpers pour envoyer des notifications via WebSocket
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer


def send_notification_to_user(notification):
    """
    Envoyer une notification en temps réel via WebSocket

    Args:
        notification: Instance du modèle Notification
    """
    channel_layer = get_channel_layer()

    if not channel_layer:
        return

    # Sérialiser la notification
    serializer = NotificationSerializer(notification)
    notification_data = serializer.data

    # Envoyer au groupe de l'utilisateur
    room_group_name = f'notifications_{notification.recipient.id}'

    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


def send_unread_count_to_user(user_id, count):
    """
    Envoyer une mise à jour du compteur de notifications non lues

    Args:
        user_id: ID de l'utilisateur
        count: Nombre de notifications non lues
    """
    channel_layer = get_channel_layer()

    if not channel_layer:
        return

    room_group_name = f'notifications_{user_id}'

    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'unread_count_update',
            'count': count
        }
    )
