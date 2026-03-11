#!/bin/bash

# ========================================
# Loura AI Installation Script
# ========================================

set -e  # Exit on error

echo "🤖 Installing Loura AI Components..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+  "
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"

# Install AI dependencies
echo ""
echo -e "${BLUE}Installing AI dependencies...${NC}"
pip install -r requirements-ai.txt

echo ""
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup .env
echo ""
echo -e "${BLUE}Configuring environment...${NC}"

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
else
    echo -e "${YELLOW}✓ .env file already exists${NC}"
fi

# Detect available providers
echo ""
echo -e "${BLUE}Detecting available providers...${NC}"

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    if ollama list &> /dev/null; then
        echo "  Models: $(ollama list | tail -n +2 | awk '{print $1}' | tr '\n' ' ')"
    fi
else
    echo -e "${YELLOW}○ Ollama not installed (optional)${NC}"
    echo "  Install with: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Check API keys
if grep -q "GOOGLE_API_KEY=your_" .env 2>/dev/null; then
    echo -e "${YELLOW}○ Gemini API key not configured${NC}"
    echo "  Get key from: https://makersuite.google.com/app/apikey"
else
    if grep -q "GOOGLE_API_KEY=" .env 2>/dev/null; then
        echo -e "${GREEN}✓ Gemini API key configured${NC}"
    fi
fi

if grep -q "OPENAI_API_KEY=" .env 2>/dev/null && ! grep -q "OPENAI_API_KEY=your_" .env; then
    echo -e "${GREEN}✓ OpenAI API key configured${NC}"
fi

if grep -q "ANTHROPIC_API_KEY=" .env 2>/dev/null && ! grep -q "ANTHROPIC_API_KEY=your_" .env; then
    echo -e "${GREEN}✓ Anthropic API key configured${NC}"
fi

# Test installation
echo ""
echo -e "${BLUE}Testing installation...${NC}"

python3 << 'PYTHON_TEST'
try:
    # Test imports
    from ai.provider_manager import ProviderManager
    from ai.config import ai_config

    # Test provider detection
    manager = ProviderManager()
    providers = manager.list_available_providers()

    print("\n📊 Available Providers:")
    for p in providers:
        status = "✅" if p['available'] else "❌"
        current = " (CURRENT)" if p['is_current'] else ""
        print(f"  {status} {p['provider']}: {p['default_model']}{current}")

    if manager.current_provider:
        print(f"\n✅ AI System Ready!")
        print(f"   Provider: {manager.current_provider_type.value}")
        print(f"   Model: {manager.current_provider.model}")
    else:
        print("\n⚠️  No provider available yet.")
        print("   Please configure an API key in .env")

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    print("   Please check your installation")
    exit(1)
PYTHON_TEST

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API key"
echo "2. Run: python manage.py shell"
echo "3. Test: from ai.agent_new import LouraAIAgent"
echo ""
echo "Documentation: cat AI_SETUP.md"
echo ""
