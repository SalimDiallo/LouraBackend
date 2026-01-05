"""
Provider Manager
Easy switching between different LLM providers
"""
import os
from typing import Optional, Dict, List
from enum import Enum

from .providers.base import BaseLLMProvider
from .providers.gemini import GeminiProvider
from .providers.ollama import OllamaProvider
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider


class ProviderType(str, Enum):
    """Available LLM providers"""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ProviderManager:
    """
    Manage multiple LLM providers with easy switching

    Usage:
        # Initialize with default provider
        manager = ProviderManager()

        # Switch provider
        manager.set_provider(ProviderType.GEMINI, model="gemini-1.5-flash")

        # Use provider
        response = manager.chat(messages)
    """

    # Default configurations
    DEFAULT_CONFIGS = {
        ProviderType.GEMINI: {
            "model": "gemini-1.5-flash",
            "api_key_env": "GOOGLE_API_KEY",
        },
        ProviderType.OLLAMA: {
            "model": "llama3.2",
            "api_key_env": None,
        },
        ProviderType.OPENAI: {
            "model": "gpt-4o-mini",
            "api_key_env": "OPENAI_API_KEY",
        },
        ProviderType.ANTHROPIC: {
            "model": "claude-3-5-sonnet-20241022",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
    }

    def __init__(
        self,
        provider: Optional[ProviderType] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize provider manager

        Args:
            provider: Which provider to use (default: auto-detect)
            model: Model name (default: provider's default)
            api_key: API key (default: from environment)
        """
        self.providers: Dict[ProviderType, BaseLLMProvider] = {}
        self.current_provider: Optional[BaseLLMProvider] = None
        self.current_provider_type: Optional[ProviderType] = None

        # Auto-detect or use specified provider
        if provider:
            self.set_provider(provider, model, api_key)
        else:
            self._auto_detect_provider()

    def _auto_detect_provider(self):
        """Auto-detect first available provider"""
        import os
        
        # Vérifier si un provider est forcé via AI_PROVIDER
        forced_provider = os.getenv('AI_PROVIDER', 'auto').lower()
        
        if forced_provider != 'auto':
            provider_map = {
                'gemini': ProviderType.GEMINI,
                'ollama': ProviderType.OLLAMA,
                'openai': ProviderType.OPENAI,
                'anthropic': ProviderType.ANTHROPIC,
            }
            if forced_provider in provider_map:
                provider_type = provider_map[forced_provider]
                config = self.DEFAULT_CONFIGS[provider_type]
                api_key = os.getenv(config["api_key_env"]) if config["api_key_env"] else None
                provider = self._create_provider(provider_type, config["model"], api_key)
                
                if provider and provider.available:
                    self.current_provider = provider
                    self.current_provider_type = provider_type
                    self.providers[provider_type] = provider
                    print(f"✅ Using forced provider: {provider_type.value}")
                    return
                else:
                    print(f"⚠️ Forced provider '{forced_provider}' not available, falling back to auto-detect")
        
        # Priority order: Gemini > OpenAI > Anthropic > Ollama
        priority = [
            ProviderType.GEMINI,
            ProviderType.OPENAI,
            ProviderType.ANTHROPIC,
            ProviderType.OLLAMA,
        ]

        for provider_type in priority:
            config = self.DEFAULT_CONFIGS[provider_type]
            api_key = os.getenv(config["api_key_env"]) if config["api_key_env"] else None

            provider = self._create_provider(provider_type, config["model"], api_key)

            if provider and provider.available:
                self.current_provider = provider
                self.current_provider_type = provider_type
                self.providers[provider_type] = provider
                print(f"✅ Auto-detected provider: {provider_type.value}")
                return

        # Fallback message
        print("⚠️ No LLM provider available. Please configure API keys.")

    def _create_provider(
        self,
        provider_type: ProviderType,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Optional[BaseLLMProvider]:
        """Create provider instance"""
        provider_classes = {
            ProviderType.GEMINI: GeminiProvider,
            ProviderType.OLLAMA: OllamaProvider,
            ProviderType.OPENAI: OpenAIProvider,
            ProviderType.ANTHROPIC: AnthropicProvider,
        }

        provider_class = provider_classes.get(provider_type)
        if not provider_class:
            return None

        try:
            return provider_class(api_key=api_key, model=model)
        except Exception as e:
            print(f"❌ Failed to create {provider_type.value} provider: {e}")
            return None

    def set_provider(
        self,
        provider_type: ProviderType,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Switch to a different provider

        Args:
            provider_type: Provider to switch to
            model: Model name (optional)
            api_key: API key (optional)

        Returns:
            True if successful, False otherwise
        """
        # Always create new provider if model or api_key specified
        if model or api_key:
            provider = self._create_provider(provider_type, model, api_key)
            if provider and provider.available:
                self.providers[provider_type] = provider
                self.current_provider = provider
                self.current_provider_type = provider_type
                return True
            return False

        # Check if already initialized
        if provider_type in self.providers:
            self.current_provider = self.providers[provider_type]
            self.current_provider_type = provider_type
            return True

        # Create new provider
        provider = self._create_provider(provider_type, model, api_key)

        if provider and provider.available:
            self.providers[provider_type] = provider
            self.current_provider = provider
            self.current_provider_type = provider_type
            return True

        return False

    def get_current_provider(self) -> Optional[BaseLLMProvider]:
        """Get current active provider"""
        return self.current_provider

    def get_provider_info(self) -> Dict:
        """Get info about current provider"""
        if not self.current_provider:
            return {"available": False, "provider": None}

        return {
            "available": True,
            "provider": self.current_provider_type.value if self.current_provider_type else None,
            "model": self.current_provider.model,
            "all_providers": list(self.providers.keys())
        }

    def list_available_providers(self) -> List[Dict]:
        """List all available providers with their status"""
        result = []

        for provider_type in ProviderType:
            config = self.DEFAULT_CONFIGS[provider_type]
            api_key_env = config["api_key_env"]
            has_api_key = bool(os.getenv(api_key_env)) if api_key_env else True

            # Try to initialize to check availability
            if provider_type not in self.providers:
                provider = self._create_provider(provider_type)
            else:
                provider = self.providers[provider_type]

            result.append({
                "provider": provider_type.value,
                "available": provider.available if provider else False,
                "has_api_key": has_api_key,
                "default_model": config["model"],
                "is_current": provider_type == self.current_provider_type
            })

        return result

    def list_models(self) -> List[str]:
        """List available models for current provider"""
        if not self.current_provider:
            return []
        return self.current_provider.list_models()

    # Delegate methods to current provider
    def chat(self, *args, **kwargs):
        """Send chat request using current provider"""
        if not self.current_provider:
            raise ValueError("No LLM provider available")
        return self.current_provider.chat(*args, **kwargs)

    def stream_chat(self, *args, **kwargs):
        """Stream chat using current provider"""
        if not self.current_provider:
            raise ValueError("No LLM provider available")
        return self.current_provider.stream_chat(*args, **kwargs)
