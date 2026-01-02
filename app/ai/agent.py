# AI Module - Agent Service
"""
Service d'agent IA utilisant Ollama pour les modèles locaux
"""
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


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

    AGENT_SYSTEM_PROMPT = """Tu es l'agent IA de Loura avec accès aux données réelles de l'entreprise.

Organisation: {org_name}

OUTILS DISPONIBLES:
{tools_description}

RÈGLES ABSOLUES - À RESPECTER IMPÉRATIVEMENT:
1. Tu NE DOIS JAMAIS inventer ou halluciner des données.
2. TOUTE donnée que tu mentionnes DOIT provenir d'un outil.
3. Si aucun outil n'a été exécuté, tu DOIS d'abord appeler un outil.
4. Si un outil retourne des données vides, dis "Aucune donnée trouvée".
5. JAMAIS de noms, chiffres ou informations inventés.

FORMAT D'APPEL D'OUTIL:
<action>
{{"tool": "nom_outil", "params": {{}}}}
</action>

OUTILS ET QUAND LES UTILISER:
- liste_employes: Pour lister TOUS les employés
- liste_departements: Pour lister les départements
- liste_produits: Pour lister les produits en stock
- rechercher_employes: Pour chercher un employé spécifique (param: query)
- statistiques_rh: Pour les stats RH globales
- verifier_stock: Pour vérifier un stock produit (param: product_name)
- conges_en_cours: Pour voir qui est en congé
- fiches_paie_recentes: Pour les fiches de paie récentes (param: limit)

IMPORTANT: Réponds UNIQUEMENT avec les données reçues des outils. Aucune invention.
"""

    def __init__(self, organization=None, model: str = None):
        self.organization = organization
        self.model = model or self.DEFAULT_MODEL
        self.tools = self._register_tools()
        
    def _register_tools(self) -> Dict[str, callable]:
        """Enregistre les outils disponibles pour l'agent"""
        return {
            "liste_employes": {
                "function": self._list_employees,
                "description": "Liste tous les employés de l'organisation",
                "params": []
            },
            "rechercher_employes": {
                "function": self._search_employees,
                "description": "Recherche des employés par nom, département ou poste",
                "params": ["query"]
            },
            "statistiques_rh": {
                "function": self._get_hr_stats,
                "description": "Obtient les statistiques RH de l'organisation",
                "params": []
            },
            "liste_departements": {
                "function": self._list_departments,
                "description": "Liste tous les départements de l'organisation",
                "params": []
            },
            "liste_produits": {
                "function": self._list_products,
                "description": "Liste tous les produits en stock",
                "params": []
            },
            "verifier_stock": {
                "function": self._check_stock,
                "description": "Vérifie le stock d'un produit par nom",
                "params": ["product_name"]
            },
            "conges_en_cours": {
                "function": self._get_active_leaves,
                "description": "Liste les employés actuellement en congé",
                "params": []
            },
            "fiches_paie_recentes": {
                "function": self._get_recent_payslips,
                "description": "Récupère les fiches de paie récentes",
                "params": ["limit"]
            },
        }
    
    def _get_tools_description(self) -> str:
        """Génère la description des outils pour le prompt"""
        descriptions = []
        for name, tool in self.tools.items():
            params = ", ".join(tool["params"]) if tool["params"] else "aucun"
            descriptions.append(f"- {name}: {tool['description']} (params: {params})")
        return "\n".join(descriptions)

    # ==================== OUTILS MÉTIER ====================
    
    def _list_employees(self) -> ToolResult:
        """Liste tous les employés de l'organisation"""
        start = time.time()
        try:
            from hr.models import Employee
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(organization=self.organization)[:20]
            
            results = [
                {
                    "id": str(e.id),
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
                    "id": str(p.id),
                    "nom": p.name,
                    "sku": p.sku,
                    "categorie": p.category.name if p.category else "Non catégorisé",
                    "prix": float(p.selling_price) if p.selling_price else 0,
                    "stock": total_qty,
                })
            
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
            
            # Filtrer si une requête est fournie
            if query:
                employees = employees.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query) |
                    Q(employee_id__icontains=query)
                )
            
            employees = employees[:10]
            
            results = [
                {
                    "id": str(e.id),
                    "nom": e.full_name,
                    "email": e.email,
                    "poste": e.position.title if e.position else None,
                    "departement": e.department.name if e.department else None,
                    "statut": e.employment_status,
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

    def _get_hr_stats(self) -> ToolResult:
        """Statistiques RH"""
        start = time.time()
        try:
            from hr.models import Employee, Department
            from django.db import models
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(organization=self.organization)
            
            stats = {
                "total_employes": employees.count(),
                "employes_actifs": employees.filter(employment_status='active').count(),
                "en_conge": employees.filter(employment_status='on_leave').count(),
                "suspendus": employees.filter(employment_status='suspended').count(),
                "total_departements": Department.objects.filter(organization=self.organization).count(),
            }
            
            return ToolResult(
                success=True,
                data=stats,
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _list_departments(self) -> ToolResult:
        """Liste les départements"""
        start = time.time()
        try:
            from hr.models import Department
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            departments = Department.objects.filter(
                organization=self.organization,
                is_active=True
            )
            
            results = [
                {
                    "id": str(d.id),
                    "nom": d.name,
                    "code": d.code,
                    "description": d.description,
                }
                for d in departments
            ]
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=int((time.time() - start) * 1000)
            )
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
            
            # Filtrer si un nom de produit est fourni
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
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_active_leaves(self) -> ToolResult:
        """Récupère les congés en cours"""
        start = time.time()
        try:
            from hr.models import LeaveRequest
            from django.utils import timezone
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            today = timezone.now().date()
            leaves = LeaveRequest.objects.filter(
                employee__organization=self.organization,
                status='approved',
                start_date__lte=today,
                end_date__gte=today
            )[:20]
            
            results = [
                {
                    "employe": l.employee.full_name,
                    "type": l.leave_type.name if l.leave_type else "N/A",
                    "debut": str(l.start_date),
                    "fin": str(l.end_date),
                }
                for l in leaves
            ]
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_recent_payslips(self, limit: int = 10) -> ToolResult:
        """Récupère les fiches de paie récentes"""
        start = time.time()
        try:
            from hr.models import Payroll
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            payslips = Payroll.objects.filter(
                employee__organization=self.organization
            ).order_by('-created_at')[:limit]
            
            results = [
                {
                    "employe": p.employee.full_name,
                    "periode": p.payroll_period.name if p.payroll_period else "N/A",
                    "net": float(p.net_salary),
                    "statut": p.status,
                }
                for p in payslips
            ]
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=int((time.time() - start) * 1000)
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # ==================== MÉTHODES PRINCIPALES ====================

    def chat(self, message: str, conversation_history: List[Dict] = None, agent_mode: bool = False) -> Dict:
        """
        Envoie un message au modèle et retourne la réponse
        """
        start_time = time.time()
        
        if not OLLAMA_AVAILABLE:
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
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Garder les 10 derniers messages
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            messages.append({"role": "user", "content": message})
            
            # Appel à Ollama
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            # Nouvelle API Ollama: response.message.content au lieu de dict
            content = response.message.content if hasattr(response, 'message') else str(response)
            
            # Si mode agent, traiter les actions
            tool_calls = []
            tool_results = []
            
            if agent_mode and "<action>" in content:
                _, tool_calls, tool_results = self._process_agent_actions(content)
                
                # Si des outils ont été exécutés, rappeler l'IA avec les résultats réels
                if tool_results:
                    # Construire le message avec les résultats réels
                    results_data = self._format_tool_results_for_ai(tool_results)
                    
                    # Ajouter la réponse précédente et les résultats
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user", 
                        "content": f"""Voici les données RÉELLES récupérées par les outils. 
Réponds à l'utilisateur en utilisant UNIQUEMENT ces données. 
NE JAMAIS inventer de données supplémentaires.

DONNÉES RÉELLES:
{results_data}

Formule une réponse claire et concise basée UNIQUEMENT sur ces données."""
                    })
                    
                    # Deuxième appel pour obtenir la réponse finale
                    final_response = ollama.chat(
                        model=self.model,
                        messages=messages
                    )
                    content = final_response.message.content if hasattr(final_response, 'message') else str(final_response)
            
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
                "content": f"Erreur de communication avec le modèle IA: {str(e)}",
                "error": str(e),
                "response_time_ms": int((time.time() - start_time) * 1000),
            }
    
    def _format_tool_results_for_ai(self, tool_results: List[Dict]) -> str:
        """Formate les résultats des outils pour l'IA de manière lisible"""
        formatted = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    if len(data) == 0:
                        formatted.append(f"[{tool_name}] Aucune donnée trouvée.")
                    else:
                        items = []
                        for item in data:
                            if isinstance(item, dict):
                                # Formater chaque item de manière lisible
                                item_str = ", ".join([f"{k}: {v}" for k, v in item.items() if v])
                                items.append(f"  - {item_str}")
                            else:
                                items.append(f"  - {item}")
                        formatted.append(f"[{tool_name}] {len(data)} résultat(s):\n" + "\n".join(items))
                elif isinstance(data, dict):
                    items = [f"  - {k}: {v}" for k, v in data.items()]
                    formatted.append(f"[{tool_name}] Données:\n" + "\n".join(items))
                else:
                    formatted.append(f"[{tool_name}] {data}")
            else:
                error = result.get("error", "Erreur inconnue")
                formatted.append(f"[{tool_name}] Erreur: {error}")
        
        return "\n\n".join(formatted)

    def _process_agent_actions(self, content: str) -> tuple:
        """Traite les actions demandées par l'agent"""
        import re
        
        tool_calls = []
        tool_results = []
        
        # Essayer plusieurs patterns pour extraire les actions
        # Pattern 1: JSON entre balises <action>
        action_pattern = r'<action>\s*(.*?)\s*</action>'
        matches = re.findall(action_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                # Essayer de parser comme JSON
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
                # Essayer de parser comme XML-like: <tool_name /> ou <tool_name></tool_name>
                inner_match = re.search(r'<(\w+)\s*/>', match) or re.search(r'<(\w+)>', match)
                if inner_match:
                    tool_name = inner_match.group(1)
                    if tool_name in self.tools:
                        tool_calls.append({"tool": tool_name, "params": {}})
                        tool_func = self.tools[tool_name]["function"]
                        result = tool_func()
                        tool_results.append({
                            "tool": tool_name,
                            "success": result.success,
                            "data": result.data,
                            "error": result.error,
                        })
                continue
            except Exception as e:
                tool_results.append({
                    "tool": tool_name if 'tool_name' in locals() else "unknown",
                    "success": False,
                    "error": str(e),
                })
        
        # Si aucune action JSON trouvée, chercher des mentions directes d'outils
        if not tool_results:
            for tool_name in self.tools.keys():
                # Chercher le nom de l'outil mentionné directement
                if f"<{tool_name}" in content.lower() or f'"{tool_name}"' in content:
                    tool_calls.append({"tool": tool_name, "params": {}})
                    tool_func = self.tools[tool_name]["function"]
                    result = tool_func()
                    tool_results.append({
                        "tool": tool_name,
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    })
                    break  # Un seul outil à la fois pour éviter la confusion
        
        # Nettoyer le contenu des balises action
        clean_content = re.sub(action_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        
        return clean_content, tool_calls, tool_results

    def _fallback_response(self, message: str, agent_mode: bool) -> Dict:
        """Réponse de secours si Ollama n'est pas disponible"""
        if agent_mode:
            content = """🤖 **Mode Agent**

⚠️ Le modèle IA local (Ollama) n'est pas disponible.

Pour activer l'IA locale:
1. Installez Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Démarrez le service: `ollama serve`
3. Téléchargez un modèle: `ollama pull llama3.2`
4. Installez le package Python: `pip install ollama`

En attendant, je peux simuler certaines actions basiques."""
        else:
            content = """👋 Bonjour !

Je suis l'assistant IA de Loura, mais le modèle local n'est pas encore configuré.

**Pour activer l'IA locale:**
1. Installez Ollama
2. Téléchargez un modèle (llama3.2, mistral, etc.)
3. Redémarrez le serveur

En attendant, n'hésitez pas à explorer l'application ! 🚀"""
        
        return {
            "success": True,
            "content": content,
            "tool_calls": [],
            "tool_results": [],
            "response_time_ms": 0,
            "model": "fallback",
        }

    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles sur Ollama"""
        if not OLLAMA_AVAILABLE:
            return []
        
        try:
            result = ollama.list()
            # Nouvelle API Ollama: result.models au lieu de result.get("models")
            if hasattr(result, 'models'):
                return [m.model for m in result.models if hasattr(m, 'model')]
            return []
        except Exception:
            return []
