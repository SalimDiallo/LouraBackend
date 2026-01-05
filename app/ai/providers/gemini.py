"""
Google Gemini Provider
Uses Google's Gemini API for LLM capabilities
"""
import os
import time
import json
from typing import List, Dict, Optional, Callable, Any

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    # Create a dummy types module for type hints
    class types:
        Content = Any
        Part = Any
        Tool = Any
        FunctionDeclaration = Any
        GenerateContentConfig = Any

from .base import BaseLLMProvider, LLMMessage, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        super().__init__(self.api_key, model)

        if self.available and GEMINI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)

    def get_default_model(self) -> str:
        """Default Gemini model"""
        return "gemini-2.5-flash"  # Latest fast model

    def check_availability(self) -> bool:
        """Check if Gemini is available"""
        if not GEMINI_AVAILABLE:
            return False
        if not self.api_key:
            return False
        return True

    def _convert_messages_to_gemini(self, messages: List[LLMMessage]) -> tuple[List[types.Content], Optional[str]]:
        """Convert standard messages to Gemini format"""
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                gemini_messages.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=msg.content)]
                    )
                )
            elif msg.role == "assistant":
                gemini_messages.append(
                    types.Content(
                        role="model",
                        parts=[types.Part(text=msg.content)]
                    )
                )

        return gemini_messages, system_instruction

    def _convert_tools_to_gemini(self, tools: List[Dict]) -> List[types.Tool]:
        """Convert standard tools to Gemini function declarations"""
        if not tools:
            return []

        function_declarations = []
        for tool in tools:
            # Build parameters schema
            properties = {}
            required = []

            for param in tool.get("params", []):
                param_name = param if isinstance(param, str) else param.get("name", "")
                param_type = "STRING"  # Default type
                param_desc = ""

                if isinstance(param, dict):
                    # Map types to Gemini format
                    type_mapping = {
                        "string": "STRING",
                        "number": "NUMBER",
                        "integer": "INTEGER",
                        "boolean": "BOOLEAN",
                        "array": "ARRAY",
                        "object": "OBJECT"
                    }
                    param_type = type_mapping.get(param.get("type", "string"), "STRING")
                    param_desc = param.get("description", "")

                    if param.get("required", False):
                        required.append(param_name)

                properties[param_name] = types.Schema(
                    type=param_type,
                    description=param_desc
                )

            # Create function declaration
            function_declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=types.Schema(
                        type="OBJECT",
                        properties=properties,
                        required=required
                    )
                )
            )

        return [types.Tool(function_declarations=function_declarations)]

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Send chat request to Gemini"""
        start = time.time()

        if not self.available:
            return LLMResponse(
                content="Gemini API non disponible. Vérifiez votre clé API.",
                tool_calls=[],
                tool_results=[],
                response_time_ms=0,
                success=False,
                error="Gemini not available"
            )

        try:
            # Convert messages
            gemini_messages, system_instruction = self._convert_messages_to_gemini(messages)

            # Configure generation
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
            )

            if system_instruction:
                config.system_instruction = system_instruction

            if tools:
                config.tools = self._convert_tools_to_gemini(tools)

            # Generate content
            response = self.client.models.generate_content(
                model=self.model,
                contents=gemini_messages,
                config=config
            )

            # Extract content
            content = response.text if hasattr(response, 'text') else ""

            # Extract function calls if any
            tool_calls = []
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                tool_calls.append({
                                    "tool": fc.name,
                                    "params": dict(fc.args) if hasattr(fc, 'args') else {}
                                })

            # Count tokens
            tokens_used = None
            if hasattr(response, 'usage_metadata'):
                tokens_used = response.usage_metadata.total_token_count

            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                tool_results=[],
                response_time_ms=response_time,
                tokens_used=tokens_used,
                model=self.model,
                success=True
            )

        except Exception as e:
            return LLMResponse(
                content=f"Erreur Gemini: {str(e)}",
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
        temperature: float = 0.3,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Stream chat response from Gemini"""
        start = time.time()

        if not self.available:
            return LLMResponse(
                content="Gemini API non disponible.",
                tool_calls=[],
                tool_results=[],
                response_time_ms=0,
                success=False,
                error="Gemini not available"
            )

        try:
            # Convert messages
            gemini_messages, system_instruction = self._convert_messages_to_gemini(messages)

            # Configure generation
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
            )

            if system_instruction:
                config.system_instruction = system_instruction

            if tools:
                config.tools = self._convert_tools_to_gemini(tools)

            # Stream response
            full_content = ""
            tool_calls = []

            response_stream = self.client.models.generate_content_stream(
                model=self.model,
                contents=gemini_messages,
                config=config
            )

            for chunk in response_stream:
                if hasattr(chunk, 'text') and chunk.text:
                    full_content += chunk.text
                    on_token(chunk.text)

                # Check for function calls
                if hasattr(chunk, 'candidates') and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    fc = part.function_call
                                    tool_calls.append({
                                        "tool": fc.name,
                                        "params": dict(fc.args) if hasattr(fc, 'args') else {}
                                    })

            response_time = int((time.time() - start) * 1000)

            return LLMResponse(
                content=full_content,
                tool_calls=tool_calls,
                tool_results=[],
                response_time_ms=response_time,
                model=self.model,
                success=True
            )

        except Exception as e:
            return LLMResponse(
                content=f"Erreur streaming Gemini: {str(e)}",
                tool_calls=[],
                tool_results=[],
                response_time_ms=int((time.time() - start) * 1000),
                success=False,
                error=str(e)
            )

    def list_models(self) -> List[str]:
        """List available Gemini models"""
        if not self.available:
            return []

        try:
            models = self.client.models.list()
            return [
                model.name.replace('models/', '')
                for model in models
                if 'generateContent' in getattr(model, 'supported_generation_methods', [])
            ]
        except:
            return [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-2.0-flash",
            ]
