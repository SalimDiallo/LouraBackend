# 🚀 Quick Start - Loura AI (2 minutes)

## Installation en 3 commandes

```bash
# 1. Installer les dépendances
cd /home/salim/Projets/loura/stack/backend
./install_ai.sh

# 2. Configurer Gemini (GRATUIT)
# Obtenir clé API: https://makersuite.google.com/app/apikey
echo "GOOGLE_API_KEY=votre_cle_ici" >> .env

# 3. Tester
python manage.py shell
```

## Test Rapide

```python
# Dans python manage.py shell

from ai.agent_new import LouraAIAgent
from core.models import Organization

# Obtenir une organisation
org = Organization.objects.first()

# Créer l'agent (auto-détecte Gemini)
agent = LouraAIAgent(organization=org)

# Vérifier le provider
print(agent.get_provider_info())
# {'provider': 'gemini', 'model': 'gemini-1.5-flash', ...}

# Test simple
response = agent.chat("Bonjour")
print(response["content"])

# Test avec données (Mode Agent)
response = agent.chat("Donne-moi les statistiques RH", agent_mode=True)
print(response["content"])
print(response["tool_results"])
```

## Changer de Provider

```python
# Passer à Ollama (local)
agent.switch_provider('ollama', 'qwen2.5:14b')

# Passer à OpenAI
agent.switch_provider('openai', 'gpt-4o-mini')

# Passer à Claude
agent.switch_provider('anthropic', 'claude-3-5-haiku-20241022')

# Retour à Gemini
agent.switch_provider('gemini', 'gemini-1.5-flash')
```

## Exemples de Questions

```python
# Stats RH
agent.chat("Combien d'employés avons-nous ?", agent_mode=True)
agent.chat("Qui est en congé cette semaine ?", agent_mode=True)

# Inventaire
agent.chat("Quels produits sont en rupture de stock ?", agent_mode=True)
agent.chat("Montre-moi les 10 produits les plus vendus", agent_mode=True)

# Finance
agent.chat("Bilan financier du mois", agent_mode=True)
agent.chat("Quels clients ont des dettes ?", agent_mode=True)

# Ventes
agent.chat("Statistiques de ventes sur 30 jours", agent_mode=True)
agent.chat("Top 5 des clients", agent_mode=True)
```

## Providers Disponibles

| Provider | Commande | Coût | Setup |
|----------|----------|------|-------|
| **Gemini** (Recommandé) | `agent.switch_provider('gemini')` | GRATUIT | 1min |
| **Ollama** (Local) | `agent.switch_provider('ollama')` | GRATUIT | 5min |
| **OpenAI** | `agent.switch_provider('openai')` | Payant | 1min |
| **Claude** | `agent.switch_provider('anthropic')` | Payant | 1min |

## Configuration .env

**Minimum (Gemini gratuit):**
```env
GOOGLE_API_KEY=votre_cle_ici
AI_PROVIDER=gemini
```

**Complet:**
```env
# Provider (auto|gemini|ollama|openai|anthropic)
AI_PROVIDER=auto
AI_MODEL=gemini-1.5-flash

# API Keys (au moins une)
GOOGLE_API_KEY=votre_cle_gemini
OPENAI_API_KEY=votre_cle_openai
ANTHROPIC_API_KEY=votre_cle_anthropic

# Settings
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=500
AI_CONCISE_MODE=true
```

## Troubleshooting

**"No provider available"**
```bash
# Vérifier .env
cat .env | grep API_KEY

# Installer dépendances
pip install google-generativeai
```

**"Gemini API error"**
```python
# Tester clé API
import google.generativeai as genai
genai.configure(api_key="votre_cle")
print(list(genai.list_models())[:3])
```

**"Ollama not found"**
```bash
# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger modèle
ollama pull qwen2.5:14b

# Démarrer service
ollama serve
```

## Documentation Complète

- **Setup détaillé:** `cat AI_SETUP.md`
- **Code examples:** `app/ai/examples/`
- **Providers:** `app/ai/providers/`

---

**C'est tout ! Votre IA est prête** 🎉

Recommandé pour démarrer: **Gemini** (gratuit, excellent en français)
