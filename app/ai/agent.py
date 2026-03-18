"""
AI Agent Service - Multi-Provider (Claude & OpenAI) with Function Calling
=========================================================================
Agent IA sophistiqué supportant Anthropic Claude et OpenAI avec function calling.

Architecture:
    User Message → AI (avec tools) → AI choisit un outil → Exécution → AI formule réponse

Le function calling natif (Claude Tool Use & OpenAI Function Calling) est BEAUCOUP
plus fiable que le parsing de <action> en XML. L'AI retourne un JSON structuré avec
le nom de l'outil et les paramètres, qu'on exécute côté serveur.

Provider sélectionné automatiquement selon les clés API disponibles :
    1. Claude (ANTHROPIC_API_KEY) - prioritaire
    2. OpenAI (OPENAI_API_KEY) - fallback
"""

import json
import time
import logging
from typing import List, Dict, Optional

from openai import OpenAI
import anthropic

from .config import ai_config
from .tools import registry

logger = logging.getLogger(__name__)


class LouraAIAgent:
    """
    Agent IA pour Loura supportant Claude & OpenAI avec function calling.

    Usage:
        agent = LouraAIAgent(organization=org, user=user)
        response = agent.chat("Combien d'employés dans ma boîte ?")

    Le provider est sélectionné automatiquement selon les clés API disponibles.
    """

    SYSTEM_PROMPT = """Tu es **Loura AI**, l'assistant intelligent du CRM Loura pour l'organisation **{org_name}**.

**TON ROLE:**
Tu es un assistant de gestion d'entreprise qui peut LIRE et AGIR sur les données de l'organisation.
Tu as accès à des outils pour consulter les données (employés, ventes, stocks, congés) 
ET pour effectuer des actions (créer des employés, soumettre des demandes de congé, etc.).

**CONTEXTE UTILISATEUR:**
- Utilisateur connecté : {user_name} ({user_email})
- Rôle : {user_role}
- Devise de l'organisation : {currency}
- Organisation : {org_name}

**REGLES:**
1. Utilise TOUJOURS les outils pour accéder aux données. Ne JAMAIS inventer de données.
2. Si l'utilisateur demande une information, appelle l'outil approprié.
3. Si l'utilisateur demande une action (créer, modifier), appelle l'outil d'écriture.
4. Si tu ne peux pas faire quelque chose, dis-le clairement et suggère une alternative.
5. Réponds en français, de manière professionnelle mais amicale.
6. Formate tes réponses en Markdown pour la lisibilité.
7. Sois concis mais complet.
8. Pour les montants, utilise toujours la devise {currency}.
9. Ne jamais utiliser d'emojis ou de stickers dans tes réponses. Reste professionnel.

**ACTIONS DISPONIBLES:**
Tu peux faire des actions réelles sur le CRM comme:
- Consulter la liste des employés, départements, produits
- Voir les statistiques RH et commerciales
- Créer un nouvel employé
- Faire une demande de congé
- Voir les clients qui doivent de l'argent (créances)
- Et bien plus...

**IMPORTANT - ACTIONS D'ECRITURE:**
- Pour les actions d'écriture (création, modification, suppression), tu DOIS d'abord décrire ce que tu vas faire et attendre la confirmation de l'utilisateur.
- Quand l'utilisateur confirme (oui, ok, confirmer, valider, etc.), exécute l'action.
- Si l'utilisateur ne donne pas assez d'informations, demande les détails manquants.
- Ne fais JAMAIS d'action d'écriture sans confirmation explicite.
"""

    def __init__(self, organization=None, user=None, model: str = None):
        self.organization = organization
        self.user = user
        self.provider = ai_config.get_provider()

        if not self.provider:
            raise ValueError(
                "Aucune clé API configurée. Ajoutez ANTHROPIC_API_KEY ou OPENAI_API_KEY dans votre fichier .env"
            )

        # Set model based on provider
        if model:
            self.model = model
        else:
            self.model = ai_config.MODEL or ai_config.get_default_model()

        # Initialize the appropriate client
        if self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=ai_config.ANTHROPIC_API_KEY)
            logger.info(f"AI Agent initialized with Claude: {self.model}")
        elif self.provider == 'openai':
            self.client = OpenAI(api_key=ai_config.OPENAI_API_KEY)
            logger.info(f"AI Agent initialized with OpenAI: {self.model}")
        else:
            raise ValueError(f"Provider inconnu: {self.provider}")

    def _get_user_context(self) -> Dict:
        """Extracts user context for the system prompt."""
        user_name = "Utilisateur"
        user_email = "non défini"
        user_role = "utilisateur"

        if self.user:
            user_name = self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user)
            user_email = getattr(self.user, 'email', 'non défini')
            user_type = getattr(self.user, 'user_type', 'employee')
            user_role = "Administrateur" if user_type == 'admin' else "Employé"

        currency = "MAD"
        if self.organization:
            try:
                settings = self.organization.settings
                currency = settings.currency or "MAD"
            except Exception:
                pass

        return {
            "user_name": user_name,
            "user_email": user_email,
            "user_role": user_role,
            "currency": currency,
        }

    def _build_system_prompt(self) -> str:
        """Builds the system prompt with user context."""
        org_name = self.organization.name if self.organization else "Non définie"
        ctx = self._get_user_context()
        return self.SYSTEM_PROMPT.format(
            org_name=org_name,
            user_name=ctx["user_name"],
            user_email=ctx["user_email"],
            user_role=ctx["user_role"],
            currency=ctx["currency"],
        )

    def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ) -> Dict:
        """
        Envoie un message à l'agent IA avec function calling.

        Args:
            message: Message de l'utilisateur
            conversation_history: Historique de conversation

        Returns:
            Dict avec: success, content, tool_calls, tool_results, response_time_ms, model, provider
        """
        if self.provider == 'anthropic':
            return self._chat_anthropic(message, conversation_history)
        elif self.provider == 'openai':
            return self._chat_openai(message, conversation_history)
        else:
            return {
                "success": False,
                "content": "Provider inconnu.",
                "error": f"Provider inconnu: {self.provider}",
                "tool_calls": [],
                "tool_results": [],
                "response_time_ms": 0,
                "model": self.model,
                "provider": self.provider,
            }

    def _chat_openai(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ) -> Dict:
        """Implémentation chat pour OpenAI."""
        start_time = time.time()

        try:
            system_prompt = self._build_system_prompt()

            # Construire les messages
            messages = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                for msg in conversation_history[-20:]:  # Garder les 20 derniers messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            messages.append({"role": "user", "content": message})

            # Récupérer les outils OpenAI
            tools = registry.get_openai_tools()

            # Premier appel à GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=ai_config.TEMPERATURE,
                max_tokens=ai_config.MAX_TOKENS,
            )

            assistant_message = response.choices[0].message
            all_tool_calls = []
            all_tool_results = []
            pending_confirmations = []

            # Boucle de function calling (GPT peut appeler plusieurs outils)
            max_iterations = ai_config.MAX_TOOL_CALLS
            iteration = 0

            while assistant_message.tool_calls and iteration < max_iterations:
                iteration += 1

                # Ajouter le message assistant avec les tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ],
                })

                # Exécuter chaque outil demandé
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    logger.info(f"Tool execution: {tool_name} with args: {tool_args}")

                    # Check if tool requires confirmation
                    tool_def = registry.get(tool_name)
                    if tool_def and not tool_def.is_read_only:
                        # For write actions, return a pending confirmation
                        pending_confirmations.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "description": tool_def.description,
                        })
                        result = self._execute_tool(tool_name, tool_args)
                    else:
                        result = self._execute_tool(tool_name, tool_args)

                    all_tool_calls.append({
                        "tool": tool_name,
                        "params": tool_args,
                        "is_write": not (tool_def.is_read_only if tool_def else True),
                    })
                    all_tool_results.append({
                        "tool": tool_name,
                        "success": result.get("success", True),
                        "data": result,
                        "error": result.get("error"),
                    })

                    # Ajouter le résultat au contexte pour GPT
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    })

                # Rappeler GPT avec les résultats des outils
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    temperature=ai_config.TEMPERATURE,
                    max_tokens=ai_config.MAX_TOKENS,
                )

                assistant_message = response.choices[0].message

            content = assistant_message.content or ""
            response_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "content": content,
                "tool_calls": all_tool_calls,
                "tool_results": all_tool_results,
                "pending_confirmations": pending_confirmations,
                "response_time_ms": response_time,
                "model": self.model,
                "provider": "openai",
            }

        except Exception as e:
            logger.error(f"AI Agent OpenAI error: {e}", exc_info=True)
            return {
                "success": False,
                "content": f"Erreur lors du traitement: {str(e)}",
                "error": str(e),
                "tool_calls": [],
                "tool_results": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
                "model": self.model,
                "provider": "openai",
            }

    def _chat_anthropic(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ) -> Dict:
        """Implémentation chat pour Anthropic Claude."""
        start_time = time.time()

        try:
            system_prompt = self._build_system_prompt()

            # Construire les messages (Claude n'utilise pas de message system dans messages)
            messages = []

            if conversation_history:
                for msg in conversation_history[-20:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            messages.append({"role": "user", "content": message})

            # Récupérer les outils Anthropic
            tools = registry.get_anthropic_tools()

            # Premier appel à Claude
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                tools=tools if tools else None,
                temperature=ai_config.TEMPERATURE,
                max_tokens=ai_config.MAX_TOKENS,
            )

            all_tool_calls = []
            all_tool_results = []

            # Boucle de tool use (Claude peut appeler plusieurs outils)
            max_iterations = ai_config.MAX_TOOL_CALLS
            iteration = 0

            while response.stop_reason == "tool_use" and iteration < max_iterations:
                iteration += 1

                # Ajouter la réponse de Claude
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                # Exécuter chaque outil demandé
                tool_results_content = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_args = content_block.input

                        logger.info(f"Tool execution: {tool_name} with args: {tool_args}")

                        # Exécuter l'outil
                        result = self._execute_tool(tool_name, tool_args)

                        tool_def = registry.get(tool_name)
                        all_tool_calls.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "is_write": not (tool_def.is_read_only if tool_def else True),
                        })
                        all_tool_results.append({
                            "tool": tool_name,
                            "success": result.get("success", True),
                            "data": result,
                            "error": result.get("error"),
                        })

                        # Ajouter le résultat pour Claude
                        tool_results_content.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        })

                # Ajouter les résultats des outils
                messages.append({
                    "role": "user",
                    "content": tool_results_content,
                })

                # Rappeler Claude avec les résultats des outils
                response = self.client.messages.create(
                    model=self.model,
                    system=system_prompt,
                    messages=messages,
                    tools=tools if tools else None,
                    temperature=ai_config.TEMPERATURE,
                    max_tokens=ai_config.MAX_TOKENS,
                )

            # Extraire le contenu textuel
            content = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    content += content_block.text

            response_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "content": content,
                "tool_calls": all_tool_calls,
                "tool_results": all_tool_results,
                "response_time_ms": response_time,
                "model": self.model,
                "provider": "anthropic",
            }

        except Exception as e:
            logger.error(f"AI Agent Anthropic error: {e}", exc_info=True)
            return {
                "success": False,
                "content": f"Erreur lors du traitement: {str(e)}",
                "error": str(e),
                "tool_calls": [],
                "tool_results": [],
                "response_time_ms": int((time.time() - start_time) * 1000),
                "model": self.model,
                "provider": "anthropic",
            }

    def chat_stream(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ):
        """
        Version streaming du chat. Retourne un générateur d'événements SSE.

        Yields:
            dict avec type ('token', 'tools', 'done', 'error') et contenu
        """
        if self.provider == 'anthropic':
            yield from self._chat_stream_anthropic(message, conversation_history)
        elif self.provider == 'openai':
            yield from self._chat_stream_openai(message, conversation_history)
        else:
            yield {"type": "error", "error": f"Provider inconnu: {self.provider}"}

    def _chat_stream_openai(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ):
        """
        Version streaming pour OpenAI avec vrai streaming token par token.

        Architecture:
        1. Premier appel en streaming → on yield les tokens en temps réel
        2. Si l'AI veut appeler des outils, on les accumule depuis le stream
        3. On exécute les outils, puis on re-streame la réponse finale
        """
        try:
            system_prompt = self._build_system_prompt()

            messages = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                for msg in conversation_history[-20:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            messages.append({"role": "user", "content": message})

            tools = registry.get_openai_tools()
            all_tool_calls = []
            all_tool_results = []
            max_iterations = ai_config.MAX_TOOL_CALLS
            iteration = 0

            while iteration <= max_iterations:
                # Appel en streaming
                # Construire les kwargs dynamiquement
                stream_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": ai_config.TEMPERATURE,
                    "max_tokens": ai_config.MAX_TOKENS,
                    "stream": True,
                }

                # Ajouter tools seulement à la première itération
                if tools and iteration == 0:
                    stream_kwargs["tools"] = tools
                    stream_kwargs["tool_choice"] = "auto"

                stream = self.client.chat.completions.create(**stream_kwargs)

                # Accumuler les tokens et détecter les tool_calls depuis le stream
                accumulated_content = ""
                accumulated_tool_calls = {}  # index -> {id, name, arguments}

                for chunk in stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    # Tokens de texte → yield immédiat
                    if delta.content:
                        accumulated_content += delta.content
                        yield {"type": "token", "content": delta.content}

                    # Tool calls accumulés depuis le stream
                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in accumulated_tool_calls:
                                accumulated_tool_calls[idx] = {
                                    "id": "",
                                    "name": "",
                                    "arguments": "",
                                }
                            if tc_delta.id:
                                accumulated_tool_calls[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    accumulated_tool_calls[idx]["name"] += tc_delta.function.name
                                if tc_delta.function.arguments:
                                    accumulated_tool_calls[idx]["arguments"] += tc_delta.function.arguments

                # Pas de tool calls → terminé
                if not accumulated_tool_calls:
                    break

                iteration += 1
                if iteration > max_iterations:
                    break

                # Construire le message assistant avec les tool_calls
                tool_calls_list = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"],
                        }
                    }
                    for tc in accumulated_tool_calls.values()
                ]

                messages.append({
                    "role": "assistant",
                    "content": accumulated_content or None,
                    "tool_calls": tool_calls_list,
                })

                # Exécuter chaque outil (ou demander confirmation pour les write tools)
                has_pending_confirmation = False
                for tc in accumulated_tool_calls.values():
                    tool_name = tc["name"]
                    try:
                        tool_args = json.loads(tc["arguments"])
                    except json.JSONDecodeError:
                        tool_args = {}

                    tool_def = registry.get(tool_name)
                    is_write = not (tool_def.is_read_only if tool_def else True)

                    if is_write:
                        # Write tool → demander confirmation, NE PAS exécuter
                        has_pending_confirmation = True
                        yield {
                            "type": "confirmation_required",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "tool_call_id": tc["id"],
                            "description": tool_def.description if tool_def else tool_name,
                        }

                        all_tool_calls.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "is_write": True,
                        })

                        # Envoyer un résultat "en attente" au modèle AI
                        pending_result = {
                            "status": "PENDING_CONFIRMATION",
                            "message": f"L'action '{tool_name}' nécessite la confirmation de l'utilisateur avant d'être exécutée.",
                        }
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(pending_result, ensure_ascii=False),
                        })
                    else:
                        # Read tool → exécuter normalement
                        yield {
                            "type": "tool_executing",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                        }

                        result = self._execute_tool(tool_name, tool_args)

                        all_tool_calls.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "is_write": False,
                        })
                        all_tool_results.append({
                            "tool": tool_name,
                            "success": result.get("success", True),
                            "data": result,
                            "error": result.get("error"),
                        })

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        })

                # Envoyer les résultats des outils au frontend
                if all_tool_results:
                    yield {"type": "tools", "tool_calls": all_tool_calls, "tool_results": all_tool_results}

                # La boucle continue → le prochain appel streaming génère la réponse finale
                # (sans tools pour éviter une boucle infinie)

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Streaming OpenAI error: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)}

    def _chat_stream_anthropic(
        self,
        message: str,
        conversation_history: List[Dict] = None,
    ):
        """
        Version streaming pour Anthropic Claude avec vrai streaming token par token.

        Architecture:
        1. Premier appel EN STREAMING pour voir les tokens en temps réel
        2. Si tools → exécute, puis re-streame la réponse finale
        """
        try:
            system_prompt = self._build_system_prompt()

            messages = []

            if conversation_history:
                for msg in conversation_history[-20:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    })

            messages.append({"role": "user", "content": message})

            tools = registry.get_anthropic_tools()
            all_tool_calls = []
            all_tool_results = []
            max_iterations = ai_config.MAX_TOOL_CALLS
            iteration = 0

            while iteration <= max_iterations:
                # Appel EN STREAMING depuis le début
                # Construire les kwargs dynamiquement pour éviter tools=None
                stream_kwargs = {
                    "model": self.model,
                    "system": system_prompt,
                    "messages": messages,
                    "temperature": ai_config.TEMPERATURE,
                    "max_tokens": ai_config.MAX_TOKENS,
                }

                # Ajouter tools seulement si nécessaire (première itération et tools disponibles)
                if tools and iteration == 0:
                    stream_kwargs["tools"] = tools

                with self.client.messages.stream(**stream_kwargs) as stream:
                    # Accumuler le contenu et les tool_use
                    accumulated_content = []
                    tool_uses = []

                    for event in stream:
                        # Stream de texte → yield immédiat
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text") and event.delta.text:
                                yield {"type": "token", "content": event.delta.text}

                        # Détecter les content blocks (texte et tool_use)
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                accumulated_content.append({"type": "text", "text": ""})
                            elif event.content_block.type == "tool_use":
                                tool_uses.append({
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": event.content_block.input,
                                })
                                accumulated_content.append(event.content_block)

                        # Accumuler le texte
                        if event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                if accumulated_content and accumulated_content[-1].get("type") == "text":
                                    accumulated_content[-1]["text"] += event.delta.text

                    # Récupérer le message final
                    final_message = stream.get_final_message()

                # Pas de tool_use → terminé
                if not tool_uses:
                    break

                iteration += 1
                if iteration > max_iterations:
                    break

                # Ajouter le message assistant avec les tool_use
                messages.append({
                    "role": "assistant",
                    "content": final_message.content,
                })

                # Traiter chaque tool_use
                tool_results_content = []
                for tool_use in tool_uses:
                    tool_name = tool_use["name"]
                    tool_args = tool_use["input"]
                    tool_id = tool_use["id"]

                    tool_def = registry.get(tool_name)
                    is_write = not (tool_def.is_read_only if tool_def else True)

                    if is_write:
                        # Write tool → demander confirmation
                        yield {
                            "type": "confirmation_required",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "tool_call_id": tool_id,
                            "description": tool_def.description if tool_def else tool_name,
                        }

                        all_tool_calls.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "is_write": True,
                        })

                        pending_result = json.dumps({
                            "status": "PENDING_CONFIRMATION",
                            "message": f"L'action '{tool_name}' nécessite la confirmation de l'utilisateur.",
                        }, ensure_ascii=False)
                        tool_results_content.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": pending_result,
                        })
                    else:
                        # Read tool → exécuter normalement
                        yield {
                            "type": "tool_executing",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                        }

                        result = self._execute_tool(tool_name, tool_args)

                        all_tool_calls.append({
                            "tool": tool_name,
                            "params": tool_args,
                            "is_write": False,
                        })
                        all_tool_results.append({
                            "tool": tool_name,
                            "success": result.get("success", True),
                            "data": result,
                            "error": result.get("error"),
                        })

                        tool_results_content.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result, ensure_ascii=False, default=str),
                        })

                messages.append({
                    "role": "user",
                    "content": tool_results_content,
                })

                # Envoyer les résultats des outils au frontend
                if all_tool_results:
                    yield {"type": "tools", "tool_calls": all_tool_calls, "tool_results": all_tool_results}

                # La boucle continue → le prochain appel streaming génère la réponse finale

            yield {"type": "done"}

        except Exception as e:
            logger.error(f"Streaming Anthropic error: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)}

    def _execute_tool(self, tool_name: str, args: Dict) -> Dict:
        """Exécute un outil enregistré."""
        tool = registry.get(tool_name)

        if not tool:
            return {
                "success": False,
                "error": f"Outil '{tool_name}' inconnu. Outils disponibles: {list(registry.get_all().keys())}",
            }

        try:
            # Tous les outils reçoivent organization en premier argument
            result = tool.function(self.organization, **args)
            return result
        except Exception as e:
            logger.error(f"Tool execution error {tool_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Erreur lors de l'exécution de '{tool_name}': {str(e)}",
            }

    def get_available_tools(self) -> List[Dict]:
        """Retourne la liste des outils disponibles."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "is_read_only": tool.is_read_only,
                "parameters": list(tool.parameters.get("properties", {}).keys()),
            }
            for tool in registry.get_all().values()
        ]

    def get_provider_info(self) -> Dict:
        """Get provider info."""
        return {
            "provider": self.provider,
            "model": self.model,
            "available": ai_config.is_configured(),
            "tools_count": len(registry.get_all()),
        }
