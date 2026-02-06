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
    Crée une notification de façon asynchrone.

    Utilisée par send_notification() pour ne jamais bloquer
    la vue qui déclenche l'action métier.
    """
    from django.utils import timezone
    from core.models import BaseUser, Organization
    from .models import Notification, NotificationPreference

    try:
        organization = Organization.objects.get(id=organization_id)
        recipient = BaseUser.objects.get(id=recipient_id)
        sender = BaseUser.objects.get(id=sender_id) if sender_id else None

        # --- Vérification préférences (même logique que _should_deliver) ---
        try:
            pref = NotificationPreference.objects.get(
                organization=organization, user=recipient
            )
            # Filtrer par type
            type_map = {
                'alert': pref.receive_alerts,
                'system': pref.receive_system,
                'user': pref.receive_user,
            }
            if not type_map.get(notification_type, True):
                logger.debug("Notif filtrée par préférences type=%s", notification_type)
                return None

            # Filtrer par priorité min
            PRIORITY_ORDER = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            if PRIORITY_ORDER.get(priority, 0) < PRIORITY_ORDER.get(pref.min_priority, 0):
                logger.debug("Notif filtrée par priorité min=%s", pref.min_priority)
                return None
        except NotificationPreference.DoesNotExist:
            pass  # Pas de préfs → on livre

        # --- Créer la notification ---
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
