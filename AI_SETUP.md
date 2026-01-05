# 🤖 Loura AI Setup Guide

## Quick Start (5 minutes)

### 1️⃣ Install Dependencies

```bash
cd /home/salim/Projets/loura/stack/backend
pip install -r requirements-ai.txt
```

### 2️⃣ Choose Your Provider

#### **Option A: Google Gemini** (RECOMMENDED ⭐)

**Why Gemini?**
- ✅ FREE tier (60 requests/minute)
- ✅ Excellent French support
- ✅ Great at function calling
- ✅ Fast and reliable

**Setup:**
```bash
# 1. Get API key from: https://makersuite.google.com/app/apikey
# 2. Add to .env:
echo "GOOGLE_API_KEY=your_key_here" >> .env
echo "AI_PROVIDER=gemini" >> .env
echo "AI_MODEL=gemini-1.5-flash" >> .env
```

**Test:**
```python
python manage.py shell
>>> from ai.provider_manager import ProviderManager
>>> manager = ProviderManager()
>>> # Should print: ✅ Auto-detected provider: gemini
```

---

#### **Option B: Ollama** (Local & Free 🆓)

**Why Ollama?**
- ✅ Completely FREE
- ✅ Works offline
- ✅ Privacy (data stays local)
- ⚠️ Requires 16GB RAM for best models

**Setup:**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download recommended model
ollama pull qwen2.5:14b  # Best for French + business data
# OR for lighter option:
ollama pull mistral:7b-instruct-v0.3

# 3. Configure
echo "AI_PROVIDER=ollama" >> .env
echo "AI_MODEL=qwen2.5:14b" >> .env

# 4. Start Ollama service
ollama serve
```

**Test:**
```bash
ollama run qwen2.5:14b
>>> Bonjour, tu es l'assistant IA de Loura
```

---

#### **Option C: OpenAI GPT** (Paid 💰)

```bash
# 1. Get API key from: https://platform.openai.com/api-keys
# 2. Add to .env:
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "AI_PROVIDER=openai" >> .env
echo "AI_MODEL=gpt-4o-mini" >> .env  # Most affordable
```

**Pricing:**
- GPT-4o-mini: ~$0.15 / 1M input tokens
- GPT-4o: ~$2.50 / 1M input tokens

---

#### **Option D: Anthropic Claude** (Paid 💰)

```bash
# 1. Get API key from: https://console.anthropic.com/
# 2. Add to .env:
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
echo "AI_PROVIDER=anthropic" >> .env
echo "AI_MODEL=claude-3-5-haiku-20241022" >> .env  # Fastest & cheapest
```

**Pricing:**
- Claude 3.5 Haiku: ~$0.25 / 1M tokens
- Claude 3.5 Sonnet: ~$3.00 / 1M tokens

---

## 3️⃣ Configuration (.env file)

Copy and edit `.env.example`:

```bash
cp .env.example .env
nano .env
```

**Minimum required:**
```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_api_key_here
```

**Full configuration:**
```env
# Provider
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash

# API Key
GOOGLE_API_KEY=AIzaSy...

# Settings (optional, defaults shown)
AI_TEMPERATURE=0.3          # 0.0 (precise) to 1.0 (creative)
AI_MAX_TOKENS=500           # Max response length
AI_CONCISE_MODE=true        # Force short responses
AI_USE_EMOJIS=true          # Use emojis 📊💰👥
AI_ENABLE_TOOLS=true        # Agent mode with data access
```

---

## 4️⃣ Testing

### Test Provider Connection

```python
python manage.py shell

from ai.provider_manager import ProviderManager

# Check available providers
manager = ProviderManager()
print(manager.list_available_providers())

# Test chat
from ai.providers.base import LLMMessage
messages = [LLMMessage(role="user", content="Bonjour")]
response = manager.chat(messages)
print(response.content)
```

### Test Agent with Tools

```python
from ai.agent_new import LouraAIAgent
from core.models import Organization

org = Organization.objects.first()
agent = LouraAIAgent(organization=org)

# Check provider
print(agent.get_provider_info())

# Test chat
response = agent.chat("Donne-moi les statistiques RH", agent_mode=True)
print(response["content"])
print(response["tool_results"])
```

---

## 5️⃣ Switching Providers

### At Runtime

```python
from ai.agent_new import LouraAIAgent

agent = LouraAIAgent(organization=org)

# Start with Gemini
print(agent.get_provider_info())  # {'provider': 'gemini', ...}

# Switch to Ollama
agent.switch_provider('ollama', 'qwen2.5:14b')
print(agent.get_provider_info())  # {'provider': 'ollama', ...}

# Switch to OpenAI
agent.switch_provider('openai', 'gpt-4o-mini')
```

### Via Environment Variable

```bash
# Switch to Ollama
export AI_PROVIDER=ollama
export AI_MODEL=qwen2.5:14b

# Restart Django
python manage.py runserver
```

---

## 🎯 Recommended Configurations

### **For Production (Best Quality)**

```env
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=500
```

**Cost:** FREE (60 req/min) or ~$0.07 / 1M tokens

---

### **For Development (Fast & Free)**

```env
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-flash
AI_TEMPERATURE=0.3
```

**Cost:** FREE (60 req/min)

---

### **For On-Premise / Privacy**

```env
AI_PROVIDER=ollama
AI_MODEL=qwen2.5:14b
AI_TEMPERATURE=0.3
```

**Cost:** FREE (requires 16GB RAM)

---

### **For Lightweight / Testing**

```env
AI_PROVIDER=ollama
AI_MODEL=mistral:7b-instruct-v0.3
AI_TEMPERATURE=0.3
```

**Cost:** FREE (works on 8GB RAM)

---

## 📊 Provider Comparison

| Provider | Cost | Speed | French | Function Calling | Setup |
|----------|------|-------|--------|------------------|-------|
| **Gemini** | FREE/Cheap | Fast | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5min |
| **Ollama** | FREE | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 10min |
| **OpenAI** | $$$ | Very Fast | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5min |
| **Claude** | $$$ | Fast | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 5min |

---

## 🔧 Troubleshooting

### "No LLM provider available"

```bash
# Check .env file exists
ls -la .env

# Check API key is set
echo $GOOGLE_API_KEY

# Or for Ollama:
ollama list  # Should show installed models
```

### "Gemini API non disponible"

```bash
# Install/update library
pip install --upgrade google-generativeai

# Test API key
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print(genai.list_models())"
```

### "Ollama not available"

```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# In another terminal:
ollama list
```

---

## 🚀 Next Steps

1. ✅ Choose and configure a provider
2. ✅ Test with `python manage.py shell`
3. ✅ Try the agent with real organization data
4. ✅ Optionally: Set up multiple providers for failover

---

## 💡 Tips

- **Use Gemini for FREE tier** - Best value for money
- **Use Ollama for privacy** - Data never leaves your server
- **Use GPT-4o-mini for production** - If budget allows
- **Keep AI_CONCISE_MODE=true** - Better UX with short responses
- **Set AI_TEMPERATURE=0.3** - More predictable for business data

---

## 📞 Support

- Gemini: https://ai.google.dev/docs
- Ollama: https://ollama.com/docs
- OpenAI: https://platform.openai.com/docs
- Anthropic: https://docs.anthropic.com/

---

**Ready to chat!** 🎉
