"""
Notification Helpers
====================
Fonctions utilitaires pour créer, envoyer et gérer les notifications.

Intégration Novu :
    Chaque envoi de notification déclenche également un workflow Novu
    (si NOVU_ENABLED=True) pour la livraison multi-canal (email, SMS, push).
    Le canal in-app local reste actif indépendamment de Novu.

Usage typique :
    from notifications.notification_helpers import send_notification, send_alert_notification

    # Notification générique
    send_notification(
        organization=org,
        recipient=user,
        title="Bienvenue",
        message="Vous êtes désormais membre de l'organisation.",
        notification_type='system',
        priority='low',
    )

    # Notification d'alerte de stock (intégré avec le module inventory)
    send_alert_notification(
        organization=org,
        product=product,
        alert_type='low_stock',
        severity='high',
    )
"""

import json
import logging
from typing import Optional

from django.utils import timezone

from core.models import BaseUser, Organization
from .models import Notification, NotificationPreference


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mappage priorité → ordre numérique
# ---------------------------------------------------------------------------
PRIORITY_ORDER = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}


# ---------------------------------------------------------------------------
# Interne : vérification des préférences
# ---------------------------------------------------------------------------

def _should_deliver(
    organization: Organization,
    recipient: BaseUser,
    notification_type: str,
    priority: str,
) -> bool:
    """
    Vérifie si la notification doit être livrée selon les préférences du destinataire.

    Si aucune préférence n'existe → livraison par défaut (True).
    """
    try:
        pref = NotificationPreference.objects.get(
            organization=organization,
            user=recipient,
        )
    except NotificationPreference.DoesNotExist:
        return True

    # Filtrer par type
    type_map = {
        'alert': pref.receive_alerts,
        'system': pref.receive_system,
        'user': pref.receive_user,
    }
    if not type_map.get(notification_type, True):
        return False

    # Filtrer par priorité minimale
    if PRIORITY_ORDER.get(priority, 0) < PRIORITY_ORDER.get(pref.min_priority, 0):
        return False

    return True


# ---------------------------------------------------------------------------
# Push SSE en temps réel
# ---------------------------------------------------------------------------

def _push_sse_notification(notification: Notification):
    """
    Envoie un événement SSE en temps réel via le système de broadcast.
    Publie sur Redis (ou in-memory) pour que le SSE generator le capte.
    """
    try:
        from .websocket_helpers import send_notification_to_user, send_unread_count_to_user
        send_notification_to_user(notification)

        # Envoyer aussi le compteur mis à jour
        unread = Notification.objects.filter(
            organization=notification.organization,
            recipient=notification.recipient,
            is_read=False,
        ).count()
        send_unread_count_to_user(str(notification.recipient_id), unread)
    except Exception as e:
        logger.warning("Échec push SSE: %s", e)


def _push_sse_unread_update(organization: Organization, user: BaseUser):
    """
    Envoie une mise à jour du compteur non lu via SSE/WebSocket.
    """
    try:
        from .websocket_helpers import send_unread_count_to_user
        unread = Notification.objects.filter(
            organization=organization,
            recipient=user,
            is_read=False,
        ).count()
        send_unread_count_to_user(str(user.id), unread)
    except Exception as e:
        logger.warning("Échec push SSE unread: %s", e)


# ---------------------------------------------------------------------------
# Novu — dispatch multi-canal
# ---------------------------------------------------------------------------

def _trigger_novu(
    workflow_id: str,
    recipient: BaseUser,
    payload: dict,
    organization: Optional[Organization] = None,
):
    """
    Déclenche un workflow Novu en background (via Celery).

    Fail-safe : ne lève jamais d'exception, le canal in-app local
    fonctionne indépendamment.
    """
    try:
        from .novu_tasks import novu_trigger_workflow_task

        tenant_id = str(organization.id) if organization else None

        novu_trigger_workflow_task.delay(
            workflow_id=workflow_id,
            subscriber_id=str(recipient.id),
            payload=payload,
            tenant_id=tenant_id,
        )
    except Exception as e:
        logger.debug("Novu trigger ignoré (%s) : %s", workflow_id, e)


# Mapping notification_type → workflow Novu
_NOVU_WORKFLOW_MAP = {
    'alert': 'stock-alert',
    'system': 'system-announcement',
    'user': 'user-action',
}


# ---------------------------------------------------------------------------
# Création de notification de base
# ---------------------------------------------------------------------------

def send_notification(
    organization: Organization,
    recipient: BaseUser,
    title: str,
    message: str,
    notification_type: str = 'system',
    priority: str = 'medium',
    sender: Optional[BaseUser] = None,
    entity_type: str = '',
    entity_id: str = '',
    action_url: str = '',
) -> Optional[Notification]:
    """
    Crée une notification en vérifiant les préférences du destinataire.

    Retourne l'instance Notification créée, ou None si filtrée par les préférences.

    Déclenche également un workflow Novu pour la livraison multi-canal
    (email, SMS, push) si NOVU_ENABLED=True.
    """
    # Vérification des préférences
    if not _should_deliver(organization, recipient, notification_type, priority):
        logger.debug(
            "Notification filtrée par préférences : recipient=%s, type=%s, priority=%s",
            recipient.id, notification_type, priority
        )
        return None

    # --- Canal Novu (multi-canal : email, SMS, push) ----------------------
    novu_workflow = _NOVU_WORKFLOW_MAP.get(notification_type)
    if novu_workflow:
        _trigger_novu(
            workflow_id=novu_workflow,
            recipient=recipient,
            payload={
                'title': title,
                'message': message,
                'priority': priority,
                'entity_type': entity_type,
                'entity_id': str(entity_id) if entity_id else '',
                'action_url': action_url,
                'organization_name': organization.name if organization else '',
                'sender_name': sender.get_full_name() if sender else '',
            },
            organization=organization,
        )

    # --- Canal in-app local (existant) ------------------------------------
    # Dispatch via Celery (ou sync si ALWAYS_EAGER)
    from .tasks import create_notification_task

    try:
        create_notification_task.delay(
            organization_id=str(organization.id),
            recipient_id=str(recipient.id),
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            sender_id=str(sender.id) if sender else None,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else '',
            action_url=action_url,
        )
        logger.info(
            "Notification dispatchée (Celery) : recipient=%s, type=%s, priority=%s",
            recipient.id, notification_type, priority
        )
    except Exception as exc:
        # Fallback synchrone
        logger.warning("Celery dispatch échoué, création synchrone : %s", exc)
        notification = Notification.objects.create(
            organization=organization,
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else '',
            action_url=action_url,
        )
        # Push en temps réel
        _push_sse_notification(notification)
        return notification

    # En mode eager la tâche s'exécute sync
    try:
        return Notification.objects.filter(
            organization=organization,
            recipient=recipient,
            title=title,
            message=message,
        ).order_by('-created_at').first()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Raccourcis pour les notifications d'alerte (inventaire)
# ---------------------------------------------------------------------------

def send_alert_notification(
    organization: Organization,
    product,
    alert_type: str,
    severity: str,
    message: Optional[str] = None,
    warehouse=None,
) -> list:
    """
    Envoie une notification d'alerte à tous les administrateurs de l'organisation.

    Déclenche aussi le workflow Novu 'stock-alert' pour chaque admin.
    """
    TITLE_MAP = {
        'low_stock': 'Stock bas',
        'out_of_stock': 'Rupture de stock',
        'overstock': 'Surstock',
        'expiring_soon': 'Expiration proche',
    }
    title = TITLE_MAP.get(alert_type, 'Alerte stock')

    if not message:
        loc = f" à {warehouse.name}" if warehouse else ""
        message = f"{title} : {product.name}{loc} ({product.sku})"

    admin_users = BaseUser.objects.filter(
        user_type='admin',
        adminuser__organizations=organization,
        is_active=True,
    )

    created = []
    for user in admin_users:
        # --- Novu multi-canal avec payload enrichi pour le template ---
        from django.db.models import Sum
        current_stock = 0
        threshold = 0
        try:
            total = product.stocks.aggregate(total=Sum('quantity'))['total']
            current_stock = float(total) if total else 0
            threshold = float(product.min_stock_level) if product.min_stock_level else 0
        except Exception:
            pass

        _trigger_novu(
            workflow_id='stock-alert',
            recipient=user,
            payload={
                'product_name': product.name,
                'product_sku': getattr(product, 'sku', ''),
                'alert_type': alert_type,
                'severity': severity,
                'current_stock': current_stock,
                'threshold': threshold,
                'warehouse_name': warehouse.name if warehouse else '',
                'organization_name': organization.name,
                'title': title,
                'message': message,
            },
            organization=organization,
        )

        # --- Canal in-app local ---
        notif = send_notification(
            organization=organization,
            recipient=user,
            title=title,
            message=message,
            notification_type='alert',
            priority=severity,
            entity_type='product',
            entity_id=str(product.id),
        )
        if notif:
            created.append(notif)

    return created


# ---------------------------------------------------------------------------
# Raccourcis : notification système
# ---------------------------------------------------------------------------

def send_system_notification(
    organization: Organization,
    recipient: BaseUser,
    title: str,
    message: str,
    priority: str = 'low',
) -> Optional[Notification]:
    """Raccourci pour envoyer une notification de type système."""
    return send_notification(
        organization=organization,
        recipient=recipient,
        title=title,
        message=message,
        notification_type='system',
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Raccourcis : notification entre utilisateurs
# ---------------------------------------------------------------------------

def send_user_notification(
    organization: Organization,
    recipient: BaseUser,
    sender: BaseUser,
    title: str,
    message: str,
    priority: str = 'medium',
    entity_type: str = '',
    entity_id: str = '',
    action_url: str = '',
) -> Optional[Notification]:
    """Raccourci pour envoyer une notification d'un utilisateur à un autre."""
    return send_notification(
        organization=organization,
        recipient=recipient,
        sender=sender,
        title=title,
        message=message,
        notification_type='user',
        priority=priority,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
    )


# ---------------------------------------------------------------------------
# Lecture en masse
# ---------------------------------------------------------------------------

def mark_all_as_read(organization: Organization, user: BaseUser) -> int:
    """
    Marque toutes les notifications non lues d'un utilisateur comme lues.
    Pousse la mise à jour du compteur en temps réel.
    """
    now = timezone.now()
    count = Notification.objects.filter(
        organization=organization,
        recipient=user,
        is_read=False,
    ).update(is_read=True, read_at=now)

    # Push mise à jour en temps réel
    _push_sse_unread_update(organization, user)

    return count


# ---------------------------------------------------------------------------
# Compteur non lus
# ---------------------------------------------------------------------------

def get_unread_count(organization: Organization, user: BaseUser) -> int:
    """Retourne le nombre de notifications non lues pour un utilisateur."""
    return Notification.objects.filter(
        organization=organization,
        recipient=user,
        is_read=False,
    ).count()


# ---------------------------------------------------------------------------
# Nettoyage (purge anciennes notifications)
# ---------------------------------------------------------------------------

def purge_old_notifications(organization: Organization, days: int = 30) -> int:
    """
    Supprime les notifications lues plus anciennes de `days` jours.
    """
    cutoff = timezone.now() - timezone.timedelta(days=days)
    count, _ = Notification.objects.filter(
        organization=organization,
        is_read=True,
        read_at__lt=cutoff,
    ).delete()
    return count
