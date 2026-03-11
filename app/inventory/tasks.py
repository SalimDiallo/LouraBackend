"""
Inventory — Celery Tasks
=========================
Tâches en background pour la gestion des ventes à crédit et notifications.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task
def check_credit_sale_deadlines():
    """
    Tâche périodique pour vérifier les échéances de ventes à crédit.

    Envoie des notifications pour:
    - Échéances approchantes (7 jours, 3 jours, 1 jour avant)
    - Paiements en retard

    Devrait être exécutée quotidiennement.
    """
    from core.models import Organization
    from .models import CreditSale
    from notifications.notification_helpers import send_notification

    today = timezone.now().date()
    processed_count = 0
    notifications_sent = 0

    logger.info("Démarrage vérification échéances crédit - %s", today)

    # Parcourir toutes les organisations actives
    organizations = Organization.objects.filter(is_active=True)

    for org in organizations:
        # Récupérer toutes les ventes à crédit non payées avec due_date
        credit_sales = CreditSale.objects.filter(
            organization=org,
            status__in=['pending', 'partial'],
            due_date__isnull=False
        ).select_related('customer', 'sale')

        for credit_sale in credit_sales:
            processed_count += 1

            # Calculer la vraie date limite avec délai de grâce
            effective_due_date = credit_sale.due_date
            if credit_sale.grace_period_days > 0:
                effective_due_date = credit_sale.due_date + timedelta(days=credit_sale.grace_period_days)

            days_until_due = (effective_due_date - today).days

            # --- ÉCHÉANCES APPROCHANTES ---

            # 7 jours avant (seulement si pas déjà envoyé récemment)
            if days_until_due == 7:
                if should_send_reminder(credit_sale, days=1):
                    sent = send_approaching_deadline_notification(
                        credit_sale, days_until_due, org
                    )
                    if sent:
                        notifications_sent += 1

            # 3 jours avant
            elif days_until_due == 3:
                if should_send_reminder(credit_sale, days=1):
                    sent = send_approaching_deadline_notification(
                        credit_sale, days_until_due, org
                    )
                    if sent:
                        notifications_sent += 1

            # 1 jour avant (priorité haute)
            elif days_until_due == 1:
                if should_send_reminder(credit_sale, days=1):
                    sent = send_approaching_deadline_notification(
                        credit_sale, days_until_due, org, priority='high'
                    )
                    if sent:
                        notifications_sent += 1

            # --- PAIEMENTS EN RETARD ---

            # Jour de l'échéance (sans grâce passée)
            elif days_until_due == 0:
                if should_send_reminder(credit_sale, days=1):
                    sent = send_overdue_notification(
                        credit_sale, days_overdue=0, organization=org, priority='high'
                    )
                    if sent:
                        notifications_sent += 1
                        # Mettre à jour le statut si nécessaire
                        credit_sale.update_status()
                        credit_sale.save()

            # En retard (échéances passées)
            elif days_until_due < 0:
                days_overdue = abs(days_until_due)

                # Rappels progressifs: 1, 3, 7, 14, 30 jours de retard
                if days_overdue in [1, 3, 7, 14, 30]:
                    # Vérifier si on n'a pas déjà envoyé aujourd'hui
                    if should_send_reminder(credit_sale, days=1):
                        priority = 'critical' if days_overdue >= 7 else 'high'
                        sent = send_overdue_notification(
                            credit_sale, days_overdue, org, priority=priority
                        )
                        if sent:
                            notifications_sent += 1
                            # Mettre à jour le statut
                            credit_sale.update_status()
                            credit_sale.save()

    logger.info(
        "Vérification échéances terminée - Créances traitées: %d, Notifications envoyées: %d",
        processed_count, notifications_sent
    )

    return {
        'processed': processed_count,
        'notifications_sent': notifications_sent
    }


def should_send_reminder(credit_sale, days=1):
    """
    Vérifie si on doit envoyer un rappel.
    Évite d'envoyer plusieurs fois le même jour.

    Args:
        credit_sale: Instance CreditSale
        days: Nombre de jours depuis le dernier rappel (défaut: 1)

    Returns:
        bool: True si on peut envoyer
    """
    if not credit_sale.last_reminder_date:
        return True

    from django.utils import timezone
    days_since_last = (timezone.now().date() - credit_sale.last_reminder_date).days
    return days_since_last >= days


def send_approaching_deadline_notification(credit_sale, days_until_due, organization, priority='medium'):
    """
    Envoie une notification pour une échéance approchante.

    Args:
        credit_sale: Instance CreditSale
        days_until_due: Nombre de jours avant échéance
        organization: Organisation
        priority: Priorité de la notification

    Returns:
        bool: True si envoyé
    """
    from notifications.notification_helpers import send_notification
    from core.models import BaseUser

    customer_name = credit_sale.customer.name if credit_sale.customer else "Client inconnu"
    sale_number = credit_sale.sale.sale_number if credit_sale.sale else "N/A"

    # Obtenir la devise de l'organisation
    currency = getattr(organization, 'currency', 'FCFA')

    # Message personnalisé selon le nombre de jours
    if days_until_due == 1:
        title = f"⚠️ Échéance demain - {customer_name}"
        urgency = "demain"
    elif days_until_due == 3:
        title = f"Échéance dans 3 jours - {customer_name}"
        urgency = "dans 3 jours"
    else:
        title = f"Échéance dans {days_until_due} jours - {customer_name}"
        urgency = f"dans {days_until_due} jours"

    message = (
        f"La créance #{sale_number} arrive à échéance {urgency}.\n"
        f"Client: {customer_name}\n"
        f"Montant restant: {credit_sale.remaining_amount:,.0f} {currency}\n"
        f"Date d'échéance: {credit_sale.due_date.strftime('%d/%m/%Y')}"
    )

    # Envoyer aux admins de l'organisation
    admins = BaseUser.objects.filter(
        organizations=organization,
        role__in=['admin', 'super_admin'],
        is_active=True
    )

    sent = False
    for admin in admins:
        try:
            send_notification(
                organization=organization,
                recipient=admin,
                title=title,
                message=message,
                notification_type='alert',
                priority=priority,
                entity_type='credit_sale',
                entity_id=str(credit_sale.id),
                action_url=f'/inventory/credit-sales/{credit_sale.id}'
            )
            sent = True
        except Exception as e:
            logger.error(f"Erreur envoi notification échéance: {e}")

    if sent:
        # Mettre à jour les champs de tracking
        credit_sale.last_reminder_date = timezone.now().date()
        credit_sale.reminder_count += 1
        credit_sale.save(update_fields=['last_reminder_date', 'reminder_count'])

    return sent


def send_overdue_notification(credit_sale, days_overdue, organization, priority='high'):
    """
    Envoie une notification pour un paiement en retard.

    Args:
        credit_sale: Instance CreditSale
        days_overdue: Nombre de jours de retard
        organization: Organisation
        priority: Priorité de la notification

    Returns:
        bool: True si envoyé
    """
    from notifications.notification_helpers import send_notification
    from core.models import BaseUser

    customer_name = credit_sale.customer.name if credit_sale.customer else "Client inconnu"
    sale_number = credit_sale.sale.sale_number if credit_sale.sale else "N/A"

    # Obtenir la devise de l'organisation
    currency = getattr(organization, 'currency', 'FCFA')

    # Message personnalisé selon le nombre de jours de retard
    if days_overdue == 0:
        title = f"🔴 Échéance aujourd'hui - {customer_name}"
        urgency_msg = "arrive à échéance aujourd'hui"
    elif days_overdue == 1:
        title = f"🔴 Paiement en retard (1 jour) - {customer_name}"
        urgency_msg = "est en retard de 1 jour"
    else:
        title = f"🔴 Paiement en retard ({days_overdue} jours) - {customer_name}"
        urgency_msg = f"est en retard de {days_overdue} jours"

    message = (
        f"La créance #{sale_number} {urgency_msg}.\n"
        f"Client: {customer_name}\n"
        f"Montant restant: {credit_sale.remaining_amount:,.0f} {currency}\n"
        f"Date d'échéance: {credit_sale.due_date.strftime('%d/%m/%Y')}\n"
        f"Rappels envoyés: {credit_sale.reminder_count}"
    )

    # Envoyer aux admins de l'organisation
    admins = BaseUser.objects.filter(
        organizations=organization,
        role__in=['admin', 'super_admin'],
        is_active=True
    )

    sent = False
    for admin in admins:
        try:
            send_notification(
                organization=organization,
                recipient=admin,
                title=title,
                message=message,
                notification_type='alert',
                priority=priority,
                entity_type='credit_sale',
                entity_id=str(credit_sale.id),
                action_url=f'/inventory/credit-sales/{credit_sale.id}'
            )
            sent = True
        except Exception as e:
            logger.error(f"Erreur envoi notification retard: {e}")

    if sent:
        # Mettre à jour les champs de tracking
        credit_sale.last_reminder_date = timezone.now().date()
        credit_sale.reminder_count += 1
        credit_sale.save(update_fields=['last_reminder_date', 'reminder_count'])

    return sent


@shared_task
def update_overdue_credit_sales():
    """
    Tâche périodique pour mettre à jour le statut des ventes à crédit.
    Vérifie toutes les créances et met à jour leur statut overdue.

    Devrait être exécutée quotidiennement.
    """
    from .models import CreditSale

    today = timezone.now().date()
    updated_count = 0

    logger.info("Mise à jour statuts créances - %s", today)

    # Récupérer toutes les ventes à crédit non payées avec due_date
    credit_sales = CreditSale.objects.filter(
        status__in=['pending', 'partial'],
        due_date__isnull=False
    )

    for credit_sale in credit_sales:
        old_status = credit_sale.status
        credit_sale.update_status()

        if old_status != credit_sale.status:
            credit_sale.save()
            updated_count += 1

    logger.info("Mise à jour statuts terminée - %d créances mises à jour", updated_count)

    return {'updated': updated_count}
