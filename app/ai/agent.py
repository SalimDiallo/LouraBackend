"""
AI Agent Service - Ollama Only
Simplified agent using local Ollama models
"""
import json
import re
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .provider_manager import OllamaManager, LLMMessage, LLMResponse
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
    Agent IA pour Loura utilisant Ollama (modèles locaux)
    
    Usage:
        agent = LouraAIAgent(organization=org)
        response = agent.chat("Combien d'employés ?", agent_mode=True)
    """
    
    # Modèle par défaut
    DEFAULT_MODEL = "llama3.2"
    
    # Prompt système pour l'assistant
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

⛔ RÈGLES ANTI-HALLUCINATION:
1. Tu NE DOIS JAMAIS inventer de données
2. Si tu n'as pas exécuté d'outil → DIS "Je vais chercher ces informations" et appelle un outil
3. Si l'outil retourne "Aucune donnée" → DIS "Aucune donnée trouvée"

🎯 PROCESSUS:
1. L'utilisateur pose une question → APPELLE un outil
2. Attends les données réelles
3. Réponds avec les données reçues

📋 FORMAT D'APPEL D'OUTIL:
```
<action>
{{"tool": "nom_outil", "params": {{"param": "valeur"}}}}
</action>
```

✅ FORMAT DE RÉPONSE:
- Maximum 3 phrases
- Chiffres en **gras** avec émojis
- Structure: Donnée → Insight → Action

RAPPEL: Tu es UN RAPPORTEUR DE DONNÉES, pas un créateur."""

    def __init__(self, organization=None, model: str = None):
        self.organization = organization
        self.model = model or ai_config.MODEL or self.DEFAULT_MODEL
        self.ollama = OllamaManager(model=self.model)
        self.tools = self._register_tools()
        
    @property
    def provider_manager(self):
        """Alias for compatibility"""
        return self.ollama
        
    def _register_tools(self) -> Dict[str, callable]:
        """Enregistre les outils disponibles pour l'agent"""
        return {
            # === EMPLOYÉS ===
            "liste_employes": {
                "function": self._list_employees,
                "description": "Liste tous les employés de l'organisation",
                "params": []
            },
            "rechercher_employes": {
                "function": self._search_employees,
                "description": "Recherche des employés par nom",
                "params": ["query"]
            },
            "statistiques_rh": {
                "function": self._get_hr_stats,
                "description": "Statistiques RH globales",
                "params": []
            },

            # === DÉPARTEMENTS ===
            "liste_departements": {
                "function": self._list_departments,
                "description": "Liste tous les départements",
                "params": []
            },

            # === INVENTAIRE ===
            "liste_produits": {
                "function": self._list_products,
                "description": "Liste tous les produits en stock",
                "params": []
            },
            "verifier_stock": {
                "function": self._check_stock,
                "description": "Vérifie le stock d'un produit",
                "params": ["product_name"]
            },
            "produits_stock_bas": {
                "function": self._get_low_stock_products,
                "description": "Produits avec stock bas",
                "params": []
            },

            # === VENTES ===
            "ventes_recentes": {
                "function": self._get_recent_sales,
                "description": "Liste des ventes récentes",
                "params": ["limit"]
            },
            "statistiques_ventes": {
                "function": self._get_sales_stats,
                "description": "Statistiques des ventes",
                "params": ["days"]
            },

            # === CLIENTS ===
            "liste_clients": {
                "function": self._list_customers,
                "description": "Liste tous les clients",
                "params": []
            },
        }
    
    def _get_tools_description(self) -> str:
        """Génère la description des outils pour le prompt"""
        descriptions = []
        for name, tool in self.tools.items():
            params = ", ".join(tool["params"]) if tool["params"] else "aucun"
            descriptions.append(f"- {name}: {tool['description']} (params: {params})")
        return "\n".join(descriptions)

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles sur Ollama"""
        return self.ollama.list_models()

    def get_provider_info(self) -> Dict:
        """Get provider info"""
        return self.ollama.get_provider_info()

    def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None,
        agent_mode: bool = False
    ) -> Dict:
        """
        Envoie un message à l'agent IA
        
        Args:
            message: Message de l'utilisateur
            conversation_history: Historique de conversation
            agent_mode: Active l'exécution des outils
        """
        start_time = time.time()

        # Vérifier disponibilité
        if not self.ollama.available:
            return self._fallback_response(message, agent_mode)

        try:
            # Construire le prompt système
            org_name = self.organization.name if self.organization else "Non définie"
            
            if agent_mode:
                system_prompt = self.AGENT_SYSTEM_PROMPT.format(
                    org_name=org_name,
                    tools_description=self._get_tools_description()
                )
            else:
                system_prompt = self.SYSTEM_PROMPT.format(org_name=org_name)
            
            # Construire les messages
            messages = [LLMMessage(role="system", content=system_prompt)]
            
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append(LLMMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", "")
                    ))
            
            messages.append(LLMMessage(role="user", content=message))
            
            # Appeler Ollama
            response = self.ollama.chat(
                messages=messages,
                temperature=ai_config.TEMPERATURE,
                max_tokens=ai_config.MAX_TOKENS,
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
            
            # Traiter les actions en mode agent
            if agent_mode and "<action>" in content:
                content, tool_calls, tool_results = self._process_agent_actions(content)
                
                # Si des outils ont été exécutés, générer la réponse finale
                if tool_results:
                    results_data = self._format_tool_results_for_ai(tool_results)
                    
                    messages.append(LLMMessage(role="assistant", content=content))
                    messages.append(LLMMessage(
                        role="user",
                        content=f"""⛔ RAPPEL - ZÉRO HALLUCINATION:
Réponds UNIQUEMENT avec les données ci-dessous.

DONNÉES RÉELLES:
{results_data}

RÈGLES:
1. Cite UNIQUEMENT les chiffres exacts présents
2. Si info absente → dis "non disponible"
3. Maximum 3 phrases, format: Donnée → Insight
4. **Gras** pour les chiffres + émojis

Formule ta réponse:"""
                    ))
                    
                    final_response = self.ollama.chat(
                        messages=messages,
                        temperature=ai_config.TEMPERATURE,
                        max_tokens=ai_config.MAX_TOKENS,
                    )
                    content = final_response.content if final_response.success else content
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "content": content,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "response_time_ms": response_time,
                "model": self.model,
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
        """Parse et exécute les actions demandées par l'agent"""
        tool_calls = []
        tool_results = []
        
        # Regex pour trouver les blocs <action>...</action>
        action_pattern = r'<action>(.*?)</action>'
        matches = re.findall(action_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                action = json.loads(match.strip())
                tool_name = action.get("tool")
                params = action.get("params", {})
                
                if tool_name in self.tools:
                    tool_calls.append({"tool": tool_name, "params": params})
                    
                    # Exécuter l'outil
                    tool_func = self.tools[tool_name]["function"]
                    if params:
                        result = tool_func(**params)
                    else:
                        result = tool_func()
                    
                    tool_results.append({
                        "tool": tool_name,
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    })
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                tool_results.append({
                    "tool": tool_name if 'tool_name' in locals() else "unknown",
                    "success": False,
                    "error": str(e),
                })
        
        # Nettoyer le contenu des balises action
        clean_content = re.sub(action_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        
        return clean_content, tool_calls, tool_results

    def _format_tool_results_for_ai(self, tool_results: List[Dict]) -> str:
        """Formate les résultats des outils pour l'IA"""
        formatted = []
        for result in tool_results:
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    formatted.append(f"📊 {result['tool']}: {len(data)} résultats")
                    for item in data[:5]:  # Limiter
                        formatted.append(f"  • {json.dumps(item, ensure_ascii=False, default=str)[:200]}")
                else:
                    formatted.append(f"📊 {result['tool']}: {json.dumps(data, ensure_ascii=False, default=str)[:500]}")
            else:
                formatted.append(f"❌ {result['tool']}: {result.get('error', 'Erreur inconnue')}")
        
        return "\n".join(formatted) if formatted else "Aucune donnée trouvée"

    def _fallback_response(self, message: str, agent_mode: bool) -> Dict:
        """Réponse de secours si Ollama n'est pas disponible"""
        content = """🤖 **Assistant IA**

⚠️ Le modèle IA local (Ollama) n'est pas disponible.

**Pour activer l'IA locale:**
1. Installez Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Démarrez le service: `ollama serve`
3. Téléchargez un modèle: `ollama pull llama3.2`
4. Installez le package Python: `pip install ollama`

Redémarrez ensuite le serveur Django."""
        
        return {
            "success": True,
            "content": content,
            "tool_calls": [],
            "tool_results": [],
            "response_time_ms": 0,
            "model": "fallback",
        }

    # ==================== OUTILS MÉTIER ====================
    
    def _list_employees(self) -> ToolResult:
        """Liste tous les employés"""
        start = time.time()
        try:
            from hr.models import Employee
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(organization=self.organization)[:20]
            
            results = [
                {
                    "nom": f"{e.first_name} {e.last_name}",
                    "email": e.email,
                    "poste": str(e.position) if e.position else "Non défini",
                    "departement": e.department.name if e.department else "Non assigné",
                    "statut": e.employment_status or "actif",
                }
                for e in employees
            ]
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _search_employees(self, query: str = "") -> ToolResult:
        """Recherche des employés"""
        start = time.time()
        try:
            from hr.models import Employee
            from django.db.models import Q
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(organization=self.organization)
            
            if query:
                employees = employees.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query)
                )
            
            employees = employees[:10]
            
            results = [
                {
                    "nom": e.full_name,
                    "email": e.email,
                    "poste": e.position.title if e.position else None,
                    "departement": e.department.name if e.department else None,
                }
                for e in employees
            ]
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_hr_stats(self) -> ToolResult:
        """Statistiques RH"""
        start = time.time()
        try:
            from hr.models import Employee, Department
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(organization=self.organization)
            
            stats = {
                "total_employes": employees.count(),
                "employes_actifs": employees.filter(employment_status='active').count(),
                "en_conge": employees.filter(employment_status='on_leave').count(),
                "total_departements": Department.objects.filter(organization=self.organization).count(),
            }
            
            return ToolResult(success=True, data=stats, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _list_departments(self) -> ToolResult:
        """Liste les départements"""
        start = time.time()
        try:
            from hr.models import Department
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            departments = Department.objects.filter(organization=self.organization, is_active=True)
            
            results = [
                {"nom": d.name, "code": d.code, "description": d.description}
                for d in departments
            ]
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
    
    def _list_products(self) -> ToolResult:
        """Liste tous les produits"""
        start = time.time()
        try:
            from inventory.models import Product, Stock
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            products = Product.objects.filter(organization=self.organization)[:20]
            
            results = []
            for p in products:
                stocks = Stock.objects.filter(product=p)
                total_qty = sum(s.quantity for s in stocks)
                results.append({
                    "nom": p.name,
                    "sku": p.sku,
                    "categorie": p.category.name if p.category else "Non catégorisé",
                    "prix": float(p.selling_price) if p.selling_price else 0,
                    "stock": total_qty,
                })
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _check_stock(self, product_name: str = "") -> ToolResult:
        """Vérifie le stock d'un produit"""
        start = time.time()
        try:
            from inventory.models import Product, Stock
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            products = Product.objects.filter(organization=self.organization)
            
            if product_name:
                products = products.filter(name__icontains=product_name)
            
            products = products[:5]
            
            results = []
            for p in products:
                stocks = Stock.objects.filter(product=p)
                total_qty = sum(s.quantity for s in stocks)
                results.append({
                    "produit": p.name,
                    "sku": p.sku,
                    "stock_total": total_qty,
                    "stock_min": p.min_stock_level,
                    "alerte": total_qty <= p.min_stock_level if p.min_stock_level else False,
                })
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_low_stock_products(self) -> ToolResult:
        """Produits avec stock bas"""
        start = time.time()
        try:
            from inventory.models import Product, Stock
            from django.db.models import Sum
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            products = Product.objects.filter(
                organization=self.organization,
                min_stock_level__isnull=False
            ).annotate(
                total_stock=Sum('stocks__quantity')
            )
            
            results = []
            for p in products:
                total = p.total_stock or 0
                if total <= p.min_stock_level:
                    results.append({
                        "produit": p.name,
                        "stock_actuel": total,
                        "stock_min": p.min_stock_level,
                        "manque": p.min_stock_level - total,
                    })
            
            return ToolResult(success=True, data=results[:10], execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_recent_sales(self, limit: int = 10) -> ToolResult:
        """Ventes récentes"""
        start = time.time()
        try:
            from inventory.models import Sale
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            sales = Sale.objects.filter(organization=self.organization).order_by('-created_at')[:limit]
            
            results = [
                {
                    "numero": s.sale_number,
                    "client": s.customer.name if s.customer else "Anonyme",
                    "total": float(s.total_amount),
                    "statut": s.status,
                    "date": str(s.created_at.date()),
                }
                for s in sales
            ]
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_sales_stats(self, days: int = 30) -> ToolResult:
        """Statistiques des ventes"""
        start = time.time()
        try:
            from inventory.models import Sale
            from django.utils import timezone
            from django.db.models import Sum, Count
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            start_date = timezone.now() - timezone.timedelta(days=days)
            sales = Sale.objects.filter(
                organization=self.organization,
                created_at__gte=start_date
            )
            
            stats = sales.aggregate(
                total_ca=Sum('total_amount'),
                nombre_ventes=Count('id'),
            )
            
            return ToolResult(
                success=True,
                data={
                    "periode_jours": days,
                    "chiffre_affaires": float(stats['total_ca'] or 0),
                    "nombre_ventes": stats['nombre_ventes'] or 0,
                },
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _list_customers(self) -> ToolResult:
        """Liste les clients"""
        start = time.time()
        try:
            from inventory.models import Customer
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            customers = Customer.objects.filter(organization=self.organization)[:20]
            
            results = [
                {
                    "nom": c.name,
                    "email": c.email,
                    "telephone": c.phone,
                }
                for c in customers
            ]
            
            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
