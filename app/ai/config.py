"""
AI Configuration - Simplified for Ollama only
"""
import os


class AIConfig:
    """
    AI Configuration - Ollama Only

    Environment Variables:
        AI_MODEL: Ollama model name (default: llama3.2)
        AI_TEMPERATURE: 0.0-1.0 (default: 0.3)
        AI_MAX_TOKENS: Max tokens to generate (default: 1024)
        AI_TIMEOUT: Request timeout in seconds (default: 60)
        OLLAMA_HOST: Ollama server URL (default: http://localhost:11434)
    """

    # Ollama settings
    MODEL = os.getenv('AI_MODEL', 'llama3.2')
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

    # Generation settings
    TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.3'))
    MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1024'))
    TIMEOUT = int(os.getenv('AI_TIMEOUT', '60'))

    # Response settings
    CONCISE_MODE = os.getenv('AI_CONCISE_MODE', 'true').lower() == 'true'
    USE_EMOJIS = os.getenv('AI_USE_EMOJIS', 'true').lower() == 'true'

    # Tool/Function calling
    ENABLE_TOOLS = os.getenv('AI_ENABLE_TOOLS', 'true').lower() == 'true'
    MAX_TOOL_CALLS = int(os.getenv('AI_MAX_TOOL_CALLS', '5'))

    @classmethod
    def get_config(cls) -> dict:
        """Get configuration"""
        return {
            'model': cls.MODEL,
            'ollama_host': cls.OLLAMA_HOST,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'timeout': cls.TIMEOUT,
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Check if Ollama is available"""
        return True  # Ollama doesn't need API key


# Quick access to configuration
ai_config = AIConfig()
