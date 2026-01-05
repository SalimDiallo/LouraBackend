"""
AI Agent Service - Multi-Provider Support
Enhanced with flexible LLM provider switching
"""
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .provider_manager import ProviderManager, ProviderType
from .providers.base import LLMMessage, LLMResponse
from .config import ai_config


@dataclass
class ToolResult:
    """Résultat d'une exécution d'outil"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: int = 0


class LouraAIAgent:
    """
    Agent IA pour Loura avec support multi-providers

    Usage:
        # Auto-detect provider
        agent = LouraAIAgent(organization=org)

        # Use specific provider
        agent = LouraAIAgent(organization=org, provider='gemini')

        # Switch provider at runtime
        agent.switch_provider('ollama', 'qwen2.5:14b')

        # Chat
        response = agent.chat("Donne-moi les stats RH", agent_mode=True)
    """

    # Défaut pour compatibilité
    DEFAULT_MODEL = "gemini-2.5-flash"

    # Prompts système
    SYSTEM_PROMPT = """Tu es l'assistant IA de Loura, une application de gestion d'entreprise.
Organisation: {org_name}

RÈGLES STRICTES:
1. Tu NE DOIS JAMAIS inventer de données. Si tu ne sais pas, dis-le.
2. Tu guides les utilisateurs dans l'utilisation de l'application.
3. Tu expliques les fonctionnalités disponibles.
4. Pour obtenir des données réelles, active le "Mode Agent".

Réponds en français, de manière professionnelle mais amicale.
"""

    AGENT_SYSTEM_PROMPT = """Tu es l'agent IA de Loura - Assistant de gestion d'entreprise pour {org_name}.

OUTILS DISPONIBLES:
{tools_description}

⛔ RÈGLES ANTI-HALLUCINATION - ABSOLUMENT INTERDITES:
1. Tu NE DOIS JAMAIS inventer de données, chiffres, noms ou statistiques
2. Tu NE DOIS JAMAIS extrapoler ou deviner des informations non fournies
3. Tu NE DOIS JAMAIS "compléter" des données partielles avec des suppositions
4. Tu NE DOIS JAMAIS donner d'exemples avec des données fictives
5. Si tu n'as pas exécuté d'outil → DIS "Je vais chercher ces informations" et appelle un outil
6. Si l'outil retourne "Aucune donnée" → DIS EXACTEMENT "Aucune donnée trouvée" + propose une alternative

🎯 PROCESSUS OBLIGATOIRE:
1. L'utilisateur pose une question → APPELLE un outil approprié
2. Attends les DONNÉES RÉELLES retournées par l'outil  
3. Réponds UNIQUEMENT à partir des données reçues
4. Si donnée absente → NE PAS inventer, dire "non disponible"

📋 FORMAT D'APPEL D'OUTIL:
```
<action>
{{"tool": "nom_outil", "params": {{"param": "valeur"}}}}
</action>
```

✅ FORMAT DE RÉPONSE CORRECT:
- Maximum 3 phrases
- Chiffres en **gras** avec émojis
- Structure: Donnée → Insight → Action
- Exemples UNIQUEMENT si données réelles disponibles

❌ CE QUE TU NE DOIS JAMAIS FAIRE:
- "Par exemple, vous pourriez avoir 45 employés..." → INTERDIT
- "Imaginons que le stock soit de..." → INTERDIT  
- "En général, les entreprises ont..." → INTERDIT
- Donner des chiffres sans les avoir reçus d'un outil → INTERDIT

📊 EXEMPLES DE RÉPONSES CORRECTES:
Q: "Combien d'employés ?"
A: [Appelle d'abord liste_employes ou statistiques_rh, puis répond avec les vrais chiffres]

Q: "Montre le stock"  
A: [Appelle liste_produits ou verifier_stock, puis répond avec les données réelles]

RAPPEL FINAL: Tu es UN RAPPORTEUR DE DONNÉES, pas un créateur. Zéro invention."""

    def __init__(
        self,
        organization=None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize AI Agent

        Args:
            organization: Organization instance
            provider: LLM provider (gemini|ollama|openai|anthropic|auto)
            model: Model name (optional, uses provider default)
            api_key: API key (optional, uses environment variable)
        """
        self.organization = organization
        self._model = model

        # Initialize provider manager
        if provider and provider != 'auto':
            provider_type = ProviderType(provider)
            self.provider_manager = ProviderManager(provider_type, model, api_key)
        else:
            self.provider_manager = ProviderManager()

        # Register tools (importé du code existant)
        self.tools = self._register_tools()

    @property
    def model(self) -> str:
        """Return current model name"""
        info = self.provider_manager.get_provider_info()
        return info.get('model', self._model or self.DEFAULT_MODEL)

    def _register_tools(self) -> Dict[str, callable]:
        """Enregistre les outils disponibles pour l'agent"""
        # ... (copier tout le code de _register_tools de agent_old.py)
        # Pour simplifier, je vais importer les fonctions existantes
        from .agent_old import LouraAIAgent as OldAgent
        old_agent = OldAgent(self.organization)
        return old_agent.tools

    def switch_provider(
        self,
        provider: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Switch to a different LLM provider

        Args:
            provider: Provider name (gemini|ollama|openai|anthropic)
            model: Model name (optional)
            api_key: API key (optional)

        Returns:
            True if successful

        Example:
            agent.switch_provider('gemini', 'gemini-1.5-pro')
            agent.switch_provider('ollama', 'qwen2.5:14b')
        """
        provider_type = ProviderType(provider)
        return self.provider_manager.set_provider(provider_type, model, api_key)

    def get_provider_info(self) -> Dict:
        """Get information about current LLM provider"""
        return self.provider_manager.get_provider_info()

    def list_available_providers(self) -> List[Dict]:
        """List all available providers"""
        return self.provider_manager.list_available_providers()

    def list_available_models(self) -> List[str]:
        """List available models for current provider"""
        return self.provider_manager.list_models()

    def get_available_models(self) -> List[str]:
        """Alias for list_available_models (compatibility with views.py)"""
        return self.list_available_models()

    def _get_tools_description(self) -> str:
        """Génère la description des outils pour le prompt"""
        descriptions = []
        for name, tool in self.tools.items():
            params = ", ".join(tool["params"]) if tool["params"] else "aucun"
            descriptions.append(f"- {name}: {tool['description']} (params: {params})")
        return "\n".join(descriptions)

    def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        agent_mode: bool = False
    ) -> Dict:
        """
        Send message to AI agent

        Args:
            message: User message
            conversation_history: Previous messages
            agent_mode: Enable tool execution

        Returns:
            Dict with content, tool_calls, tool_results, metadata
        """
        start_time = time.time()

        # Check provider availability
        if not self.provider_manager.current_provider:
            return {
                "success": False,
                "content": "Aucun provider IA disponible. Configurez une clé API.",
                "error": "No provider available",
                "tool_calls": [],
                "tool_results": [],
                "response_time_ms": 0,
            }

        try:
            # Build system prompt
            org_name = self.organization.name if self.organization else "Non définie"

            if agent_mode:
                system_prompt = self.AGENT_SYSTEM_PROMPT.format(
                    org_name=org_name,
                    tools_description=self._get_tools_description()
                )
            else:
                system_prompt = self.SYSTEM_PROMPT.format(org_name=org_name)

            # Build messages
            messages = [LLMMessage(role="system", content=system_prompt)]

            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append(LLMMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", "")
                    ))

            messages.append(LLMMessage(role="user", content=message))

            # Convert tools to standard format
            tools_list = None
            if agent_mode:
                tools_list = [
                    {
                        "name": name,
                        "description": tool["description"],
                        "params": tool["params"]
                    }
                    for name, tool in self.tools.items()
                ]

            # Call LLM provider
            response = self.provider_manager.chat(
                messages=messages,
                temperature=ai_config.TEMPERATURE,
                max_tokens=ai_config.MAX_TOKENS,
                tools=tools_list
            )

            if not response.success:
                return {
                    "success": False,
                    "content": response.content,
                    "error": response.error,
                    "tool_calls": [],
                    "tool_results": [],
                    "response_time_ms": response.response_time_ms,
                }

            content = response.content
            tool_calls = []
            tool_results = []

            # Process agent actions if in agent mode
            if agent_mode and "<action>" in content:
                content, tool_calls, tool_results = self._process_agent_actions(content)

                # If tools were executed, get final response with real data
                if tool_results:
                    results_data = self._format_tool_results_for_ai(tool_results)

                    messages.append(LLMMessage(role="assistant", content=content))
                    messages.append(LLMMessage(
                        role="user",
                        content=f"""⛔ RAPPEL CRITIQUE - ZÉRO HALLUCINATION:
Tu DOIS répondre en utilisant EXCLUSIVEMENT les données ci-dessous.
NE JAMAIS inventer, extrapoler ou "compléter" avec des informations non présentes.

DONNÉES RÉELLES RETOURNÉES PAR LES OUTILS:
{results_data}

RÈGLES DE RÉPONSE:
1. Cite UNIQUEMENT les chiffres exacts présents dans les données
2. Si une info n'est pas dans les données → dis "non disponible" 
3. Maximum 3 phrases, format: Donnée → Insight → Action
4. Utilise **gras** pour les chiffres clés + émojis pertinents
5. Si "Aucune donnée trouvée" → dis-le clairement et propose une alternative

Formule ta réponse maintenant:"""
                    ))

                    final_response = self.provider_manager.chat(
                        messages=messages,
                        temperature=ai_config.TEMPERATURE,
                        max_tokens=ai_config.MAX_TOKENS,
                    )
                    content = final_response.content if final_response.success else content

            response_time = int((time.time() - start_time) * 1000)
            provider_info = self.get_provider_info()

            return {
                "success": True,
                "content": content,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "response_time_ms": response_time,
                "model": provider_info.get("model", "unknown"),
                "provider": provider_info.get("provider", "unknown"),
                "tokens_used": response.tokens_used,
            }

        except Exception as e:
            return {
                "success": False,
                "content": f"Erreur IA: {str(e)}",
                "error": str(e),
                "tool_calls": [],
                "tool_results": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
            }

    def _process_agent_actions(self, content: str) -> tuple:
        """Process agent tool calls (same as before)"""
        # ... (copier le code de agent_old.py)
        from .agent_old import LouraAIAgent as OldAgent
        old_agent = OldAgent(self.organization)
        return old_agent._process_agent_actions(content)

    def _format_tool_results_for_ai(self, tool_results: List[Dict]) -> str:
        """Format tool results for AI (same as before)"""
        from .agent_old import LouraAIAgent as OldAgent
        old_agent = OldAgent(self.organization)
        return old_agent._format_tool_results_for_ai(tool_results)

    # Note: Les autres méthodes (_list_employees, _get_hr_stats, etc.)
    # sont déjà dans agent_old.py et seront importées automatiquement
    # via l'héritage implicite des tools
