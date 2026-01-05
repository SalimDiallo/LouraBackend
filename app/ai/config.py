"""
AI Configuration
Centralized configuration for LLM providers
"""
import os
from typing import Optional
from enum import Enum


class AIConfig:
    """
    AI Configuration Manager

    Environment Variables:
        # Provider selection
        AI_PROVIDER: gemini|ollama|openai|anthropic (default: auto-detect)
        AI_MODEL: Model name (default: provider's default)

        # API Keys
        GOOGLE_API_KEY or GEMINI_API_KEY: For Gemini
        OPENAI_API_KEY: For OpenAI
        ANTHROPIC_API_KEY: For Claude
        # Ollama doesn't need API key (local)

        # Advanced settings
        AI_TEMPERATURE: 0.0-1.0 (default: 0.3)
        AI_MAX_TOKENS: Max tokens to generate (default: 500)
        AI_TIMEOUT: Request timeout in seconds (default: 30)
    """

    # Provider settings
    PROVIDER = os.getenv('AI_PROVIDER', 'auto')  # auto | gemini | ollama | openai | anthropic
    MODEL = os.getenv('AI_MODEL', None)  # None = use provider's default

    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

    # Generation settings - Low temperature for factual accuracy, avoid hallucinations
    TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.1'))
    MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1024'))
    TIMEOUT = int(os.getenv('AI_TIMEOUT', '30'))

    # Response settings
    CONCISE_MODE = os.getenv('AI_CONCISE_MODE', 'true').lower() == 'true'
    USE_EMOJIS = os.getenv('AI_USE_EMOJIS', 'true').lower() == 'true'

    # Tool/Function calling
    ENABLE_TOOLS = os.getenv('AI_ENABLE_TOOLS', 'true').lower() == 'true'
    MAX_TOOL_CALLS = int(os.getenv('AI_MAX_TOOL_CALLS', '5'))

    @classmethod
    def get_provider_config(cls) -> dict:
        """Get provider configuration"""
        return {
            'provider': cls.PROVIDER,
            'model': cls.MODEL,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'timeout': cls.TIMEOUT,
        }

    @classmethod
    def get_api_keys(cls) -> dict:
        """Get all API keys"""
        return {
            'google': cls.GOOGLE_API_KEY,
            'openai': cls.OPENAI_API_KEY,
            'anthropic': cls.ANTHROPIC_API_KEY,
        }

    @classmethod
    def is_configured(cls, provider: str) -> bool:
        """Check if a specific provider is configured"""
        if provider == 'ollama':
            return True  # Ollama doesn't need API key

        key_map = {
            'gemini': cls.GOOGLE_API_KEY,
            'openai': cls.OPENAI_API_KEY,
            'anthropic': cls.ANTHROPIC_API_KEY,
        }

        return bool(key_map.get(provider))


# Quick access to configuration
ai_config = AIConfig()
