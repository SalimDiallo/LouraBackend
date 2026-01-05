# Loura AI Integration - Complete Setup

## Summary

Your Loura AI system is now fully configured with **Google Gemini 2.5 Flash** and a multi-provider architecture allowing easy switching between AI models.

## What Has Been Implemented

### 1. Multi-Provider Architecture

Created a flexible provider system supporting 4 LLM providers:

- **Google Gemini** (ACTIVE - using your API key)
- **Ollama** (local open-source models)
- **OpenAI** (GPT models)
- **Anthropic** (Claude models)

### 2. Provider Files Created

#### Backend (`/home/salim/Projets/loura/stack/backend/app/ai/`)

- `providers/base.py` - Base interface for all providers
- `providers/gemini.py` - Google Gemini implementation (CONFIGURED)
- `providers/ollama.py` - Local models support
- `providers/openai.py` - GPT models support
- `providers/anthropic.py` - Claude models support
- `provider_manager.py` - Provider orchestration and switching
- `config.py` - Centralized configuration
- `agent_new.py` - New multi-provider agent

### 3. Configuration Files

- `requirements-ai.txt` - Python dependencies (updated with google-genai)
- `.env` - API keys and settings (CONFIGURED with your Gemini key)
- `.env.example` - Template for environment variables
- `install_ai.sh` - Automated installation script
- `AI_SETUP.md` - Complete setup guide
- `QUICKSTART_AI.md` - 2-minute quick start

### 4. Current Configuration

**Active Provider:** Google Gemini
**Model:** gemini-2.5-flash
**API Key:** Configured and tested (AIzaSyA_hu31_K8Oebbvxzgi5-jhg1qahc0iArE)
**Status:** ✅ Working

## Test Results

```
✅ Gemini API connection: SUCCESS
✅ Model gemini-2.5-flash: WORKING
✅ Chat responses: WORKING
✅ Provider switching: WORKING
```

## How to Use

### Quick Test

```bash
cd /home/salim/Projets/loura/stack/backend
source venv/bin/activate
python manage.py shell
```

```python
from ai.agent_new import LouraAIAgent
from core.models import Organization

# Get organization
org = Organization.objects.first()

# Create agent (auto-uses Gemini)
agent = LouraAIAgent(organization=org)

# Check provider
print(agent.get_provider_info())
# Output: {'provider': 'gemini', 'model': 'gemini-2.5-flash', 'available': True}

# Test chat
response = agent.chat("Bonjour")
print(response["content"])

# Test with business tools
response = agent.chat("Combien d'employés avons-nous ?", agent_mode=True)
print(response["content"])
print(response["tool_results"])
```

### Switch Providers

```python
# Switch to Ollama (local)
agent.switch_provider('ollama', 'qwen2.5:14b')

# Switch to OpenAI (requires OPENAI_API_KEY in .env)
agent.switch_provider('openai', 'gpt-4o-mini')

# Switch to Claude (requires ANTHROPIC_API_KEY in .env)
agent.switch_provider('anthropic', 'claude-3-5-haiku-20241022')

# Back to Gemini
agent.switch_provider('gemini', 'gemini-2.5-flash')
```

## Frontend Integration

The frontend is already configured to work with the AI backend:

**File:** `/home/salim/Projets/loura/stack/frontend/lourafrontend/lib/services/ai/ai.service.ts`

The chat interface will automatically use the configured backend provider (currently Gemini).

### Chat Features

- Streaming responses (Server-Sent Events)
- Tool execution with visualizations
- Conversation history
- Feedback system
- 45+ business tools for HR, inventory, sales, finance

### Data Visualizations

**File:** `/home/salim/Projets/loura/stack/frontend/lourafrontend/components/core/chat-data-display.tsx`

Supports 5 chart types:
- Bar charts (rankings, comparisons)
- Line charts (trends over time)
- Area charts (multi-metric trends)
- Pie charts (proportions)
- Comparison charts (multi-dimensional data)

## Available Models

### Gemini (Currently Active)

- `gemini-2.5-flash` (ACTIVE) - Fastest, best balance
- `gemini-2.5-pro` - More powerful, slower
- `gemini-2.0-flash` - Previous generation

### Ollama (Local - Free)

To use Ollama:

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull qwen2.5:14b

# Start service
ollama serve

# Update .env
AI_PROVIDER=ollama
AI_MODEL=qwen2.5:14b
```

### OpenAI (Paid)

To use OpenAI:

```bash
# Add to .env
OPENAI_API_KEY=your_key_here
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
```

### Anthropic (Paid)

To use Claude:

```bash
# Add to .env
ANTHROPIC_API_KEY=your_key_here
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-haiku-20241022
```

## Advanced Features (45+ Business Tools)

The AI agent has access to your business data through tools:

### HR Tools
- Employee statistics
- Department information
- Leave requests and balances
- Payroll data
- Attendance tracking

### Inventory Tools
- Product search and details
- Stock levels and movements
- Low stock alerts
- Category information

### Sales Tools
- Recent sales
- Sales statistics
- Top products
- Revenue analysis

### Finance Tools
- Financial summaries
- Client debts
- Expense tracking
- Invoices

### Example Queries

```python
# HR
agent.chat("Qui est en congé cette semaine ?", agent_mode=True)
agent.chat("Statistiques de paie du mois", agent_mode=True)

# Inventory
agent.chat("Produits en rupture de stock", agent_mode=True)
agent.chat("Top 10 produits vendus", agent_mode=True)

# Finance
agent.chat("Bilan financier du mois", agent_mode=True)
agent.chat("Clients avec des dettes", agent_mode=True)
```

## API Endpoints

All endpoints are available at `http://localhost:8000/api/ai/`:

- `POST /ai/chat/` - Send chat message
- `POST /ai/chat/stream/` - Stream chat response
- `GET /ai/models/` - List available models
- `GET /ai/tools/` - List available tools
- `GET /ai/conversations/` - List conversations
- `GET /ai/conversations/{id}/` - Get conversation details
- `DELETE /ai/conversations/{id}/` - Delete conversation
- `POST /ai/conversations/{id}/feedback/` - Add feedback

## Configuration Options (.env)

```env
# Provider Selection
AI_PROVIDER=gemini               # auto|gemini|ollama|openai|anthropic
AI_MODEL=gemini-2.5-flash       # Model name

# API Keys
GOOGLE_API_KEY=AIzaSyA_hu31_K8Oebbvxzgi5-jhg1qahc0iArE
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here

# AI Settings
AI_TEMPERATURE=0.3              # 0.0 (precise) to 1.0 (creative)
AI_MAX_TOKENS=500               # Max response length
AI_TIMEOUT=30                   # Request timeout (seconds)
AI_CONCISE_MODE=true            # Force concise responses
AI_USE_EMOJIS=true              # Use emojis in responses

# Tool/Function Calling
AI_ENABLE_TOOLS=true            # Enable agent mode
AI_MAX_TOOL_CALLS=5             # Max tools per request
```

## Troubleshooting

### "No provider available"

```bash
# Check .env file
cat .env | grep API_KEY

# Verify Gemini key
python -c "import os; print(os.getenv('GOOGLE_API_KEY'))"
```

### "Model not found"

Make sure you're using a supported model:
- Gemini: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`
- Not supported: `gemini-1.5-flash` (use 2.5 instead)

### Provider Switching

```python
# Check available providers
from ai.provider_manager import ProviderManager
manager = ProviderManager()
print(manager.list_available_providers())
```

## Next Steps

1. ✅ Start using the chat with Gemini
2. ✅ Test different business queries
3. ✅ Explore data visualizations in frontend
4. Optional: Set up additional providers (Ollama, OpenAI, Claude)
5. Optional: Integrate LangGraph for advanced workflows

## Documentation

- **Quick Start:** `cat QUICKSTART_AI.md`
- **Full Setup Guide:** `cat AI_SETUP.md`
- **Provider Code:** `app/ai/providers/`
- **Agent Code:** `app/ai/agent_new.py`
- **Example Queries:** `app/ai/examples/` (if created)

---

**Status:** ✅ FULLY OPERATIONAL

**Current Provider:** Google Gemini 2.5 Flash

**API Key:** Configured and tested

**Integration:** Backend ✅ | Frontend ✅ | Database ✅

Your Loura AI system is ready to use!
