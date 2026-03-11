# Module Services - LouraTech

## Vue d'ensemble

Le module **Services** est le cœur métier de LouraTech. Il permet de gérer tous les types de services pour tous les secteurs d'activité avec une seule architecture générique et configurable.

### Principe clé
**Les données définissent le métier, pas le code.** Aucun service n'est codé en dur.

## Architecture

```
BusinessProfile (Secteur)
    ↓
ServiceType (Type de service)
    ↓
ServiceField (Champs dynamiques) + ServiceStatus (Statuts)
    ↓
Service (Service réel client)
    ↓
ServiceStatusHistory + ServiceActivity + ServiceComment
```

## Modèles de données

### 1. BusinessProfile
Définit le secteur d'activité de l'entreprise.

**Exemples**: BTP, Agence de voyage, Location automobile, Formation

**Champs principaux**:
- `name`: Nom du secteur
- `code`: Code unique
- `icon`, `color`: Personnalisation UI
- `settings`: Configuration JSON

### 2. ServiceType
Définit ce que l'entreprise vend.

**Exemples**: Location voiture, Projet BTP, Dossier voyage, Formation

**Champs principaux**:
- `business_profile`: Lien vers le secteur
- `name`, `code`: Identification
- `allow_nested_services`: Services dans des services
- `allowed_child_types`: Types de sous-services autorisés
- `has_pricing`: Activer la tarification
- `pricing_model`: fixed, hourly, daily, custom
- `requires_approval`: Workflow d'approbation
- `default_values`: Valeurs par défaut

### 3. ServiceField
Champs dynamiques configurables pour un type de service.

**Types de champs supportés**:
- `text`, `textarea`: Texte
- `number`, `decimal`, `currency`: Nombres
- `date`, `datetime`: Dates
- `boolean`: Oui/Non
- `select`, `multiselect`: Listes
- `file`, `image`: Fichiers
- `email`, `phone`, `url`: Formats spéciaux
- `user`: Référence utilisateur
- `relation`: Relation vers un autre service

**Configuration**:
- `is_required`: Obligatoire
- `is_unique`: Valeur unique
- `is_searchable`: Recherchable
- `is_visible_in_list`: Affiché dans les listes
- `validation_rules`: Règles de validation JSON
- `options`: Options pour select
- `order`: Ordre d'affichage

### 4. ServiceStatus
Statuts du cycle de vie d'un service.

**Exemples**:
- Location: Réservé → En cours → Terminé
- BTP: Étude → Planifié → En cours → Terminé
- Vente: Devis → Négociation → Payé → Livré

**Configuration**:
- `status_type`: initial, in_progress, completed, cancelled, on_hold
- `is_initial`: Statut par défaut
- `is_final`: Statut terminal
- `requires_comment`: Commentaire obligatoire
- `allowed_next_statuses`: Transitions autorisées
- `required_permission`: Permission requise

### 5. Service
Le service réel pour un client.

**Champs principaux**:
- `reference`: Auto-générée (ex: LOC-2024-00001)
- `title`: Titre descriptif
- `service_type`: Type de service
- `current_status`: Statut actuel
- `client_name`, `client_email`, `client_phone`: Infos client
- `client_user`: Si client dans le système
- `assigned_to`: Employé assigné
- `parent_service`: Service parent (si sous-service)
- `field_values`: Valeurs des champs dynamiques (JSON)
- `start_date`, `end_date`, `completed_at`: Dates
- `estimated_amount`, `actual_amount`, `currency`: Tarification
- `priority`: low, normal, high, urgent
- `tags`: Catégorisation
- `attachments`: Fichiers joints

### 6. ServiceStatusHistory
Historique des changements de statut avec commentaires.

### 7. ServiceActivity
Journal des activités:
- created, updated, status_changed
- assigned, comment_added, file_attached
- field_changed, child_added, custom

### 8. ServiceComment
Commentaires avec support de threads et pièces jointes.
- `is_internal`: Commentaires internes vs visibles client
- `parent_comment`: Réponses

### 9. ServiceTemplate
Templates pré-configurés pour créer rapidement des services.

## API Endpoints

### Business Profiles
```
GET    /api/services/business-profiles/
POST   /api/services/business-profiles/
GET    /api/services/business-profiles/{id}/
PUT    /api/services/business-profiles/{id}/
DELETE /api/services/business-profiles/{id}/
```

### Service Types
```
GET    /api/services/service-types/
POST   /api/services/service-types/
GET    /api/services/service-types/{id}/
PUT    /api/services/service-types/{id}/
DELETE /api/services/service-types/{id}/
GET    /api/services/service-types/{id}/fields/
GET    /api/services/service-types/{id}/statuses/
GET    /api/services/service-types/{id}/templates/
```

### Services
```
GET    /api/services/services/
POST   /api/services/services/
GET    /api/services/services/{id}/
PUT    /api/services/services/{id}/
PATCH  /api/services/services/{id}/
DELETE /api/services/services/{id}/

# Actions personnalisées
POST   /api/services/services/{id}/change_status/
GET    /api/services/services/{id}/activities/
GET    /api/services/services/{id}/comments/
POST   /api/services/services/{id}/comments/
GET    /api/services/services/{id}/history/
POST   /api/services/services/{id}/archive/
POST   /api/services/services/{id}/restore/
GET    /api/services/services/statistics/
```

### Service Fields
```
GET    /api/services/service-fields/
POST   /api/services/service-fields/
GET    /api/services/service-fields/{id}/
PUT    /api/services/service-fields/{id}/
DELETE /api/services/service-fields/{id}/
```

### Service Statuses
```
GET    /api/services/service-statuses/
POST   /api/services/service-statuses/
GET    /api/services/service-statuses/{id}/
PUT    /api/services/service-statuses/{id}/
DELETE /api/services/service-statuses/{id}/
```

### Templates
```
GET    /api/services/service-templates/
POST   /api/services/service-templates/
GET    /api/services/service-templates/{id}/
POST   /api/services/service-templates/{id}/create_service/
```

### Activities & Comments
```
GET    /api/services/service-activities/
GET    /api/services/service-comments/
POST   /api/services/service-comments/
```

## Exemples d'utilisation

### 1. Configuration: Location de véhicules

#### a. Créer le Business Profile
```json
POST /api/services/business-profiles/
{
  "name": "Location de véhicules",
  "code": "location-vehicules",
  "icon": "Car",
  "color": "#3B82F6"
}
```

#### b. Créer le Service Type
```json
POST /api/services/service-types/
{
  "business_profile": "{business_profile_id}",
  "name": "Location voiture",
  "code": "location-voiture",
  "allow_nested_services": false,
  "has_pricing": true,
  "pricing_model": "daily"
}
```

#### c. Créer les champs
```json
POST /api/services/service-fields/
[
  {
    "service_type": "{service_type_id}",
    "name": "Marque",
    "field_key": "marque",
    "field_type": "text",
    "is_required": true,
    "order": 1
  },
  {
    "service_type": "{service_type_id}",
    "name": "Modèle",
    "field_key": "modele",
    "field_type": "text",
    "is_required": true,
    "order": 2
  },
  {
    "service_type": "{service_type_id}",
    "name": "Date début",
    "field_key": "date_debut",
    "field_type": "date",
    "is_required": true,
    "order": 3
  },
  {
    "service_type": "{service_type_id}",
    "name": "Date fin",
    "field_key": "date_fin",
    "field_type": "date",
    "is_required": true,
    "order": 4
  }
]
```

#### d. Créer les statuts
```json
POST /api/services/service-statuses/
[
  {
    "service_type": "{service_type_id}",
    "name": "Réservé",
    "code": "reserved",
    "status_type": "initial",
    "is_initial": true,
    "color": "#F59E0B",
    "order": 1
  },
  {
    "service_type": "{service_type_id}",
    "name": "En cours",
    "code": "ongoing",
    "status_type": "in_progress",
    "color": "#3B82F6",
    "order": 2
  },
  {
    "service_type": "{service_type_id}",
    "name": "Terminé",
    "code": "completed",
    "status_type": "completed",
    "is_final": true,
    "color": "#10B981",
    "order": 3
  }
]
```

### 2. Créer un service

```json
POST /api/services/services/
{
  "service_type": "{service_type_id}",
  "title": "Location Toyota Prado - M. Diallo",
  "client_name": "Mamadou Diallo",
  "client_email": "m.diallo@example.com",
  "client_phone": "+224 622 00 00 00",
  "field_values": {
    "marque": "Toyota",
    "modele": "Prado",
    "date_debut": "2024-03-01",
    "date_fin": "2024-03-15"
  },
  "estimated_amount": "500000",
  "currency": "GNF",
  "priority": "normal"
}
```

### 3. Changer le statut

```json
POST /api/services/services/{service_id}/change_status/
{
  "new_status_id": "{status_id}",
  "comment": "Client a récupéré le véhicule"
}
```

### 4. Ajouter un commentaire

```json
POST /api/services/services/{service_id}/comments/
{
  "content": "Client a demandé une extension de 3 jours",
  "is_internal": false
}
```

## Fonctionnalités avancées

### Services imbriqués

Pour un projet BTP avec sous-services:

```json
// Service parent: Projet de construction
{
  "service_type": "projet-btp",
  "title": "Construction villa Conakry",
  "allow_nested_services": true
}

// Sous-service: Étude de sol
{
  "service_type": "etude-technique",
  "title": "Étude de sol",
  "parent_service": "{parent_service_id}"
}

// Sous-service: Fondations
{
  "service_type": "travaux-fondation",
  "title": "Travaux de fondation",
  "parent_service": "{parent_service_id}"
}
```

### Templates de service

```json
POST /api/services/service-templates/
{
  "service_type": "{service_type_id}",
  "name": "Location Standard",
  "default_field_values": {
    "assurance": "Complète",
    "kilometrage": "Illimité"
  },
  "default_title_template": "Location {marque} {modele}"
}

// Créer un service depuis le template
POST /api/services/service-templates/{template_id}/create_service/
{
  "client_name": "Jean Dupont",
  "field_values": {
    "marque": "Toyota",
    "modele": "Corolla"
  }
}
```

### Statistiques

```json
GET /api/services/services/statistics/

// Réponse
{
  "total": 156,
  "by_status": {
    "Réservé": { "count": 23, "color": "#F59E0B" },
    "En cours": { "count": 45, "color": "#3B82F6" },
    "Terminé": { "count": 88, "color": "#10B981" }
  },
  "by_priority": {
    "low": 12,
    "normal": 120,
    "high": 20,
    "urgent": 4
  },
  "by_service_type": {
    "Location voiture": 89,
    "Location moto": 45,
    "Location camion": 22
  }
}
```

## Filtres et recherche

Tous les endpoints supportent les filtres Django:

```
GET /api/services/services/?service_type={id}&current_status={id}&priority=high
GET /api/services/services/?search=Diallo
GET /api/services/services/?ordering=-created_at
GET /api/services/services/?start_date_from=2024-01-01&start_date_to=2024-12-31
GET /api/services/services/?parent_service=null  # Services racine uniquement
```

## Permissions

Tous les endpoints nécessitent une authentification JWT.
Les données sont automatiquement filtrées par organisation.

## Notes importantes

1. **Références auto-générées**: Format `{TYPE}-{YEAR}-{NUM}` (ex: LOC-2024-00001)
2. **Workflow de statuts**: Configurez les transitions autorisées via `allowed_next_statuses`
3. **Champs requis**: Les champs marqués `is_required=True` sont validés à la création
4. **Historique complet**: Tous les changements sont tracés automatiquement
5. **Multi-organisation**: Isolation totale des données par organisation

## Évolutivité

Ce module est conçu pour:
- Ajouter de nouveaux secteurs sans modifier le code
- Créer des types de services illimités
- Adapter les champs selon les besoins métier
- Gérer n'importe quel workflow
- Supporter les services complexes avec hiérarchies

**LouraTech n'est pas un logiciel par métier, c'est une plateforme métier configurable.**
