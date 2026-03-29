# SERVICES - Documentation

## Vue d'ensemble

L'application **services** est un module générique et hautement configurable pour la gestion de tout type de service. Elle permet de créer des profils métier (secteurs d'activité) avec des types de services personnalisés, des champs dynamiques, des statuts configurables et des services imbriqués. Architecture modulaire et data-driven.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/services/`
- **Modèles** : 9 modèles (BusinessProfile, ServiceType, ServiceField, ServiceStatus, Service, ServiceStatusHistory, ServiceActivity, ServiceComment, ServiceTemplate)
- **ViewSets** : ~9 ViewSets
- **Endpoints** : ~60 endpoints
- **Dépendances** : `core` (Organization, BaseUser)

**Schéma d'architecture** :
```
BusinessProfile → ServiceType → ServiceField/ServiceStatus → Service
```

## Modèles de données

### BusinessProfile

**Description** : Profil métier / Secteur d'activité (ex: BTP, Voyage, Automobile, Formation).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom du secteur
- `code` (SlugField) : Code unique
- `description` (TextField) : Description
- `icon` (CharField) : Icône pour l'interface (ex: Building, Car, Plane)
- `color` (CharField) : Couleur hexadécimale pour l'UI (défaut: #3B82F6)
- `is_active` (BooleanField) : Profil actif
- `settings` (JSONField) : Configuration spécifique au métier

**Relations** :
- ForeignKey vers `Organization`
- OneToMany avec `ServiceType` (types de services du profil)

### ServiceType

**Description** : Type de service proposé (ex: Location voiture, Projet BTP, Dossier voyage).

**Champs principaux** :
- `business_profile` (ForeignKey) : Profil métier
- `name` (CharField) : Nom du type de service
- `code` (SlugField) : Code unique
- `description` (TextField) : Description
- `icon`, `color` (CharField) : Icône et couleur pour l'UI
- `requires_approval` (BooleanField) : Nécessite approbation
- `allow_nested_services` (BooleanField) : Peut contenir des sous-services
- `allowed_child_types` (ManyToMany to self) : Types de services autorisés en sous-services
- `has_pricing` (BooleanField) : Système de tarification
- `pricing_model` (CharField) : Modèle (fixed, hourly, daily, custom)
- `is_active` (BooleanField) : Type actif
- `default_values` (JSONField) : Valeurs par défaut pour les champs
- `settings` (JSONField) : Configuration spécifique

**Relations** :
- ForeignKey vers `BusinessProfile`
- ManyToMany avec `ServiceType` (allowed_child_types)
- OneToMany avec `ServiceField`, `ServiceStatus`, `Service`, `ServiceTemplate`

**Propriété** :
- `organization` : Retourne l'organisation via business_profile.organization

### ServiceField

**Description** : Champ dynamique pour un type de service (ex: Marque, Modèle, Date début, Prix).

**Champs principaux** :
- `service_type` (ForeignKey) : Type de service
- `name` (CharField) : Nom du champ (affiché)
- `field_key` (SlugField) : Clé unique pour stockage
- `field_type` (CharField) : Type (text, textarea, number, decimal, date, datetime, boolean, select, multiselect, file, image, email, phone, url, currency, user, relation)
- `description` (TextField) : Description ou aide
- `is_required`, `is_unique`, `is_searchable`, `is_visible_in_list` (BooleanField) : Configuration
- `order` (IntegerField) : Ordre d'affichage
- `default_value` (TextField) : Valeur par défaut
- `validation_rules` (JSONField) : Règles de validation (min, max, pattern, etc.)
- `options` (JSONField) : Options pour select/multiselect
- `settings` (JSONField) : Configuration avancée (unité, format, etc.)
- `is_active` (BooleanField) : Champ actif

**Types de champs supportés** :
- **Texte** : text, textarea, email, phone, url
- **Nombre** : number, decimal, currency
- **Date** : date, datetime
- **Booléen** : boolean
- **Sélection** : select, multiselect
- **Fichiers** : file, image
- **Relations** : user, relation (vers un autre service)

### ServiceStatus

**Description** : Statut du cycle de vie d'un service (ex: Réservé, En cours, Terminé, Annulé).

**Champs principaux** :
- `service_type` (ForeignKey) : Type de service
- `name` (CharField) : Nom du statut
- `code` (SlugField) : Code unique
- `description` (TextField) : Description
- `color` (CharField) : Couleur pour l'affichage (défaut: #6B7280)
- `icon` (CharField) : Icône
- `order` (IntegerField) : Ordre dans le workflow
- `status_type` (CharField) : Type (initial, in_progress, completed, cancelled, on_hold)
- `is_initial` (BooleanField) : Statut par défaut à la création
- `is_final` (BooleanField) : Statut final (terminé ou annulé)
- `requires_comment` (BooleanField) : Nécessite un commentaire lors du passage
- `allowed_next_statuses` (ManyToMany to self) : Statuts suivants autorisés
- `required_permission` (CharField) : Permission requise pour passer à ce statut
- `is_active` (BooleanField) : Statut actif

**Workflow** :
- Les transitions entre statuts sont définies via `allowed_next_statuses`
- Les statuts initiaux (`is_initial=True`) sont utilisés à la création
- Les statuts finaux (`is_final=True`) marquent la fin du cycle de vie

### Service

**Description** : Service réel pour un client (ex: Location Prado pour M. Diallo).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `service_type` (ForeignKey) : Type de service
- `reference` (CharField, unique) : Référence unique (ex: SRV-2024-001)
- `title` (CharField) : Titre descriptif
- `description` (TextField) : Description
- `client_type` (CharField) : Type de client (individual, company)
- `client_name`, `client_email`, `client_phone` (CharField) : Informations client
- `client_user` (ForeignKey to BaseUser, nullable) : Client utilisateur du système
- `assigned_to` (ForeignKey to BaseUser, nullable) : Employé assigné
- `parent_service` (ForeignKey to self, nullable) : Service parent (services imbriqués)
- `current_status` (ForeignKey to ServiceStatus) : Statut actuel
- `field_values` (JSONField) : Valeurs des champs dynamiques
- `start_date`, `end_date`, `completed_at` (DateField/DateTimeField) : Dates
- `estimated_amount`, `actual_amount` (DecimalField) : Montants
- `currency` (CharField) : Devise (défaut: MAD)
- `priority` (CharField) : Priorité (low, normal, high, urgent)
- `tags` (JSONField) : Tags pour catégorisation
- `metadata` (JSONField) : Données additionnelles
- `attachments` (JSONField) : Liste des fichiers attachés
- `is_archived` (BooleanField) : Service archivé

**Relations** :
- ForeignKey vers `Organization`, `ServiceType`, `BaseUser` (client_user, assigned_to), `Service` (parent), `ServiceStatus`
- OneToMany avec `Service` (child_services), `ServiceStatusHistory`, `ServiceActivity`, `ServiceComment`

**Méthodes importantes** :
- `save()` : Auto-génère la référence si non fournie
- `generate_reference()` : Génère une référence unique (format: {PREFIX}-{YEAR}-{NUMBER})

### ServiceStatusHistory

**Description** : Historique des changements de statut d'un service.

**Champs principaux** :
- `service` (ForeignKey) : Service
- `from_status` (ForeignKey to ServiceStatus, nullable) : Statut d'origine
- `to_status` (ForeignKey to ServiceStatus) : Statut de destination
- `changed_by` (ForeignKey to BaseUser, nullable) : Utilisateur qui a changé
- `comment` (TextField) : Commentaire
- `metadata` (JSONField) : Données additionnelles sur le changement

### ServiceActivity

**Description** : Journal d'activités sur un service.

**Champs principaux** :
- `service` (ForeignKey) : Service
- `activity_type` (CharField) : Type (created, updated, status_changed, assigned, comment_added, file_attached, field_changed, child_added, custom)
- `user` (ForeignKey to BaseUser, nullable) : Utilisateur
- `title` (CharField) : Titre
- `description` (TextField) : Description
- `data` (JSONField) : Détails de l'activité

### ServiceComment

**Description** : Commentaires sur un service.

**Champs principaux** :
- `service` (ForeignKey) : Service
- `user` (ForeignKey to BaseUser, nullable) : Utilisateur
- `content` (TextField) : Contenu du commentaire
- `parent_comment` (ForeignKey to self, nullable) : Commentaire parent (réponses)
- `attachments` (JSONField) : Fichiers attachés
- `is_internal` (BooleanField) : Commentaire interne (non visible par le client)

### ServiceTemplate

**Description** : Templates pré-configurés pour créer des services.

**Champs principaux** :
- `service_type` (ForeignKey) : Type de service
- `name` (CharField) : Nom du template
- `description` (TextField) : Description
- `default_field_values` (JSONField) : Valeurs par défaut des champs
- `default_title_template` (CharField) : Template pour générer le titre (ex: 'Location {marque} {modele}')
- `is_active` (BooleanField) : Template actif

## API Endpoints

### BusinessProfileViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/services/business-profiles/ | Liste des profils métier | IsAuthenticated |
| POST | /api/services/business-profiles/ | Créer un profil | IsAuthenticated |
| GET | /api/services/business-profiles/{id}/ | Détails | IsAuthenticated |
| PUT/PATCH | /api/services/business-profiles/{id}/ | Modifier | IsAuthenticated |
| DELETE | /api/services/business-profiles/{id}/ | Supprimer | IsAuthenticated |

### ServiceTypeViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/services/service-types/ | Liste des types | IsAuthenticated |
| POST | /api/services/service-types/ | Créer un type | IsAuthenticated |
| GET | /api/services/service-types/{id}/ | Détails | IsAuthenticated |
| PUT/PATCH | /api/services/service-types/{id}/ | Modifier | IsAuthenticated |
| DELETE | /api/services/service-types/{id}/ | Supprimer | IsAuthenticated |

### ServiceFieldViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/services/service-fields/ | Liste des champs | IsAuthenticated |
| POST | /api/services/service-fields/ | Créer un champ | IsAuthenticated |
| GET | /api/services/service-fields/{id}/ | Détails | IsAuthenticated |
| PUT/PATCH | /api/services/service-fields/{id}/ | Modifier | IsAuthenticated |
| DELETE | /api/services/service-fields/{id}/ | Supprimer | IsAuthenticated |

### ServiceStatusViewSet

Endpoints CRUD standards similaires aux ViewSets ci-dessus.

### ServiceViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/services/services/ | Liste des services | IsAuthenticated |
| POST | /api/services/services/ | Créer un service | IsAuthenticated |
| GET | /api/services/services/{id}/ | Détails | IsAuthenticated |
| PUT/PATCH | /api/services/services/{id}/ | Modifier | IsAuthenticated |
| DELETE | /api/services/services/{id}/ | Supprimer | IsAuthenticated |
| POST | /api/services/services/{id}/change_status/ | Changer le statut | IsAuthenticated |
| POST | /api/services/services/{id}/add_comment/ | Ajouter un commentaire | IsAuthenticated |
| POST | /api/services/services/{id}/assign/ | Assigner à un utilisateur | IsAuthenticated |

**Filtres** : `service_type`, `current_status`, `assigned_to`, `client_name`, `start_date`, `end_date`, `priority`, `is_archived`

### ServiceTemplateViewSet

Endpoints CRUD standards pour les templates.

## Exemples de requêtes

### Créer un profil métier

**Request:**
```json
POST /api/services/business-profiles/
{
  "name": "Location de véhicules",
  "code": "location-vehicules",
  "description": "Gestion de location de véhicules",
  "icon": "Car",
  "color": "#10B981",
  "settings": {
    "enable_insurance": true,
    "default_currency": "GNF"
  }
}
```

### Créer un type de service

**Request:**
```json
POST /api/services/service-types/
{
  "business_profile": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Location voiture",
  "code": "location-voiture",
  "description": "Location de voiture courte/longue durée",
  "icon": "Car",
  "color": "#10B981",
  "requires_approval": false,
  "allow_nested_services": false,
  "has_pricing": true,
  "pricing_model": "daily"
}
```

### Créer un champ dynamique

**Request:**
```json
POST /api/services/service-fields/
{
  "service_type": "123e4567-e89b-12d3-a456-426614174001",
  "name": "Marque du véhicule",
  "field_key": "vehicle_brand",
  "field_type": "select",
  "description": "Marque du véhicule à louer",
  "is_required": true,
  "is_searchable": true,
  "is_visible_in_list": true,
  "order": 1,
  "options": [
    {"value": "toyota", "label": "Toyota"},
    {"value": "nissan", "label": "Nissan"},
    {"value": "mercedes", "label": "Mercedes"}
  ]
}
```

### Créer un service

**Request:**
```json
POST /api/services/services/
{
  "service_type": "123e4567-e89b-12d3-a456-426614174001",
  "title": "Location Toyota Prado - M. Diallo",
  "client_type": "individual",
  "client_name": "Mamadou Diallo",
  "client_email": "diallo@example.com",
  "client_phone": "+224622000000",
  "assigned_to": "123e4567-e89b-12d3-a456-426614174002",
  "field_values": {
    "vehicle_brand": "toyota",
    "vehicle_model": "Prado",
    "start_date": "2024-01-20",
    "end_date": "2024-01-27",
    "daily_rate": 250000
  },
  "start_date": "2024-01-20",
  "end_date": "2024-01-27",
  "estimated_amount": 1750000,
  "currency": "GNF",
  "priority": "normal"
}
```

## Serializers

- BusinessProfileSerializer, ServiceTypeSerializer, ServiceFieldSerializer, ServiceStatusSerializer
- ServiceSerializer, ServiceCreateSerializer, ServiceListSerializer
- ServiceStatusHistorySerializer, ServiceActivitySerializer, ServiceCommentSerializer, ServiceTemplateSerializer

## Permissions

- **IsAuthenticated** : Toutes les actions nécessitent une authentification
- Filtrage automatique par organisation

## Services/Utilities

Aucun service externe spécifique (logique métier dans les ViewSets et modèles).

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Multi-secteur** : Supporter différents secteurs d'activité dans une même organisation
2. **Configuration data-driven** : Définir des types de services avec champs et statuts personnalisés
3. **Services imbriqués** : Créer des hiérarchies de services (projet BTP avec sous-tâches)
4. **Workflow personnalisé** : Définir des workflows de statuts avec transitions autorisées
5. **Historique complet** : Traçabilité des changements de statut et activités
6. **Templates** : Accélérer la création de services via des templates pré-configurés

### Architecture data-driven

Le module services est conçu pour être entièrement configurable par données :
- Pas besoin de modifier le code pour ajouter un nouveau type de service
- Les champs sont définis dynamiquement via ServiceField
- Les statuts et workflows sont configurables via ServiceStatus
- Les valeurs des champs sont stockées dans le JSONField `field_values`

## Points d'attention

### Services imbriqués
- Activer `allow_nested_services` sur le ServiceType parent
- Définir les types de services autorisés via `allowed_child_types`
- Les services enfants sont liés via `parent_service`

### Champs dynamiques
- Les valeurs sont stockées dans `Service.field_values` (JSONField)
- La validation des champs se fait côté backend selon `validation_rules`
- Les champs de type `relation` permettent de lier des services entre eux

### Workflow de statuts
- Les transitions sont validées via `allowed_next_statuses`
- Les statuts finaux (`is_final=True`) ne peuvent plus être changés
- L'historique est automatiquement créé dans `ServiceStatusHistory`

### Références auto-générées
- Format : `{PREFIX}-{YEAR}-{NUMBER}` (ex: LOC-2024-00001)
- Le préfixe est basé sur le code du ServiceType (3 premiers caractères)
- La numérotation est incrémentale par organisation et type

### Pricing
- Configurable via `has_pricing` et `pricing_model`
- Les montants sont stockés dans `estimated_amount` et `actual_amount`
- Support de différentes devises via `currency`

### Templates
- Accélèrent la création de services avec valeurs pré-remplies
- Le `default_title_template` supporte les variables (ex: "Location {vehicle_brand} {vehicle_model}")
- Les variables sont remplacées par les valeurs de `field_values`

### Commentaires internes
- Les commentaires avec `is_internal=True` ne sont pas visibles par les clients
- Support des réponses via `parent_comment`

### Activités
- Automatiquement créées pour les actions importantes (création, changement de statut, etc.)
- Permettent de reconstituer l'historique complet d'un service
