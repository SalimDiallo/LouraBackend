"""
Novu Service — Passerelle vers Novu Cloud
==========================================
Service centralisé pour l'intégration Novu.

Responsabilités :
  - Gestion des subscribers (sync utilisateurs Django → Novu)
  - Déclenchement des workflows multi-canaux
  - Sync des préférences de notification

Le service est conçu pour être **résilient** :
  - Si Novu est désactivé (`NOVU_ENABLED=False`), toutes les méthodes
    retournent silencieusement sans erreur.
  - Si un appel Novu échoue, l'erreur est loggée mais ne bloque jamais
    la logique métier (le canal in-app local fonctionne toujours).

Usage :
    from notifications.novu_service import novu_service
    novu_service.trigger_workflow('stock-alert', subscriber_id, payload)
"""

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Workflow IDs (doivent correspondre aux workflows créés dans le Dashboard Novu)
# ---------------------------------------------------------------------------

class NovuWorkflows:
    """Identifiants des workflows définis dans le Dashboard Novu."""
    STOCK_ALERT = 'stock-alert'
    CREDIT_DEADLINE_APPROACHING = 'credit-deadline-approaching'
    CREDIT_OVERDUE = 'credit-overdue'
    SYSTEM_ANNOUNCEMENT = 'system-announcement'
    USER_ACTION = 'user-action'
    DAILY_DIGEST = 'daily-digest'
    WELCOME = 'welcome'


# ---------------------------------------------------------------------------
# NovuService
# ---------------------------------------------------------------------------

class NovuService:
    """
    Service singleton pour interagir avec l'API Novu.

    Toutes les méthodes sont fail-safe : elles catchent les exceptions
    et loggent les erreurs sans les propager.
    """

    def __init__(self):
        self._client = None
        self._enabled = getattr(settings, 'NOVU_ENABLED', False)
        self._api_key = getattr(settings, 'NOVU_API_KEY', '')

    # --- Client lazy (initialisé au premier appel) -------------------------

    @property
    def client(self):
        """Client Novu initialisé paresseusement."""
        if not self._enabled:
            return None

        if self._client is None:
            try:
                from novu_py import Novu
                self._client = Novu(secret_key=self._api_key)
                logger.info("Client Novu initialisé avec succès")
            except ImportError:
                logger.error(
                    "Le package 'novu-py' n'est pas installé. "
                    "Installez-le via : pip install novu-py"
                )
                self._enabled = False
            except Exception as e:
                logger.error("Erreur initialisation client Novu : %s", e)
                self._enabled = False

        return self._client

    @property
    def is_enabled(self) -> bool:
        """Indique si le service Novu est activé et opérationnel."""
        return self._enabled and self._api_key != ''

    # -----------------------------------------------------------------------
    # Subscriber Management
    # -----------------------------------------------------------------------

    def identify_subscriber(
        self,
        user,
        phone: str = '',
    ) -> bool:
        """
        Crée ou met à jour un subscriber dans Novu.

        Doit être appelé :
          - À la création d'un utilisateur
          - Quand un utilisateur met à jour son email/téléphone
          - Au login (pour s'assurer de la synchronisation)

        Args:
            user: Instance BaseUser (AdminUser ou Employee)
            phone: Numéro de téléphone pour le canal SMS

        Returns:
            True si l'opération a réussi, False sinon
        """
        if not self.is_enabled or not self.client:
            return False

        try:
            from novu_py import models

            subscriber_id = str(user.id)
            first_name = getattr(user, 'first_name', '') or ''
            last_name = getattr(user, 'last_name', '') or ''
            email = getattr(user, 'email', '') or ''

            self.client.subscribers.create(
                subscriber=models.SubscriberDto(
                    subscriber_id=subscriber_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email if email else None,
                    phone=phone if phone else None,
                    data={
                        'user_type': getattr(user, 'user_type', 'unknown'),
                        'django_id': subscriber_id,
                    }
                )
            )

            logger.info(
                "Subscriber Novu synchronisé : id=%s, email=%s",
                subscriber_id, email
            )
            return True

        except Exception as e:
            logger.warning("Échec identify_subscriber Novu : %s", e)
            return False

    def delete_subscriber(self, user_id: str) -> bool:
        """Supprime un subscriber de Novu."""
        if not self.is_enabled or not self.client:
            return False

        try:
            self.client.subscribers.delete(subscriber_id=user_id)
            logger.info("Subscriber Novu supprimé : %s", user_id)
            return True
        except Exception as e:
            logger.warning("Échec delete_subscriber Novu : %s", e)
            return False

    # -----------------------------------------------------------------------
    # Trigger Workflows
    # -----------------------------------------------------------------------

    def trigger_workflow(
        self,
        workflow_id: str,
        subscriber_id: str,
        payload: dict,
        overrides: Optional[dict] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Déclenche un workflow Novu.

        Args:
            workflow_id: ID du workflow (cf. NovuWorkflows)
            subscriber_id: UUID de l'utilisateur Django (= subscriber_id Novu)
            payload: Données dynamiques pour le template
            overrides: Overrides optionnels pour les canaux
            tenant_id: ID du tenant (organisation) optionnel

        Returns:
            True si le trigger a réussi
        """
        if not self.is_enabled or not self.client:
            return False

        try:
            from novu_py import models

            trigger_data = {
                'name': workflow_id,
                'to': models.SubscriberPayloadDto(
                    subscriber_id=subscriber_id,
                ),
                'payload': payload,
            }

            if overrides:
                trigger_data['overrides'] = overrides

            if tenant_id:
                trigger_data['tenant'] = tenant_id

            self.client.trigger(**trigger_data)

            logger.info(
                "Workflow Novu déclenché : workflow=%s, subscriber=%s",
                workflow_id, subscriber_id
            )
            return True

        except Exception as e:
            logger.warning(
                "Échec trigger workflow Novu '%s' pour subscriber=%s : %s",
                workflow_id, subscriber_id, e
            )
            return False

    # -----------------------------------------------------------------------
    # Raccourcis métier
    # -----------------------------------------------------------------------

    def trigger_stock_alert(
        self,
        subscriber_id: str,
        product_name: str,
        product_sku: str,
        alert_type: str,
        severity: str,
        current_stock: float,
        threshold: float,
        warehouse_name: str = '',
        organization_name: str = '',
    ) -> bool:
        """Déclenche le workflow d'alerte de stock."""
        return self.trigger_workflow(
            workflow_id=NovuWorkflows.STOCK_ALERT,
            subscriber_id=subscriber_id,
            payload={
                'product_name': product_name,
                'product_sku': product_sku,
                'alert_type': alert_type,
                'severity': severity,
                'current_stock': current_stock,
                'threshold': threshold,
                'warehouse_name': warehouse_name,
                'organization_name': organization_name,
            },
        )

    def trigger_credit_deadline(
        self,
        subscriber_id: str,
        customer_name: str,
        sale_number: str,
        remaining_amount: float,
        due_date: str,
        days_until_due: int,
        currency: str = 'FCFA',
        organization_name: str = '',
    ) -> bool:
        """Déclenche le workflow d'échéance de crédit approchante."""
        return self.trigger_workflow(
            workflow_id=NovuWorkflows.CREDIT_DEADLINE_APPROACHING,
            subscriber_id=subscriber_id,
            payload={
                'customer_name': customer_name,
                'sale_number': sale_number,
                'remaining_amount': remaining_amount,
                'due_date': due_date,
                'days_until_due': days_until_due,
                'currency': currency,
                'organization_name': organization_name,
            },
        )

    def trigger_credit_overdue(
        self,
        subscriber_id: str,
        customer_name: str,
        sale_number: str,
        remaining_amount: float,
        due_date: str,
        days_overdue: int,
        reminder_count: int = 0,
        currency: str = 'FCFA',
        organization_name: str = '',
    ) -> bool:
        """Déclenche le workflow de paiement en retard."""
        return self.trigger_workflow(
            workflow_id=NovuWorkflows.CREDIT_OVERDUE,
            subscriber_id=subscriber_id,
            payload={
                'customer_name': customer_name,
                'sale_number': sale_number,
                'remaining_amount': remaining_amount,
                'due_date': due_date,
                'days_overdue': days_overdue,
                'reminder_count': reminder_count,
                'currency': currency,
                'organization_name': organization_name,
            },
        )

    def trigger_system_announcement(
        self,
        subscriber_id: str,
        title: str,
        message: str,
        action_url: str = '',
        organization_name: str = '',
    ) -> bool:
        """Déclenche le workflow d'annonce système."""
        return self.trigger_workflow(
            workflow_id=NovuWorkflows.SYSTEM_ANNOUNCEMENT,
            subscriber_id=subscriber_id,
            payload={
                'title': title,
                'message': message,
                'action_url': action_url,
                'organization_name': organization_name,
            },
        )

    # -----------------------------------------------------------------------
    # Subscriber Preferences (sync depuis/vers Novu)
    # -----------------------------------------------------------------------

    def update_subscriber_preferences(
        self,
        subscriber_id: str,
        email_enabled: bool = True,
        sms_enabled: bool = False,
        push_enabled: bool = True,
        in_app_enabled: bool = True,
    ) -> bool:
        """
        Met à jour les préférences de canal d'un subscriber dans Novu.

        Note : Les préférences par workflow sont gérées directement
        dans le Dashboard Novu. Cette méthode gère les préférences
        globales par canal.
        """
        if not self.is_enabled or not self.client:
            return False

        try:
            # Novu gère les préférences via les subscriber preferences API
            # Cela permet au subscriber de désactiver certains canaux
            channels = []
            if not email_enabled:
                channels.append({'type': 'email', 'enabled': False})
            if not sms_enabled:
                channels.append({'type': 'sms', 'enabled': False})
            if not push_enabled:
                channels.append({'type': 'push', 'enabled': False})
            if not in_app_enabled:
                channels.append({'type': 'in_app', 'enabled': False})

            self.client.subscribers.preferences.update(
                subscriber_id=subscriber_id,
                channel=channels,
            )

            logger.info(
                "Préférences Novu mises à jour : subscriber=%s",
                subscriber_id
            )
            return True

        except Exception as e:
            logger.warning(
                "Échec update préférences Novu subscriber=%s : %s",
                subscriber_id, e
            )
            return False


# ---------------------------------------------------------------------------
# Singleton — importable directement
# ---------------------------------------------------------------------------

novu_service = NovuService()
