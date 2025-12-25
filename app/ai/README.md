# Module AI - Assistant IA Loura

## Vue d'ensemble

Ce module fournit un assistant IA intégré à l'application Loura, utilisant des modèles de langage locaux via Ollama.

## Prérequis

### Installation d'Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Démarrer le service
ollama serve

# Télécharger un modèle
ollama pull llama3.2
# ou
ollama pull mistral
ollama pull phi3
```

### Dépendances Python

```bash
pip install ollama
```

## Architecture

```
backend/app/ai/
├── __init__.py
├── admin.py          # Configuration admin Django
├── agent.py          # Service Agent IA avec outils métier
├── apps.py
├── models.py         # Modèles Conversation, Message, AIToolExecution
├── serializers.py    # Serializers DRF
├── urls.py           # Routes API
└── views.py          # Views et endpoints
```

## API Endpoints

### Chat
- `POST /api/ai/chat/` - Envoyer un message à l'IA

**Request:**
```json
{
  "message": "Combien d'employés actifs ?",
  "agent_mode": false,
  "conversation_id": "uuid-optional"
}
```

**Headers:**
```
X-Organization-Subdomain: mon-org
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "content": "📊 Vous avez actuellement 15 employés actifs...",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "tool_calls": [],
  "tool_results": [],
  "response_time_ms": 1234,
  "model": "llama3.2"
}
```

### Conversations
- `GET /api/ai/conversations/` - Lister les conversations
- `GET /api/ai/conversations/{id}/` - Détails d'une conversation
- `DELETE /api/ai/conversations/{id}/` - Supprimer une conversation
- `DELETE /api/ai/conversations/{id}/clear/` - Vider les messages
- `POST /api/ai/conversations/{id}/feedback/` - Ajouter un feedback

### Modèles et Outils
- `GET /api/ai/models/` - Lister les modèles disponibles
- `GET /api/ai/tools/` - Lister les outils de l'agent

## Outils Disponibles (Mode Agent)

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `rechercher_employes` | Recherche d'employés | `query` |
| `statistiques_rh` | Stats RH de l'organisation | - |
| `liste_departements` | Liste les départements | - |
| `verifier_stock` | Vérifie le stock d'un produit | `product_name` |
| `conges_en_cours` | Employés en congé | - |
| `fiches_paie_recentes` | Fiches de paie récentes | `limit` |

## Mode Agent vs Mode Assistant

### Mode Assistant (par défaut)
- Répond aux questions de manière conversationnelle
- Ne peut pas exécuter d'actions
- Idéal pour l'aide et les explications

### Mode Agent
- Peut exécuter des actions automatiquement
- Utilise les outils pour interroger les données
- Peut effectuer des modifications (avec permissions)

## Configuration

### Modèle par défaut

Dans `agent.py`:
```python
class LouraAIAgent:
    DEFAULT_MODEL = "llama3.2"  # Changer ici
```

### Personnaliser les prompts système

```python
SYSTEM_PROMPT = """Tu es l'assistant IA de Loura..."""
AGENT_SYSTEM_PROMPT = """Tu es l'agent IA autonome..."""
```

## Frontend

Le composant `ChatSidebar` (`components/core/chat-sidebar.tsx`) gère l'interface utilisateur du chat.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `open` | boolean | Afficher/masquer le sidebar |
| `onClose` | () => void | Callback de fermeture |
| `orgSlug` | string | Slug de l'organisation |

### Service Frontend

```typescript
import { aiService } from "@/lib/services/ai";

// Envoyer un message
const response = await aiService.chat("mon-org", {
  message: "Bonjour!",
  agent_mode: false,
});

// Lister les modèles
const models = await aiService.getModels();
```

## Modèles Recommandés

| Modèle | Taille | RAM | Utilisation |
|--------|--------|-----|-------------|
| `phi3` | 3.8B | 4GB | Rapide, léger |
| `llama3.2` | 8B | 8GB | Équilibré |
| `mistral` | 7B | 8GB | Polyvalent |
| `qwen2` | 7B | 8GB | Bon en français |

## Dépannage

### Ollama non disponible
```
Erreur: Le modèle IA local (Ollama) n'est pas disponible
```
**Solution:** Vérifiez que `ollama serve` est en cours d'exécution.

### Modèle non trouvé
```
Erreur: model not found
```
**Solution:** Téléchargez le modèle avec `ollama pull <nom>`.

### Mémoire insuffisante
**Solution:** Utilisez un modèle plus petit comme `phi3`.
