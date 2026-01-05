"""
Ollama Provider
For local open-source models
"""
import time
from typing import List, Dict, Optional, Callable

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from .base import BaseLLMProvider, LLMMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM Provider"""

    def get_default_model(self) -> str:
        return "qwen2.5:14b"

    def check_availability(self) -> bool:
        if not OLLAMA_AVAILABLE:
            return False
        try:
            result = ollama.list()
            # Vérifier si le modèle spécifié existe
            if hasattr(result, 'models'):
                available_models = [m.model for m in result.models if hasattr(m, 'model')]
                # Vérifier si notre modèle est dans la liste (peut être partiel, ex: "qwen2.5:14b" ou "qwen2.5")
                model_name = self.model.split(':')[0] if ':' in self.model else self.model
                return any(model_name in m for m in available_models)
            return False
        except:
            return False

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict]:
        """Convert to Ollama format"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

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
                content="Ollama non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="Ollama not available"
            )

        try:
            ollama_messages = self._convert_messages(messages)
            response = ollama.chat(
                model=self.model,
                messages=ollama_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            content = response.message.content if hasattr(response, 'message') else str(response)
            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=content,
                tool_calls=[],
                tool_results=[],
                response_time_ms=response_time,
                model=self.model,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content=f"Erreur Ollama: {str(e)}",
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
                content="Ollama non disponible",
                tool_calls=[], tool_results=[],
                response_time_ms=0, success=False,
                error="Ollama not available"
            )

        try:
            ollama_messages = self._convert_messages(messages)
            full_content = ""

            for chunk in ollama.chat(
                model=self.model,
                messages=ollama_messages,
                stream=True,
                options={"temperature": temperature, "num_predict": max_tokens}
            ):
                if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                    token = chunk.message.content
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
                content=f"Erreur Ollama streaming: {str(e)}",
                tool_calls=[], tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False, error=str(e)
            )

    def list_models(self) -> List[str]:
        if not self.available:
            return []
        try:
            result = ollama.list()
            if hasattr(result, 'models'):
                return [m.model for m in result.models if hasattr(m, 'model')]
            return []
        except:
            return []
