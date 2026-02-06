"""
Notification Helpers
====================
Fonctions utilitaires pour créer, envoyer et gérer les notifications.

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

import logging
from typing import Optional

from django.utils import timezone

from core.models import BaseUser, Organization
from .models import Notification, NotificationPreference


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mappage priorité → texte lisible
# ---------------------------------------------------------------------------
PRIORITY_ORDER = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}

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

    Args:
        organization  : Organisation du contexte.
        recipient     : Utilisateur destinataire (BaseUser).
        title         : Titre court de la notification.
        message       : Corps de la notification.
        notification_type : 'alert' | 'system' | 'user'.
        priority      : 'low' | 'medium' | 'high' | 'critical'.
        sender        : Utilisateur expéditeur (None = système).
        entity_type   : Type d'entité liée (ex : 'product', 'order').
        entity_id     : ID de l'entité liée (UUID en string).
        action_url    : URL de redirection après clic.
    """
    # --- Vérification des préférences ----------------------------------------
    if not _should_deliver(organization, recipient, notification_type, priority):
        logger.debug(
            "Notification filtrée par préférences : recipient=%s, type=%s, priority=%s",
            recipient.id, notification_type, priority
        )
        return None

    # --- Dispatch via Celery (ou sync si ALWAYS_EAGER) ------------------------
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
        # Fallback synchrone : on ne bloque jamais la logique métier
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
        return notification

    # En mode eager la tâche s'exécute sync → on retourne l'instance créée
    # En mode async on ne peut pas retourner l'objet, on retourne None
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

    Utilisé typiquement depuis alert_utils.py après la création d'une alerte.

    Args:
        organization : Organisation concernée.
        product      : Instance du produit concerné.
        alert_type   : 'low_stock' | 'out_of_stock' | 'overstock' | 'expiring_soon'.
        severity     : 'low' | 'medium' | 'high' | 'critical'.
        message      : Message personnalisé (sinon, géné automatiquement).
        warehouse    : Entrepôt concerné (optionnel).

    Returns:
        Liste des Notification créées (une par destinataire).
    """
    # Titre selon le type d'alerte
    TITLE_MAP = {
        'low_stock': 'Stock bas',
        'out_of_stock': 'Rupture de stock',
        'overstock': 'Surstock',
        'expiring_soon': 'Expiration proche',
    }
    title = TITLE_MAP.get(alert_type, 'Alerte stock')

    # Message par défaut
    if not message:
        loc = f" à {warehouse.name}" if warehouse else ""
        message = f"{title} : {product.name}{loc} ({product.sku})"

    # Récupérer les destinataires : admin de l'organisation
    # On utilise BaseUser via l'organisation pour toucher les AdminUser associés
    admin_users = BaseUser.objects.filter(
        user_type='admin',
        adminuser__organizations=organization,
        is_active=True,
    )

    created = []
    for user in admin_users:
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

    Returns:
        Nombre de notifications mises à jour.
    """
    now = timezone.now()
    count, _ = Notification.objects.filter(
        organization=organization,
        recipient=user,
        is_read=False,
    ).update(is_read=True, read_at=now)
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

    Returns:
        Nombre de notifications supprimées.
    """
    cutoff = timezone.now() - timezone.timedelta(days=days)
    count, _ = Notification.objects.filter(
        organization=organization,
        is_read=True,
        read_at__lt=cutoff,
    ).delete()
    return count


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
        # Pas de préférences configurées : on livre par défaut
        return True

    # --- Filtrer par type -------------------------------------------------------
    type_map = {
        'alert': pref.receive_alerts,
        'system': pref.receive_system,
        'user': pref.receive_user,
    }
    if not type_map.get(notification_type, True):
        return False

    # --- Filtrer par priorité minimale ------------------------------------------
    if PRIORITY_ORDER.get(priority, 0) < PRIORITY_ORDER.get(pref.min_priority, 0):
        return False

    return True
