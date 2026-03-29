# AI (Assistant IA) - Documentation

## Vue d'ensemble

L'application **ai** fournit un assistant conversationnel IA pour les utilisateurs de Loura. Elle gère les conversations, les messages, les exécutions d'outils (mode agent) et le feedback utilisateur.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/ai/`
- **Modèles** : 3 modèles (Conversation, Message, AIToolExecution)
- **ViewSets** : ~2 ViewSets
- **Endpoints** : ~10 endpoints
- **Dépendances** : `core` (Organization, BaseUser), `hr` (Employee)

## Modèles de données

### Conversation

**Description** : Conversation avec l'assistant IA.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `user` (ForeignKey to BaseUser, nullable) : Utilisateur (AdminUser ou Employee)
- `employee` (ForeignKey to Employee, nullable) : Employé (duplicate pour référence directe)
- `title` (CharField) : Titre de la conversation (défaut: "Nouvelle conversation")
- `is_agent_mode` (BooleanField) : Mode agent activé (actions automatiques)
- `is_active` (BooleanField) : Conversation active
- `created_at`, `updated_at` (DateTimeField) : Dates

**Relations** :
- ForeignKey vers `Organization`, `BaseUser`, `Employee`
- OneToMany avec `Message` (messages de la conversation)

### Message

**Description** : Message dans une conversation.

**Champs principaux** :
- `conversation` (ForeignKey) : Conversation
- `role` (CharField) : Rôle (user, assistant, system)
- `content` (TextField) : Contenu du message
- `feedback` (CharField, nullable) : Feedback (like, dislike)
- `tool_calls` (JSONField, nullable) : Actions exécutées (mode agent)
- `tool_results` (JSONField, nullable) : Résultats des actions (mode agent)
- `tokens_used` (IntegerField) : Nombre de tokens utilisés
- `response_time_ms` (IntegerField) : Temps de réponse en ms
- `created_at` (DateTimeField) : Date de création

**Relations** :
- ForeignKey vers `Conversation`
- OneToMany avec `AIToolExecution` (exécutions d'outils)

### AIToolExecution

**Description** : Log d'exécution d'un outil par l'agent IA.

**Champs principaux** :
- `message` (ForeignKey) : Message associé
- `tool_name` (CharField) : Nom de l'outil
- `tool_input` (JSONField) : Paramètres d'entrée
- `tool_output` (JSONField, nullable) : Résultat de l'exécution
- `status` (CharField) : Statut (pending, running, success, error)
- `error_message` (TextField, nullable) : Message d'erreur
- `execution_time_ms` (IntegerField) : Temps d'exécution en ms
- `created_at` (DateTimeField) : Date de création

**Relations** :
- ForeignKey vers `Message`

## API Endpoints

### ConversationViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/ai/conversations/ | Liste des conversations | IsAuthenticated |
| POST | /api/ai/conversations/ | Créer une conversation | IsAuthenticated |
| GET | /api/ai/conversations/{id}/ | Détails d'une conversation | IsAuthenticated |
| PUT/PATCH | /api/ai/conversations/{id}/ | Modifier une conversation | IsAuthenticated |
| DELETE | /api/ai/conversations/{id}/ | Supprimer une conversation | IsAuthenticated |
| POST | /api/ai/conversations/{id}/send_message/ | Envoyer un message | IsAuthenticated |
| POST | /api/ai/conversations/{id}/feedback/ | Donner un feedback | IsAuthenticated |

### MessageViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/ai/messages/ | Liste des messages | IsAuthenticated |
| GET | /api/ai/messages/{id}/ | Détails d'un message | IsAuthenticated |

## Exemples de requêtes

### Créer une conversation

**Request:**
```json
POST /api/ai/conversations/
{
  "title": "Aide sur les congés",
  "is_agent_mode": false
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "organization": "123e4567-e89b-12d3-a456-426614174001",
  "user": "123e4567-e89b-12d3-a456-426614174002",
  "title": "Aide sur les congés",
  "is_agent_mode": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Envoyer un message

**Request:**
```json
POST /api/ai/conversations/{id}/send_message/
{
  "content": "Comment faire une demande de congé ?"
}
```

**Response:**
```json
{
  "message": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "conversation": "123e4567-e89b-12d3-a456-426614174000",
    "role": "user",
    "content": "Comment faire une demande de congé ?",
    "feedback": null,
    "tokens_used": 0,
    "response_time_ms": 0,
    "created_at": "2024-01-15T10:31:00Z"
  },
  "assistant_message": {
    "id": "123e4567-e89b-12d3-a456-426614174004",
    "conversation": "123e4567-e89b-12d3-a456-426614174000",
    "role": "assistant",
    "content": "Pour faire une demande de congé, rendez-vous dans le module RH...",
    "feedback": null,
    "tool_calls": null,
    "tool_results": null,
    "tokens_used": 150,
    "response_time_ms": 1200,
    "created_at": "2024-01-15T10:31:01Z"
  }
}
```

### Donner un feedback

**Request:**
```json
POST /api/ai/conversations/{id}/feedback/
{
  "message_id": "123e4567-e89b-12d3-a456-426614174004",
  "feedback": "like"
}
```

**Response:**
```json
{
  "message": "Feedback enregistré",
  "message_id": "123e4567-e89b-12d3-a456-426614174004",
  "feedback": "like"
}
```

## Serializers

- **ConversationSerializer** : Sérialisation complète des conversations avec messages
- **MessageSerializer** : Sérialisation des messages
- **AIToolExecutionSerializer** : Sérialisation des exécutions d'outils

## Permissions

- **IsAuthenticated** : Toutes les actions nécessitent une authentification
- Filtrage automatique par organisation de l'utilisateur

## Services/Utilities

- **ai/ai_service.py** : Service de communication avec l'API IA (OpenAI, Anthropic, Gemini, etc.)
- **ai/tools.py** : Définition des outils disponibles pour le mode agent
- **ai/prompts.py** : Templates de prompts système

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Assistant conversationnel** : Réponses aux questions des utilisateurs sur l'utilisation de Loura
2. **Mode agent** : Actions automatiques (créer un employé, faire un pointage, etc.)
3. **Feedback utilisateur** : Amélioration continue via like/dislike
4. **Historique des conversations** : Suivi des interactions pour chaque utilisateur

### Mode agent

Le mode agent permet à l'IA d'exécuter des actions automatiques :
- Créer/modifier des entités (employés, produits, ventes, etc.)
- Rechercher des informations
- Générer des rapports
- Effectuer des calculs

Les outils disponibles sont définis dans `ai/tools.py` et leurs exécutions sont loggées dans `AIToolExecution`.

## Points d'attention

### Filtrage par organisation
- Toutes les conversations sont filtrées par l'organisation de l'utilisateur
- L'IA n'a accès qu'aux données de l'organisation de l'utilisateur

### Gestion des tokens
- Le champ `tokens_used` permet de suivre la consommation
- Utile pour la facturation ou les limites d'utilisation

### Mode agent vs mode assistant
- **Mode assistant** : Réponses textuelles uniquement
- **Mode agent** : Peut exécuter des actions via des outils

### Feedback
- Le feedback (like/dislike) est enregistré sur le message de l'assistant
- Permet d'améliorer la qualité des réponses

### Performance
- Le champ `response_time_ms` permet de surveiller les performances
- Les requêtes longues peuvent nécessiter une optimisation

### Sécurité
- Les outils du mode agent doivent valider les permissions de l'utilisateur
- Les actions critiques nécessitent une confirmation explicite
