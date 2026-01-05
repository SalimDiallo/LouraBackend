"""
Base LLM Provider Interface
All providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """Standard message format"""
    role: str  # system, user, assistant
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[List[Dict]] = None


@dataclass
class LLMResponse:
    """Standard response format"""
    content: str
    tool_calls: List[Dict]
    tool_results: List[Dict]
    response_time_ms: int
    tokens_used: Optional[int] = None
    model: str = ""
    success: bool = True
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.available = self.check_availability()

    @abstractmethod
    def get_default_model(self) -> str:
        """Return default model name for this provider"""
        pass

    @abstractmethod
    def check_availability(self) -> bool:
        """Check if provider is available and configured"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send chat request to LLM

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[LLMMessage],
        on_token: Callable[[str], None],
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Stream chat response token by token

        Args:
            messages: List of conversation messages
            on_token: Callback for each token
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with full content and metadata
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models for this provider"""
        pass

    def format_tools_for_provider(self, tools: List[Dict]) -> Any:
        """
        Convert standard tool format to provider-specific format
        Override this if provider has special tool format
        """
        return tools
