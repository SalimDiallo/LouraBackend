"""
Novu — Celery Tasks
====================
Tâches asynchrones pour les appels vers l'API Novu.

Les appels Novu sont effectués en background pour ne jamais
bloquer les requêtes HTTP ou la logique métier.
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def novu_trigger_workflow_task(
    self,
    workflow_id: str,
    subscriber_id: str,
    payload: dict,
    overrides: dict | None = None,
    tenant_id: str | None = None,
):
    """
    Déclenche un workflow Novu de façon asynchrone.

    Utilisé par notification_helpers.py pour que le trigger Novu
    ne bloque pas le code métier.
    """
    from .novu_service import novu_service

    try:
        success = novu_service.trigger_workflow(
            workflow_id=workflow_id,
            subscriber_id=subscriber_id,
            payload=payload,
            overrides=overrides,
            tenant_id=tenant_id,
        )

        if not success:
            logger.warning(
                "Novu trigger a retourné False pour workflow=%s subscriber=%s",
                workflow_id, subscriber_id,
            )

        return success

    except Exception as exc:
        logger.error(
            "Erreur novu_trigger_workflow_task workflow=%s : %s",
            workflow_id, exc,
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def novu_identify_subscriber_task(
    self,
    user_id: str,
    first_name: str = '',
    last_name: str = '',
    email: str = '',
    phone: str = '',
    user_type: str = 'unknown',
):
    """
    Synchronise un utilisateur Django vers Novu en background.

    Appelé à la création/mise à jour d'un utilisateur.
    """
    from .novu_service import novu_service

    if not novu_service.is_enabled:
        return False

    try:
        from novu_py import models

        novu_service.client.subscribers.create(
            subscriber=models.SubscriberDto(
                subscriber_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                phone=phone if phone else None,
                data={
                    'user_type': user_type,
                    'django_id': user_id,
                }
            )
        )

        logger.info("Subscriber Novu synchronisé (task) : %s", user_id)
        return True

    except Exception as exc:
        logger.error("Erreur novu_identify_subscriber_task : %s", exc)
        raise self.retry(exc=exc)


@shared_task
def novu_sync_all_subscribers_task(organization_id: str | None = None):
    """
    Synchronise tous les utilisateurs d'une organisation (ou de toutes)
    vers Novu. Tâche de maintenance.
    """
    from core.models import BaseUser, Organization
    from .novu_service import novu_service

    if not novu_service.is_enabled:
        logger.info("Novu désactivé — sync annulée")
        return 0

    qs = BaseUser.objects.filter(is_active=True)

    if organization_id:
        try:
            org = Organization.objects.get(id=organization_id)
            # Filtrer les admins et employés de cette organisation
            from django.db.models import Q
            qs = qs.filter(
                Q(adminuser__organizations=org) |
                Q(employee__organization=org)
            ).distinct()
        except Organization.DoesNotExist:
            logger.warning("Organisation %s non trouvée pour sync Novu", organization_id)
            return 0

    synced = 0
    for user in qs:
        success = novu_service.identify_subscriber(user)
        if success:
            synced += 1

    logger.info("Sync Novu terminée : %d/%d subscribers", synced, qs.count())
    return synced
