"""
Simple Ollama Provider Manager
"""
import os
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from .config import ai_config


@dataclass
class LLMMessage:
    """Standard message format"""
    role: str  # 'system', 'user', 'assistant'
    content: str


@dataclass
class LLMResponse:
    """Standard response format"""
    content: str
    tool_calls: List[Dict]
    tool_results: List[Dict]
    response_time_ms: int
    tokens_used: Optional[int] = None
    model: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class OllamaManager:
    """
    Simplified Ollama Manager
    
    Usage:
        manager = OllamaManager()
        if manager.available:
            response = manager.chat([LLMMessage(role="user", content="Hello")])
    """

    def __init__(self, model: Optional[str] = None):
        self.model = model or ai_config.MODEL
        self._available = None

    @property
    def available(self) -> bool:
        """Check if Ollama is available"""
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Check if Ollama server is running and model exists"""
        if not OLLAMA_AVAILABLE:
            print("❌ Package 'ollama' non installé. Exécutez: pip install ollama")
            return False
        
        try:
            result = ollama.list()
            if hasattr(result, 'models'):
                available_models = [m.model for m in result.models if hasattr(m, 'model')]
                # Check if our model exists
                model_base = self.model.split(':')[0]
                found = any(model_base in m for m in available_models)
                
                if not found:
                    print(f"⚠️ Modèle '{self.model}' non trouvé. Modèles disponibles: {available_models}")
                    print(f"💡 Exécutez: ollama pull {self.model}")
                    return False
                
                print(f"✅ Ollama disponible avec modèle: {self.model}")
                return True
            return False
        except Exception as e:
            print(f"❌ Ollama non accessible: {e}")
            print("💡 Assurez-vous qu'Ollama est démarré: ollama serve")
            return False

    def list_models(self) -> List[str]:
        """List available Ollama models"""
        if not OLLAMA_AVAILABLE:
            return []
        try:
            result = ollama.list()
            if hasattr(result, 'models'):
                return [m.model for m in result.models if hasattr(m, 'model')]
            return []
        except:
            return []

    def get_provider_info(self) -> Dict:
        """Get provider info"""
        return {
            "provider": "ollama",
            "model": self.model,
            "available": self.available,
            "host": ai_config.OLLAMA_HOST
        }

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = None,
        max_tokens: int = None,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to Ollama"""
        start = time.time()
        
        temperature = temperature or ai_config.TEMPERATURE
        max_tokens = max_tokens or ai_config.MAX_TOKENS

        if not self.available:
            return LLMResponse(
                content="❌ Ollama non disponible. Vérifiez que le serveur est démarré.",
                tool_calls=[],
                tool_results=[],
                response_time_ms=0,
                success=False,
                error="Ollama not available"
            )

        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
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
                tool_calls=[],
                tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False,
                error=str(e)
            )

    def stream_chat(
        self,
        messages: List[LLMMessage],
        on_token: Callable[[str], None],
        temperature: float = None,
        max_tokens: int = None,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Stream chat response from Ollama"""
        start = time.time()
        
        temperature = temperature or ai_config.TEMPERATURE
        max_tokens = max_tokens or ai_config.MAX_TOKENS

        if not self.available:
            return LLMResponse(
                content="Ollama non disponible",
                tool_calls=[],
                tool_results=[],
                response_time_ms=0,
                success=False,
                error="Ollama not available"
            )

        try:
            ollama_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
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
                tool_calls=[],
                tool_results=[],
                response_time_ms=response_time,
                model=self.model,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                content=f"Erreur Ollama streaming: {str(e)}",
                tool_calls=[],
                tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False,
                error=str(e)
            )


# Alias pour compatibilité
ProviderManager = OllamaManager
