"""
Notifications — Celery Tasks
==============================
Tâches en background pour la création de notifications.

En dev (CELERY_TASK_ALWAYS_EAGER=True) ces tâches s'exécutent
synchronement — pas de worker nécessaire.
En production, elles sont poussées vers le broker.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def create_notification_task(
    self,
    organization_id: str,
    recipient_id: str,
    title: str,
    message: str,
    notification_type: str = 'system',
    priority: str = 'medium',
    sender_id: str | None = None,
    entity_type: str = '',
    entity_id: str = '',
    action_url: str = '',
):
    """
    Crée une notification de façon asynchrone et pousse en temps réel via SSE/WS.

    Utilisée par send_notification() pour ne jamais bloquer
    la vue qui déclenche l'action métier.
    """
    from core.models import BaseUser, Organization
    from .models import Notification
    from .notification_helpers import _should_deliver, _push_sse_notification

    try:
        organization = Organization.objects.get(id=organization_id)
        recipient = BaseUser.objects.get(id=recipient_id)
        sender = BaseUser.objects.get(id=sender_id) if sender_id else None

        # Vérification préférences (réutiliser la logique centralisée)
        if not _should_deliver(organization, recipient, notification_type, priority):
            logger.debug("Notif filtrée par préférences type=%s priority=%s", notification_type, priority)
            return None

        # Créer la notification
        notification = Notification.objects.create(
            organization=organization,
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
        )

        # Push en temps réel
        _push_sse_notification(notification)

        logger.info(
            "Notification créée (task) id=%s recipient=%s type=%s",
            notification.id, recipient_id, notification_type
        )
        return str(notification.id)

    except (Organization.DoesNotExist, BaseUser.DoesNotExist) as exc:
        logger.error("Entité introuvable dans create_notification_task : %s", exc)
        raise self.retry(exc=exc, countdown=5)
    except Exception as exc:
        logger.error("Erreur create_notification_task : %s", exc)
        raise self.retry(exc=exc, countdown=10)


@shared_task
def purge_old_notifications_task(organization_id: str | None = None, days: int = 30):
    """
    Tâche périodique pour nettoyer les vieilles notifications.
    Peut être appelée pour une org spécifique ou pour toutes.
    """
    from django.utils import timezone
    from core.models import Organization
    from .models import Notification

    cutoff = timezone.now() - timezone.timedelta(days=days)
    qs = Notification.objects.filter(is_read=True, read_at__lt=cutoff)

    if organization_id:
        try:
            org = Organization.objects.get(id=organization_id)
            qs = qs.filter(organization=org)
        except Organization.DoesNotExist:
            logger.warning("Organisation %s introuvable pour purge", organization_id)
            return 0

    count, _ = qs.delete()
    logger.info("Purge notifications : %d supprimées (days=%d)", count, days)
    return count
