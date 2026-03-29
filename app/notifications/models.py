"""
Notifications Module — Models
==============================
Système de notifications interne pour Loura.

- Notification   : chaque notification envoyée à un utilisateur dans une organisation.
- NotificationPreference : préférences de notification par utilisateur + organisation.

Liens possibles vers des entités tierces via `entity_type` / `entity_id`
(ex : un produit, une commande, une alerte …) sans FK physique, pour
rester générique et éviter les imports circulaires.
"""

from django.db import models
from django.utils import timezone

from lourabackend.models import TimeStampedModel
from core.models import Organization, BaseUser


# ===============================
# NOTIFICATION
# ===============================

class Notification(TimeStampedModel):
    """
    Notification interne envoyée à un utilisateur.

    Types de notification :
        - alert     : alerte de stock ou autre alerte métier
        - system    : message système (ex : mise à jour, maintenance)
        - user      : action d'un autre utilisateur (ex : commentaire, assignation)

    Priorités :
        - low      : info
        - medium   : avertissement
        - high     : important
        - critical : urgent / bloquant
    """

    # --- Types -----------------------------------------------------------
    TYPE_CHOICES = [
        ('alert', 'Alerte'),
        ('system', 'Système'),
        ('user', 'Utilisateur'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]

    # --- Champs ----------------------------------------------------------
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Organisation à laquelle appartient cette notification"
    )

    # Destinataire : toujours un utilisateur concret (Admin ou Employee via BaseUser)
    recipient = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Utilisateur destinataire"
    )

    # Expéditeur (optionnel) : peut être None pour les notifications systèmes
    sender = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text="Utilisateur qui a déclenché la notification (None = système)"
    )

    # Contenu
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system',
        verbose_name="Type"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorité"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre"
    )
    message = models.TextField(
        verbose_name="Message"
    )

    # Lien vers une entité tierce (générique, sans FK)
    # Ex : entity_type='product', entity_id='uuid-du-produit'
    entity_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Type d'entité liée",
        help_text="ex : product, order, alert, employee …"
    )
    entity_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="ID de l'entité liée"
    )

    # URL de redirection après clic (construite côté backend ou fournie manuellement)
    action_url = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name="URL d'action"
    )

    # Statut lecture
    is_read = models.BooleanField(default=False, verbose_name="Lue")
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at'], name='idx_notif_recipient_date'),
            models.Index(fields=['organization', 'is_read'], name='idx_notif_org_read'),
        ]

    def __str__(self):
        status_label = "Lue" if self.is_read else "Non lue"
        return f"[{self.get_notification_type_display()}] {self.title} ({status_label})"

    # --- Helpers ---------------------------------------------------------
    def mark_as_read(self):
        """Marque la notification comme lue."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ===============================
# NOTIFICATION PREFERENCES
# ===============================

class NotificationPreference(TimeStampedModel):
    """
    Préférences de notification par utilisateur et organisation.

    Permet à chaque utilisateur de contrôler :
        - les types de notifications qu'il souhaite recevoir
        - le mode de livraison (in-app uniquement pour le moment)
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    user = models.ForeignKey(
        BaseUser,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Filtres par type
    receive_alerts = models.BooleanField(
        default=True,
        verbose_name="Recevoir les alertes"
    )
    receive_system = models.BooleanField(
        default=True,
        verbose_name="Recevoir les notifications système"
    )
    receive_user = models.BooleanField(
        default=True,
        verbose_name="Recevoir les notifications utilisateur"
    )

    # Filtres par priorité minimale
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]
    min_priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='low',
        verbose_name="Priorité minimale",
        help_text="Les notifications en dessous de cette priorité ne seront pas affichées"
    )

    # --- Canaux de livraison (Novu multi-canal) ---
    email_enabled = models.BooleanField(
        default=True,
        verbose_name="Recevoir par email",
        help_text="Activer les notifications par email (nécessite Novu)"
    )
    sms_enabled = models.BooleanField(
        default=False,
        verbose_name="Recevoir par SMS",
        help_text="Activer les notifications par SMS (nécessite Novu + crédits SMS)"
    )
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="Recevoir les push",
        help_text="Activer les notifications push navigateur/mobile"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="Numéro de téléphone SMS",
        help_text="Numéro de téléphone pour les notifications SMS (format international : +224...)"
    )

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = "Préférences de notification"
        verbose_name_plural = "Préférences de notifications"
        unique_together = [['organization', 'user']]

    def __str__(self):
        return f"Préférences de {self.user.get_full_name()} ({self.organization.name})"

