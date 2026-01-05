"""
OpenAI Provider
Support for GPT models
"""
import os
import time
from typing import List, Dict, Optional, Callable

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT Provider"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        super().__init__(self.api_key, model)
        if self.available and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    def get_default_model(self) -> str:
        return "gpt-4o-mini"  # Fast and affordable

    def check_availability(self) -> bool:
        return OPENAI_AVAILABLE and bool(self.api_key)

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict]:
        return [{"role": msg.role, "content": msg.content} for msg in messages]

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
                content="OpenAI API non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="OpenAI not available"
            )

        try:
            openai_messages = self._convert_messages(messages)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
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
                content=f"Erreur OpenAI: {str(e)}",
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
                content="OpenAI API non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="OpenAI not available"
            )

        try:
            openai_messages = self._convert_messages(messages)
            full_content = ""

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    on_token(token)

            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=full_content,
                tool_calls=[], tool_results=[],
                response_time_ms=response_time,
                model=self.model, success=True
            )
        except Exception as e:
            return LLMResponse(
                content=f"Erreur OpenAI streaming: {str(e)}",
                tool_calls=[], tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False, error=str(e)
            )

    def list_models(self) -> List[str]:
        if not self.available:
            return []
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
