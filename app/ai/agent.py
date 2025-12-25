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
Tu aides les utilisateurs à gérer leurs ressources humaines, inventaire, paie et plus.

Contexte de l'organisation: {org_name}

Tu peux:
- Répondre aux questions sur les données de l'entreprise
- Aider à créer, modifier ou supprimer des enregistrements
- Fournir des statistiques et analyses
- Guider les utilisateurs dans l'utilisation de l'application

Réponds toujours en français de manière professionnelle mais amicale.
Utilise des emojis avec modération pour rendre les réponses plus engageantes.
"""

    AGENT_SYSTEM_PROMPT = """Tu es l'agent IA autonome de Loura avec la capacité d'exécuter des actions.

Organisation: {org_name}

Tu as accès aux outils suivants:
{tools_description}

Quand l'utilisateur te demande d'effectuer une action:
1. Analyse la demande
2. Utilise les outils appropriés
3. Rapporte le résultat

Format de réponse pour les actions:
<action>
{"tool": "nom_outil", "params": {"param1": "valeur1"}}
</action>

Réponds toujours en français.
"""

    def __init__(self, organization=None, model: str = None):
        self.organization = organization
        self.model = model or self.DEFAULT_MODEL
        self.tools = self._register_tools()
        
    def _register_tools(self) -> Dict[str, callable]:
        """Enregistre les outils disponibles pour l'agent"""
        return {
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
    
    def _search_employees(self, query: str) -> ToolResult:
        """Recherche des employés"""
        start = time.time()
        try:
            from hr.models import Employee
            from django.db.models import Q
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            employees = Employee.objects.filter(
                organization=self.organization
            ).filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(employee_id__icontains=query)
            )[:10]
            
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

    def _check_stock(self, product_name: str) -> ToolResult:
        """Vérifie le stock d'un produit"""
        start = time.time()
        try:
            from inventory.models import Product, Stock
            
            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")
            
            products = Product.objects.filter(
                organization=self.organization,
                name__icontains=product_name
            )[:5]
            
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
                content, tool_calls, tool_results = self._process_agent_actions(content)
            
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

    def _process_agent_actions(self, content: str) -> tuple:
        """Traite les actions demandées par l'agent"""
        import re
        
        tool_calls = []
        tool_results = []
        
        # Extraire les actions du contenu
        action_pattern = r'<action>(.*?)</action>'
        matches = re.findall(action_pattern, content, re.DOTALL)
        
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
        clean_content = re.sub(action_pattern, '', content, flags=re.DOTALL).strip()
        
        # Ajouter les résultats au contenu si des actions ont été exécutées
        if tool_results:
            results_text = "\n\n📊 **Résultats des actions:**\n"
            for result in tool_results:
                if result["success"]:
                    results_text += f"✅ {result['tool']}: {json.dumps(result['data'], ensure_ascii=False, indent=2)}\n"
                else:
                    results_text += f"❌ {result['tool']}: {result['error']}\n"
            clean_content += results_text
        
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
