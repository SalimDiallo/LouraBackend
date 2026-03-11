"""
Services Module Models
=======================
Module générique pour la gestion de tout type de service.
Architecture modulaire et configurable par données.

Schéma:
BusinessProfile -> ServiceType -> ServiceField/ServiceStatus -> Service

Fonctionnalités:
- Services imbriqués (services dans des services)
- Champs dynamiques personnalisables
- Statuts configurables par type
- Multi-organisation
- Historique complet
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from lourabackend.models import TimeStampedModel
from core.models import Organization, BaseUser


# ===============================
# 1. BUSINESS PROFILE (Secteur d'activité)
# ===============================

class BusinessProfile(TimeStampedModel):
    """
    Profil métier / Secteur d'activité
    Ex: BTP, Voyage, Automobile, Formation
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='business_profiles'
    )

    name = models.CharField(
        max_length=255,
        help_text="Nom du secteur d'activité"
    )

    code = models.SlugField(
        max_length=100,
        help_text="Code unique pour identification"
    )

    description = models.TextField(blank=True)

    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Icône pour l'interface (ex: Building, Car, Plane)"
    )

    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Couleur hexadécimale pour l'UI"
    )

    is_active = models.BooleanField(default=True)

    # Métadonnées configurables
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration spécifique au métier"
    )

    class Meta:
        db_table = 'services_business_profiles'
        verbose_name = "Profil métier"
        verbose_name_plural = "Profils métier"
        unique_together = [['organization', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ===============================
# 2. SERVICE TYPE (Type de service)
# ===============================

class ServiceType(TimeStampedModel):
    """
    Type de service proposé
    Ex: Location voiture, Projet BTP, Dossier voyage
    """

    business_profile = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='service_types'
    )

    name = models.CharField(
        max_length=255,
        help_text="Nom du type de service"
    )

    code = models.SlugField(
        max_length=100,
        help_text="Code unique pour identification"
    )

    description = models.TextField(blank=True)

    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#10B981")

    # Configuration du workflow
    requires_approval = models.BooleanField(
        default=False,
        help_text="Ce type de service nécessite une approbation"
    )

    allow_nested_services = models.BooleanField(
        default=False,
        help_text="Peut contenir des sous-services"
    )

    # Types de services autorisés en tant que sous-services
    allowed_child_types = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parent_types',
        help_text="Types de services pouvant être ajoutés comme sous-services"
    )

    # Gestion du pricing
    has_pricing = models.BooleanField(
        default=True,
        help_text="Ce type de service a un système de tarification"
    )

    pricing_model = models.CharField(
        max_length=50,
        choices=[
            ('fixed', 'Prix fixe'),
            ('hourly', 'Tarif horaire'),
            ('daily', 'Tarif journalier'),
            ('custom', 'Personnalisé'),
        ],
        default='custom'
    )

    is_active = models.BooleanField(default=True)

    # Template de service (valeurs par défaut)
    default_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Valeurs par défaut pour les champs"
    )

    # Configuration avancée
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration spécifique au type"
    )

    class Meta:
        db_table = 'services_types'
        verbose_name = "Type de service"
        verbose_name_plural = "Types de service"
        unique_together = [['business_profile', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.business_profile.name})"

    @property
    def organization(self):
        return self.business_profile.organization


# ===============================
# 3. SERVICE FIELD (Champs dynamiques)
# ===============================

class ServiceField(TimeStampedModel):
    """
    Champ dynamique pour un type de service
    Ex: Marque, Modèle, Date début, Prix
    """

    FIELD_TYPES = [
        ('text', 'Texte'),
        ('textarea', 'Texte long'),
        ('number', 'Nombre'),
        ('decimal', 'Décimal'),
        ('date', 'Date'),
        ('datetime', 'Date et heure'),
        ('boolean', 'Oui/Non'),
        ('select', 'Liste déroulante'),
        ('multiselect', 'Sélection multiple'),
        ('file', 'Fichier'),
        ('image', 'Image'),
        ('email', 'Email'),
        ('phone', 'Téléphone'),
        ('url', 'URL'),
        ('currency', 'Montant'),
        ('user', 'Utilisateur'),
        ('relation', 'Relation vers un autre service'),
    ]

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.CASCADE,
        related_name='fields'
    )

    name = models.CharField(
        max_length=255,
        help_text="Nom du champ (affiché)"
    )

    field_key = models.SlugField(
        max_length=100,
        help_text="Clé unique pour stockage"
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default='text'
    )

    description = models.TextField(
        blank=True,
        help_text="Description ou aide pour l'utilisateur"
    )

    # Configuration du champ
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    is_searchable = models.BooleanField(default=True)
    is_visible_in_list = models.BooleanField(default=True)

    # Ordre d'affichage
    order = models.IntegerField(default=0)

    # Valeur par défaut
    default_value = models.TextField(blank=True, null=True)

    # Validation
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Règles de validation (min, max, pattern, etc.)"
    )

    # Options pour select/multiselect
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="Options pour les champs de type select"
    )

    # Configuration avancée
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuration spécifique (unité, format, etc.)"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'services_fields'
        verbose_name = "Champ de service"
        verbose_name_plural = "Champs de service"
        unique_together = [['service_type', 'field_key']]
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.service_type.name})"


# ===============================
# 4. SERVICE STATUS (Statuts)
# ===============================

class ServiceStatus(TimeStampedModel):
    """
    Statut du cycle de vie d'un service
    Ex: Réservé, En cours, Terminé, Annulé
    """

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.CASCADE,
        related_name='statuses'
    )

    name = models.CharField(max_length=100)

    code = models.SlugField(
        max_length=50,
        help_text="Code unique pour identification"
    )

    description = models.TextField(blank=True)

    color = models.CharField(
        max_length=7,
        default="#6B7280",
        help_text="Couleur pour l'affichage"
    )

    icon = models.CharField(max_length=50, blank=True)

    # Ordre dans le workflow
    order = models.IntegerField(default=0)

    # Type de statut
    status_type = models.CharField(
        max_length=50,
        choices=[
            ('initial', 'Initial'),
            ('in_progress', 'En cours'),
            ('completed', 'Terminé'),
            ('cancelled', 'Annulé'),
            ('on_hold', 'En attente'),
        ],
        default='in_progress'
    )

    # Workflow
    is_initial = models.BooleanField(
        default=False,
        help_text="Statut par défaut à la création"
    )

    is_final = models.BooleanField(
        default=False,
        help_text="Statut final (terminé ou annulé)"
    )

    requires_comment = models.BooleanField(
        default=False,
        help_text="Nécessite un commentaire lors du passage à ce statut"
    )

    # Transitions autorisées
    allowed_next_statuses = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='previous_statuses',
        help_text="Statuts suivants autorisés"
    )

    # Permissions
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        help_text="Permission requise pour passer à ce statut"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'services_statuses'
        verbose_name = "Statut de service"
        verbose_name_plural = "Statuts de service"
        unique_together = [['service_type', 'code']]
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.service_type.name})"


# ===============================
# 5. SERVICE (Service réel)
# ===============================

class Service(TimeStampedModel):
    """
    Service réel pour un client
    Ex: Location Prado pour M. Diallo
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='services'
    )

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name='services'
    )

    # Référence unique
    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Référence unique du service (ex: SRV-2024-001)"
    )

    # Titre/Nom du service
    title = models.CharField(
        max_length=500,
        help_text="Titre descriptif du service"
    )

    description = models.TextField(blank=True)

    # Client (peut être un contact, une entreprise, etc.)
    client_type = models.CharField(
        max_length=50,
        choices=[
            ('individual', 'Particulier'),
            ('company', 'Entreprise'),
        ],
        default='individual'
    )

    client_name = models.CharField(max_length=255)
    client_email = models.EmailField(blank=True, null=True)
    client_phone = models.CharField(max_length=50, blank=True)

    # Relations
    client_user = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_services',
        help_text="Si le client est un utilisateur du système"
    )

    assigned_to = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_services',
        help_text="Employé assigné au service"
    )

    # Services imbriqués
    parent_service = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_services',
        help_text="Service parent si c'est un sous-service"
    )

    # Statut actuel
    current_status = models.ForeignKey(
        ServiceStatus,
        on_delete=models.PROTECT,
        related_name='current_services'
    )

    # Données dynamiques (valeurs des champs)
    field_values = models.JSONField(
        default=dict,
        help_text="Valeurs des champs dynamiques"
    )

    # Dates importantes
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Pricing
    estimated_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Montant estimé"
    )

    actual_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Montant réel"
    )

    currency = models.CharField(max_length=3, default='MAD')

    # Priorité
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Basse'),
            ('normal', 'Normale'),
            ('high', 'Haute'),
            ('urgent', 'Urgente'),
        ],
        default='normal'
    )

    # Tags
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags pour catégorisation"
    )

    # Métadonnées
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données additionnelles"
    )

    # Fichiers attachés
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des fichiers attachés"
    )

    is_archived = models.BooleanField(default=False)

    class Meta:
        db_table = 'services'
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'service_type']),
            models.Index(fields=['reference']),
            models.Index(fields=['current_status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.reference} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-générer la référence si non fournie
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def generate_reference(self):
        """Génère une référence unique"""
        import datetime
        from django.db.models import Max

        year = datetime.datetime.now().year
        prefix = self.service_type.code.upper()[:3]

        # Trouver le dernier numéro
        last_service = Service.objects.filter(
            organization=self.organization,
            reference__startswith=f"{prefix}-{year}"
        ).aggregate(Max('reference'))

        if last_service['reference__max']:
            last_num = int(last_service['reference__max'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}-{year}-{new_num:05d}"


# ===============================
# 6. SERVICE STATUS HISTORY (Historique)
# ===============================

class ServiceStatusHistory(TimeStampedModel):
    """
    Historique des changements de statut
    """

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='status_history'
    )

    from_status = models.ForeignKey(
        ServiceStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='history_from'
    )

    to_status = models.ForeignKey(
        ServiceStatus,
        on_delete=models.PROTECT,
        related_name='history_to'
    )

    changed_by = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='service_status_changes'
    )

    comment = models.TextField(blank=True)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Données additionnelles sur le changement"
    )

    class Meta:
        db_table = 'services_status_history'
        verbose_name = "Historique de statut"
        verbose_name_plural = "Historiques de statut"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.service.reference}: {self.from_status} → {self.to_status}"


# ===============================
# 7. SERVICE ACTIVITY (Activités)
# ===============================

class ServiceActivity(TimeStampedModel):
    """
    Journal d'activités sur un service
    """

    ACTIVITY_TYPES = [
        ('created', 'Créé'),
        ('updated', 'Modifié'),
        ('status_changed', 'Statut changé'),
        ('assigned', 'Assigné'),
        ('comment_added', 'Commentaire ajouté'),
        ('file_attached', 'Fichier attaché'),
        ('field_changed', 'Champ modifié'),
        ('child_added', 'Sous-service ajouté'),
        ('custom', 'Personnalisé'),
    ]

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES
    )

    user = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='service_activities'
    )

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    # Données de l'activité
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Détails de l'activité"
    )

    class Meta:
        db_table = 'services_activities'
        verbose_name = "Activité de service"
        verbose_name_plural = "Activités de service"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.service.reference}: {self.title}"


# ===============================
# 8. SERVICE COMMENT (Commentaires)
# ===============================

class ServiceComment(TimeStampedModel):
    """
    Commentaires sur un service
    """

    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    user = models.ForeignKey(
        BaseUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='service_comments'
    )

    content = models.TextField()

    # Commentaire parent (pour les réponses)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Fichiers attachés
    attachments = models.JSONField(
        default=list,
        blank=True
    )

    is_internal = models.BooleanField(
        default=False,
        help_text="Commentaire interne (non visible par le client)"
    )

    class Meta:
        db_table = 'services_comments'
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire sur {self.service.reference} par {self.user}"


# ===============================
# 9. SERVICE TEMPLATE (Templates)
# ===============================

class ServiceTemplate(TimeStampedModel):
    """
    Templates pré-configurés pour créer des services
    """

    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.CASCADE,
        related_name='templates'
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Valeurs pré-configurées
    default_field_values = models.JSONField(
        default=dict,
        help_text="Valeurs par défaut des champs"
    )

    default_title_template = models.CharField(
        max_length=500,
        blank=True,
        help_text="Template pour générer le titre (ex: 'Location {marque} {modele}')"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'services_templates'
        verbose_name = "Template de service"
        verbose_name_plural = "Templates de service"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.service_type.name})"
