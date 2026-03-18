"""
AI Tools Registry
=================
Central registry for all tools (actions) available to the AI agent.
Each tool is a function decorated with @register_tool that the agent can call.

HOW TO ADD A NEW TOOL:
1. Create a new file in ai/tools/ (e.g. ai/tools/inventory_tools.py)
2. Import and use the @register_tool decorator
3. Define your function with type hints and a docstring
4. The tool is automatically available to the agent!

Example:
    from ai.tools.registry import register_tool

    @register_tool(
        name="creer_produit",
        description="Crée un nouveau produit dans l'inventaire",
        category="inventory",
    )
    def create_product(organization, name: str, price: float, sku: str = None) -> dict:
        '''Crée un produit avec le nom, prix et SKU optionnel.'''
        from inventory.models import Product
        product = Product.objects.create(
            organization=organization,
            name=name,
            selling_price=price,
            sku=sku or f"PRD-{Product.objects.count()+1:04d}",
        )
        return {"success": True, "message": f"Produit '{name}' créé", "id": product.id}
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Définition d'un outil pour l'agent IA"""
    name: str
    description: str
    function: Callable
    category: str  # "hr", "inventory", "general", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)  # JSON Schema
    requires_confirmation: bool = False  # Si True, l'agent demande confirmation avant d'exécuter
    is_read_only: bool = True  # True = lecture, False = écriture (modification de données)


class ToolsRegistry:
    """
    Registre central des outils.
    Singleton qui contient tous les outils enregistrés.
    """
    _instance = None
    _tools: Dict[str, ToolDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: ToolDefinition):
        """Enregistre un outil"""
        self._tools[tool.name] = tool
        logger.debug(f"🔧 Outil enregistré: {tool.name} ({tool.category})")

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Récupère un outil par son nom"""
        return self._tools.get(name)

    def get_all(self) -> Dict[str, ToolDefinition]:
        """Retourne tous les outils"""
        return self._tools.copy()

    def get_by_category(self, category: str) -> Dict[str, ToolDefinition]:
        """Retourne les outils d'une catégorie"""
        return {
            name: tool for name, tool in self._tools.items()
            if tool.category == category
        }

    def get_openai_tools(self) -> List[Dict]:
        """
        Génère la liste des outils au format OpenAI function calling.
        C'est ce format que GPT utilise pour savoir quels outils existent.
        """
        tools = []
        for name, tool in self._tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
        return tools

    def get_anthropic_tools(self) -> List[Dict]:
        """
        Génère la liste des outils au format Anthropic Claude tool use.
        C'est ce format que Claude utilise pour savoir quels outils existent.
        """
        tools = []
        for name, tool in self._tools.items():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            })
        return tools

    def get_tools_summary(self) -> str:
        """Résumé des outils pour le logging/debug"""
        categories = {}
        for tool in self._tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool.name)

        lines = []
        for cat, tools in categories.items():
            lines.append(f"  {cat}: {', '.join(tools)}")
        return "\n".join(lines)

    def clear(self):
        """Vide le registre (pour les tests)"""
        self._tools = {}


# Instance globale
registry = ToolsRegistry()


def register_tool(
    name: str,
    description: str,
    category: str,
    parameters: Dict[str, Any] = None,
    requires_confirmation: bool = False,
    is_read_only: bool = True,
):
    """
    Décorateur pour enregistrer un outil.

    La fonction décorée DOIT avoir comme premier argument `organization`
    (l'objet Organization de Django). Les autres arguments sont les
    paramètres que l'agent peut passer.

    Args:
        name: Nom unique de l'outil (utilisé par GPT pour l'appeler)
        description: Description de ce que fait l'outil (visible par GPT)
        category: Catégorie ("hr", "inventory", "general")
        parameters: JSON Schema des paramètres (format OpenAI)
        requires_confirmation: Si True, action nécessite confirmation utilisateur
        is_read_only: True = lecture seule, False = modification de données
    """
    def decorator(func: Callable) -> Callable:
        # Construire les paramètres si non fournis
        params = parameters or {
            "type": "object",
            "properties": {},
            "required": [],
        }

        tool = ToolDefinition(
            name=name,
            description=description,
            function=func,
            category=category,
            parameters=params,
            requires_confirmation=requires_confirmation,
            is_read_only=is_read_only,
        )

        registry.register(tool)
        return func

    return decorator
