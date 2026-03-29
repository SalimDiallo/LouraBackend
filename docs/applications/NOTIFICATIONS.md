# NOTIFICATIONS - Documentation

## Vue d'ensemble

L'application **notifications** fournit un système de notifications interne pour Loura. Elle permet d'envoyer des notifications aux utilisateurs (AdminUser et Employee) avec différents types, priorités et préférences personnalisables.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/notifications/`
- **Modèles** : 2 modèles (Notification, NotificationPreference)
- **ViewSets** : 2 ViewSets
- **Endpoints** : ~15 endpoints
- **Dépendances** : `core` (Organization, BaseUser)

## Modèles de données

### Notification

**Description** : Notification interne envoyée à un utilisateur.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `recipient` (ForeignKey to BaseUser) : Destinataire (AdminUser ou Employee)
- `sender` (ForeignKey to BaseUser, nullable) : Expéditeur (None = système)
- `notification_type` (CharField) : Type (alert, system, user)
- `priority` (CharField) : Priorité (low, medium, high, critical)
- `title` (CharField) : Titre
- `message` (TextField) : Message
- `entity_type` (CharField) : Type d'entité liée (ex: product, order, employee)
- `entity_id` (CharField) : ID de l'entité liée
- `action_url` (CharField) : URL d'action (redirection)
- `is_read` (BooleanField) : Lue
- `read_at` (DateTimeField, nullable) : Date de lecture
- `created_at`, `updated_at` (DateTimeField) : Dates

**Relations** :
- ForeignKey vers `Organization`, `BaseUser` (recipient, sender)

**Méthodes importantes** :
- `mark_as_read()` : Marque la notification comme lue

**Types de notification** :
- **alert** : Alerte de stock ou autre alerte métier
- **system** : Message système (mise à jour, maintenance)
- **user** : Action d'un autre utilisateur (commentaire, assignation)

**Priorités** :
- **low** : Information
- **medium** : Avertissement
- **high** : Important
- **critical** : Urgent / Bloquant

### NotificationPreference

**Description** : Préférences de notification par utilisateur et organisation.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `user` (ForeignKey to BaseUser) : Utilisateur
- `receive_alerts` (BooleanField) : Recevoir les alertes (défaut: True)
- `receive_system` (BooleanField) : Recevoir les notifications système (défaut: True)
- `receive_user` (BooleanField) : Recevoir les notifications utilisateur (défaut: True)
- `min_priority` (CharField) : Priorité minimale (low, medium, high, critical) (défaut: low)

**Relations** :
- ForeignKey vers `Organization`, `BaseUser`

**Contrainte** : Unique ensemble (organization, user)

## API Endpoints

### NotificationViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/notifications/ | Liste des notifications | IsAuthenticated |
| POST | /api/notifications/ | Créer une notification | IsAuthenticated |
| GET | /api/notifications/{id}/ | Détails d'une notification | IsAuthenticated |
| PUT/PATCH | /api/notifications/{id}/ | Modifier une notification | IsAuthenticated |
| DELETE | /api/notifications/{id}/ | Supprimer une notification | IsAuthenticated |
| POST | /api/notifications/{id}/mark_read/ | Marquer comme lue | IsAuthenticated |
| POST | /api/notifications/mark_all_read/ | Marquer toutes comme lues | IsAuthenticated |
| GET | /api/notifications/unread_count/ | Nombre de non lues | IsAuthenticated |

**Filtres** : `notification_type`, `priority`, `is_read`

### NotificationPreferenceViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/notifications/preferences/ | Préférences de l'utilisateur | IsAuthenticated |
| POST | /api/notifications/preferences/ | Créer des préférences | IsAuthenticated |
| PUT/PATCH | /api/notifications/preferences/{id}/ | Modifier des préférences | IsAuthenticated |

## Exemples de requêtes

### Obtenir les notifications

**Request:**
```json
GET /api/notifications/?is_read=false
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "organization": "123e4567-e89b-12d3-a456-426614174001",
      "recipient": "123e4567-e89b-12d3-a456-426614174002",
      "sender": null,
      "notification_type": "alert",
      "priority": "high",
      "title": "Stock bas : Produit XYZ",
      "message": "Le produit XYZ est en stock bas (5 unités restantes)",
      "entity_type": "product",
      "entity_id": "123e4567-e89b-12d3-a456-426614174003",
      "action_url": "/inventory/products/123e4567-e89b-12d3-a456-426614174003",
      "is_read": false,
      "read_at": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "organization": "123e4567-e89b-12d3-a456-426614174001",
      "recipient": "123e4567-e89b-12d3-a456-426614174002",
      "sender": "123e4567-e89b-12d3-a456-426614174005",
      "notification_type": "user",
      "priority": "medium",
      "title": "Demande de congé approuvée",
      "message": "Votre demande de congé du 20 au 25 janvier a été approuvée",
      "entity_type": "leave_request",
      "entity_id": "123e4567-e89b-12d3-a456-426614174006",
      "action_url": "/hr/leave-requests/123e4567-e89b-12d3-a456-426614174006",
      "is_read": false,
      "read_at": null,
      "created_at": "2024-01-15T09:45:00Z",
      "updated_at": "2024-01-15T09:45:00Z"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174007",
      "organization": "123e4567-e89b-12d3-a456-426614174001",
      "recipient": "123e4567-e89b-12d3-a456-426614174002",
      "sender": null,
      "notification_type": "system",
      "priority": "low",
      "title": "Mise à jour système",
      "message": "Une nouvelle version de Loura est disponible",
      "entity_type": "",
      "entity_id": "",
      "action_url": "/settings/updates",
      "is_read": false,
      "read_at": null,
      "created_at": "2024-01-15T08:00:00Z",
      "updated_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

### Marquer une notification comme lue

**Request:**
```json
POST /api/notifications/{id}/mark_read/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "message": "Notification marquée comme lue",
  "notification": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "is_read": true,
    "read_at": "2024-01-15T11:00:00Z"
  }
}
```

### Marquer toutes les notifications comme lues

**Request:**
```json
POST /api/notifications/mark_all_read/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "message": "Toutes les notifications ont été marquées comme lues",
  "count": 3
}
```

### Obtenir le nombre de notifications non lues

**Request:**
```json
GET /api/notifications/unread_count/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "count": 3
}
```

### Obtenir/Modifier les préférences

**Request (GET):**
```json
GET /api/notifications/preferences/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174008",
  "organization": "123e4567-e89b-12d3-a456-426614174001",
  "user": "123e4567-e89b-12d3-a456-426614174002",
  "receive_alerts": true,
  "receive_system": true,
  "receive_user": true,
  "min_priority": "low",
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-10T08:00:00Z"
}
```

**Request (PATCH):**
```json
PATCH /api/notifications/preferences/{id}/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
{
  "receive_alerts": true,
  "receive_system": false,
  "min_priority": "medium"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174008",
  "organization": "123e4567-e89b-12d3-a456-426614174001",
  "user": "123e4567-e89b-12d3-a456-426614174002",
  "receive_alerts": true,
  "receive_system": false,
  "receive_user": true,
  "min_priority": "medium",
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T11:30:00Z"
}
```

## Serializers

- **NotificationSerializer** : Sérialisation complète des notifications
- **NotificationPreferenceSerializer** : Sérialisation des préférences

## Permissions

- **IsAuthenticated** : Toutes les actions nécessitent une authentification
- Filtrage automatique par organisation et recipient (l'utilisateur ne voit que ses propres notifications)

## Services/Utilities

- **notifications/services.py** : Service de création et d'envoi de notifications
- **notifications/signals.py** : Signaux Django pour la création automatique de notifications sur certains événements

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Notifications système** : Mises à jour, maintenance, annonces
2. **Alertes métier** : Stock bas, rupture, échéances, anomalies
3. **Notifications utilisateur** : Approbations, commentaires, assignations, mentions
4. **Préférences personnalisées** : Chaque utilisateur contrôle ce qu'il reçoit

### Création de notifications

Les notifications peuvent être créées :
- **Manuellement** : Via l'API (POST /api/notifications/)
- **Automatiquement** : Via des signaux Django ou des services métier
- **Par l'IA** : Via le mode agent de l'assistant IA

Exemple de création automatique :
```python
from notifications.services import NotificationService

NotificationService.create_notification(
    organization=organization,
    recipient=user,
    notification_type='alert',
    priority='high',
    title='Stock bas',
    message='Le produit XYZ est en stock bas',
    entity_type='product',
    entity_id=str(product.id),
    action_url=f'/inventory/products/{product.id}'
)
```

## Points d'attention

### Filtrage des notifications
- Les notifications sont automatiquement filtrées par `recipient` (l'utilisateur connecté)
- Chaque utilisateur ne voit que ses propres notifications

### Préférences par défaut
- Les préférences sont créées automatiquement à la première connexion
- Valeurs par défaut : recevoir tout, priorité minimale = low

### Lien générique vers les entités
- `entity_type` + `entity_id` permettent de lier une notification à n'importe quelle entité
- Évite les FK physiques et les imports circulaires
- Frontend utilise ces champs pour construire les liens de redirection

### Priorités et filtrage
- Les utilisateurs peuvent définir une priorité minimale
- Les notifications en dessous de cette priorité ne sont pas affichées (filtrées côté backend)

### Résolution des alertes
- Les alertes de stock sont automatiquement résolues lorsque le stock remonte
- La résolution est manuelle pour les autres types de notifications

### Performance
- Index sur `recipient` + `created_at` pour les requêtes fréquentes
- Index sur `organization` + `is_read` pour les statistiques

### Notifications en temps réel
- Pour les notifications en temps réel, utiliser WebSockets (Channels Django) ou SSE
- L'API actuelle est basée sur du polling (refresh périodique)
