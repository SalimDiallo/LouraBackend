"""
Anthropic Provider
Support for Claude models
"""
import os
import time
from typing import List, Dict, Optional, Callable

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        super().__init__(self.api_key, model)
        if self.available and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def get_default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    def check_availability(self) -> bool:
        return ANTHROPIC_AVAILABLE and bool(self.api_key)

    def _convert_messages(self, messages: List[LLMMessage]) -> tuple:
        """Convert to Anthropic format (separate system message)"""
        system = ""
        claude_messages = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                claude_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        return system, claude_messages

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        if not self.available:
            return LLMResponse(
                content="Anthropic API non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="Anthropic not available"
            )

        try:
            system, claude_messages = self._convert_messages(messages)

            response = self.client.messages.create(
                model=self.model,
                system=system,
                messages=claude_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=content,
                tool_calls=[],
                tool_results=[],
                response_time_ms=response_time,
                tokens_used=tokens_used,
                model=self.model,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content=f"Erreur Anthropic: {str(e)}",
                tool_calls=[], tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False, error=str(e)
            )

    def stream_chat(
        self,
        messages: List[LLMMessage],
        on_token: Callable[[str], None],
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        start = time.time()

        if not self.available:
            return LLMResponse(
                content="Anthropic API non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="Anthropic not available"
            )

        try:
            system, claude_messages = self._convert_messages(messages)
            full_content = ""

            with self.client.messages.stream(
                model=self.model,
                system=system,
                messages=claude_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    full_content += text
                    on_token(text)

            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=full_content,
                tool_calls=[], tool_results=[],
                response_time_ms=response_time,
                model=self.model, success=True
            )
        except Exception as e:
            return LLMResponse(
                content=f"Erreur Anthropic streaming: {str(e)}",
                tool_calls=[], tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False, error=str(e)
            )

    def list_models(self) -> List[str]:
        if not self.available:
            return []
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ]
