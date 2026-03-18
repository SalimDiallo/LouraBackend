"""
AI Configuration - Multi-Provider (Claude & OpenAI)
"""
import os


class AIConfig:
    """
    AI Configuration - Multi-Provider Support (Claude prioritized, then OpenAI)

    Environment Variables:
        ANTHROPIC_API_KEY: Anthropic Claude API key (prioritized)
        OPENAI_API_KEY: OpenAI API key (fallback)
        AI_MODEL: Model name (auto-detected based on provider if not set)
        AI_TEMPERATURE: 0.0-1.0 (default: 0.3)
        AI_MAX_TOKENS: Max tokens to generate (default: 2048)
        AI_TIMEOUT: Request timeout in seconds (default: 60)
    """

    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

    # Auto-detect provider based on available keys (Claude first, then OpenAI)
    @classmethod
    def get_provider(cls) -> str:
        """Determine which AI provider to use based on available API keys."""
        if cls.ANTHROPIC_API_KEY:
            return 'anthropic'
        elif cls.OPENAI_API_KEY:
            return 'openai'
        return None

    @classmethod
    def get_default_model(cls) -> str:
        """Get default model based on provider."""
        provider = cls.get_provider()
        if provider == 'anthropic':
            return 'claude-3-5-sonnet-20240620'
        elif provider == 'openai':
            return 'gpt-4o-mini'
        return ''

    # Model (use env var or auto-detect based on provider)
    MODEL = os.getenv('AI_MODEL', '') or get_default_model.__func__(None)

    # Generation settings
    TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.3'))
    MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '2048'))
    TIMEOUT = int(os.getenv('AI_TIMEOUT', '60'))

    # Response settings
    LANGUAGE = os.getenv('AI_LANGUAGE', 'fr')

    # Tool/Function calling
    ENABLE_TOOLS = os.getenv('AI_ENABLE_TOOLS', 'true').lower() == 'true'
    MAX_TOOL_CALLS = int(os.getenv('AI_MAX_TOOL_CALLS', '10'))

    @classmethod
    def get_config(cls) -> dict:
        provider = cls.get_provider()
        return {
            'provider': provider,
            'model': cls.MODEL or cls.get_default_model(),
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'timeout': cls.TIMEOUT,
            'has_api_key': bool(cls.ANTHROPIC_API_KEY or cls.OPENAI_API_KEY),
        }

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.ANTHROPIC_API_KEY or cls.OPENAI_API_KEY)

    @classmethod
    def get_api_key(cls) -> str:
        """Get the appropriate API key based on the provider."""
        provider = cls.get_provider()
        if provider == 'anthropic':
            return cls.ANTHROPIC_API_KEY
        elif provider == 'openai':
            return cls.OPENAI_API_KEY
        return ''


# Quick access
ai_config = AIConfig()
