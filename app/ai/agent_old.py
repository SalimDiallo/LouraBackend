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

    def __init__(self, organization=None, model: str = None):
        self.organization = organization
        self.model = model or self.DEFAULT_MODEL
        self.tools = self._register_tools()
        
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
                "description": "Recherche des employés par nom, département ou poste",
                "params": ["query"]
            },
            "details_employe": {
                "function": self._get_employee_details,
                "description": "Obtient les détails complets d'un employé par son nom",
                "params": ["employee_name"]
            },
            "statistiques_rh": {
                "function": self._get_hr_stats,
                "description": "Obtient les statistiques RH globales de l'organisation",
                "params": []
            },

            # === DÉPARTEMENTS ===
            "liste_departements": {
                "function": self._list_departments,
                "description": "Liste tous les départements de l'organisation",
                "params": []
            },
            "details_departement": {
                "function": self._get_department_details,
                "description": "Détails d'un département avec ses employés",
                "params": ["department_name"]
            },

            # === POSTES ===
            "liste_postes": {
                "function": self._list_positions,
                "description": "Liste tous les postes/fonctions de l'organisation",
                "params": []
            },

            # === CONGÉS ===
            "conges_en_cours": {
                "function": self._get_active_leaves,
                "description": "Liste les employés actuellement en congé",
                "params": []
            },
            "demandes_conges_en_attente": {
                "function": self._get_pending_leave_requests,
                "description": "Liste les demandes de congé en attente d'approbation",
                "params": []
            },
            "historique_conges": {
                "function": self._get_leave_history,
                "description": "Historique des congés sur une période",
                "params": ["limit"]
            },
            "soldes_conges": {
                "function": self._get_leave_balances,
                "description": "Soldes de congés des employés pour l'année en cours",
                "params": []
            },

            # === PAIE ===
            "fiches_paie_recentes": {
                "function": self._get_recent_payslips,
                "description": "Récupère les fiches de paie récentes",
                "params": ["limit"]
            },
            "statistiques_paie": {
                "function": self._get_payroll_stats,
                "description": "Statistiques globales de la paie",
                "params": []
            },
            "avances_salaire": {
                "function": self._get_payroll_advances,
                "description": "Liste des avances sur salaire",
                "params": ["status"]
            },

            # === POINTAGE ===
            "pointages_du_jour": {
                "function": self._get_today_attendances,
                "description": "Pointages du jour en cours",
                "params": []
            },
            "statistiques_pointage": {
                "function": self._get_attendance_stats,
                "description": "Statistiques de pointage sur une période",
                "params": ["days"]
            },

            # === INVENTAIRE - PRODUITS ===
            "liste_produits": {
                "function": self._list_products,
                "description": "Liste tous les produits en stock",
                "params": []
            },
            "rechercher_produits": {
                "function": self._search_products,
                "description": "Recherche des produits par nom ou SKU",
                "params": ["query"]
            },
            "details_produit": {
                "function": self._get_product_details,
                "description": "Détails complets d'un produit avec son stock",
                "params": ["product_name"]
            },
            "produits_stock_bas": {
                "function": self._get_low_stock_products,
                "description": "Liste des produits avec stock bas (alerte)",
                "params": []
            },
            "verifier_stock": {
                "function": self._check_stock,
                "description": "Vérifie le stock d'un produit par nom",
                "params": ["product_name"]
            },

            # === INVENTAIRE - CATÉGORIES ===
            "liste_categories": {
                "function": self._list_categories,
                "description": "Liste toutes les catégories de produits",
                "params": []
            },

            # === INVENTAIRE - ENTREPÔTS ===
            "liste_entrepots": {
                "function": self._list_warehouses,
                "description": "Liste tous les entrepôts",
                "params": []
            },

            # === INVENTAIRE - MOUVEMENTS ===
            "mouvements_stock_recents": {
                "function": self._get_recent_movements,
                "description": "Mouvements de stock récents (entrées/sorties)",
                "params": ["limit"]
            },

            # === VENTES ===
            "ventes_recentes": {
                "function": self._get_recent_sales,
                "description": "Liste des ventes récentes",
                "params": ["limit"]
            },
            "statistiques_ventes": {
                "function": self._get_sales_stats,
                "description": "Statistiques des ventes (total, nombre, CA)",
                "params": ["days"]
            },
            "top_produits_vendus": {
                "function": self._get_top_selling_products,
                "description": "Produits les plus vendus",
                "params": ["limit"]
            },
            "ventes_a_credit": {
                "function": self._get_credit_sales,
                "description": "Ventes à crédit en cours",
                "params": []
            },

            # === CLIENTS ===
            "liste_clients": {
                "function": self._list_customers,
                "description": "Liste tous les clients",
                "params": []
            },
            "rechercher_clients": {
                "function": self._search_customers,
                "description": "Recherche des clients par nom",
                "params": ["query"]
            },
            "clients_avec_dettes": {
                "function": self._get_customers_with_debt,
                "description": "Clients ayant des dettes en cours",
                "params": []
            },

            # === FOURNISSEURS ===
            "liste_fournisseurs": {
                "function": self._list_suppliers,
                "description": "Liste tous les fournisseurs",
                "params": []
            },

            # === COMMANDES ===
            "commandes_fournisseurs": {
                "function": self._get_supplier_orders,
                "description": "Commandes fournisseurs en cours",
                "params": ["status"]
            },

            # === DÉPENSES ===
            "depenses_recentes": {
                "function": self._get_recent_expenses,
                "description": "Dépenses récentes de l'entreprise",
                "params": ["limit"]
            },
            "statistiques_depenses": {
                "function": self._get_expense_stats,
                "description": "Statistiques des dépenses par période",
                "params": ["days"]
            },

            # === RAPPORTS FINANCIERS ===
            "bilan_financier": {
                "function": self._get_financial_summary,
                "description": "Bilan financier global (ventes, dépenses, profit)",
                "params": ["days"]
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
            from hr.models import Payslip

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            payslips = Payslip.objects.filter(
                employee__organization=self.organization
            ).order_by('-payroll_period__start_date')[:limit]

            results = [
                {
                    "employe": p.employee.get_full_name(),
                    "periode": p.payroll_period.name if p.payroll_period else "N/A",
                    "base": float(p.base_salary),
                    "brut": float(p.gross_salary),
                    "deductions": float(p.total_deductions),
                    "net": float(p.net_salary),
                    "statut": p.get_status_display(),
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

    # ==================== NOUVELLES FONCTIONS ====================

    # === EMPLOYÉS ===
    def _get_employee_details(self, employee_name: str = "") -> ToolResult:
        """Détails complets d'un employé"""
        start = time.time()
        try:
            from hr.models import Employee
            from django.db.models import Q

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            employee = Employee.objects.filter(
                Q(first_name__icontains=employee_name) | Q(last_name__icontains=employee_name),
                organization=self.organization
            ).first()

            if not employee:
                return ToolResult(success=False, data=None, error=f"Employé '{employee_name}' non trouvé")

            result = {
                "nom_complet": employee.get_full_name(),
                "email": employee.email,
                "telephone": employee.phone,
                "matricule": employee.employee_id,
                "poste": employee.position.title if employee.position else None,
                "departement": employee.department.name if employee.department else None,
                "manager": employee.manager.get_full_name() if employee.manager else None,
                "date_embauche": str(employee.hire_date) if employee.hire_date else None,
                "statut": employee.get_employment_status_display(),
                "role": employee.assigned_role.name if employee.assigned_role else None,
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === DÉPARTEMENTS ===
    def _get_department_details(self, department_name: str = "") -> ToolResult:
        """Détails d'un département avec ses employés"""
        start = time.time()
        try:
            from hr.models import Department, Employee

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            department = Department.objects.filter(
                name__icontains=department_name,
                organization=self.organization
            ).first()

            if not department:
                return ToolResult(success=False, data=None, error=f"Département '{department_name}' non trouvé")

            employees = Employee.objects.filter(department=department, organization=self.organization)

            result = {
                "nom": department.name,
                "code": department.code,
                "description": department.description,
                "responsable": department.head.get_full_name() if department.head else None,
                "nombre_employes": employees.count(),
                "employes": [
                    {
                        "nom": e.get_full_name(),
                        "poste": e.position.title if e.position else None,
                        "statut": e.get_employment_status_display()
                    }
                    for e in employees[:10]
                ]
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === POSTES ===
    def _list_positions(self) -> ToolResult:
        """Liste tous les postes"""
        start = time.time()
        try:
            from hr.models import Position

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            positions = Position.objects.filter(organization=self.organization, is_active=True)

            results = [
                {
                    "titre": p.title,
                    "code": p.code,
                    "salaire_min": float(p.min_salary) if p.min_salary else None,
                    "salaire_max": float(p.max_salary) if p.max_salary else None,
                    "employes": p.employees.count()
                }
                for p in positions
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === CONGÉS ===
    def _get_pending_leave_requests(self) -> ToolResult:
        """Demandes de congé en attente"""
        start = time.time()
        try:
            from hr.models import LeaveRequest

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            requests = LeaveRequest.objects.filter(
                employee__organization=self.organization,
                status='pending'
            ).order_by('-created_at')[:20]

            results = [
                {
                    "employe": r.employee.get_full_name(),
                    "type": r.leave_type.name,
                    "debut": str(r.start_date),
                    "fin": str(r.end_date),
                    "jours": float(r.total_days),
                    "raison": r.reason[:100] if r.reason else None
                }
                for r in requests
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_leave_history(self, limit: int = 20) -> ToolResult:
        """Historique des congés"""
        start = time.time()
        try:
            from hr.models import LeaveRequest

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            requests = LeaveRequest.objects.filter(
                employee__organization=self.organization
            ).order_by('-created_at')[:limit]

            results = [
                {
                    "employe": r.employee.get_full_name(),
                    "type": r.leave_type.name,
                    "debut": str(r.start_date),
                    "fin": str(r.end_date),
                    "jours": float(r.total_days),
                    "statut": r.get_status_display()
                }
                for r in requests
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_leave_balances(self) -> ToolResult:
        """Soldes de congés des employés"""
        start = time.time()
        try:
            from hr.models import LeaveBalance
            from datetime import datetime

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            current_year = datetime.now().year
            balances = LeaveBalance.objects.filter(
                employee__organization=self.organization,
                year=current_year
            )[:20]

            results = [
                {
                    "employe": b.employee.get_full_name(),
                    "type_conge": b.leave_type.name,
                    "total": float(b.total_days),
                    "utilises": float(b.used_days),
                    "en_attente": float(b.pending_days),
                    "disponibles": float(b.available_days)
                }
                for b in balances
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === PAIE ===
    def _get_payroll_stats(self) -> ToolResult:
        """Statistiques globales de la paie"""
        start = time.time()
        try:
            from hr.models import Payslip
            from django.db.models import Sum, Avg, Count
            from datetime import datetime, timedelta

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            current_month = datetime.now().replace(day=1)
            payslips = Payslip.objects.filter(
                employee__organization=self.organization,
                payroll_period__start_date__gte=current_month
            )

            stats = payslips.aggregate(
                total_brut=Sum('gross_salary'),
                total_net=Sum('net_salary'),
                total_deductions=Sum('total_deductions'),
                nombre_fiches=Count('id'),
                salaire_moyen=Avg('net_salary')
            )

            result = {
                "nombre_fiches_paie": stats['nombre_fiches'] or 0,
                "total_salaire_brut": float(stats['total_brut'] or 0),
                "total_salaire_net": float(stats['total_net'] or 0),
                "total_deductions": float(stats['total_deductions'] or 0),
                "salaire_moyen": float(stats['salaire_moyen'] or 0)
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_payroll_advances(self, status: str = "pending") -> ToolResult:
        """Liste des avances sur salaire"""
        start = time.time()
        try:
            from hr.models import PayrollAdvance

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            advances = PayrollAdvance.objects.filter(
                employee__organization=self.organization
            )

            if status:
                advances = advances.filter(status=status)

            advances = advances.order_by('-request_date')[:20]

            results = [
                {
                    "employe": a.employee.get_full_name(),
                    "montant": float(a.amount),
                    "raison": a.reason[:100],
                    "date_demande": str(a.request_date),
                    "statut": a.get_status_display(),
                    "approuve_par": a.approved_by.get_full_name() if a.approved_by else None
                }
                for a in advances
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === POINTAGE ===
    def _get_today_attendances(self) -> ToolResult:
        """Pointages du jour"""
        start = time.time()
        try:
            from hr.models import Attendance
            from datetime import date

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            today = date.today()
            attendances = Attendance.objects.filter(
                organization=self.organization,
                date=today
            ).order_by('-check_in')[:50]

            results = [
                {
                    "employe": a.user_full_name or a.user_email,
                    "arrivee": a.check_in.strftime('%H:%M') if a.check_in else None,
                    "depart": a.check_out.strftime('%H:%M') if a.check_out else None,
                    "heures_travaillees": float(a.total_hours) if a.total_hours else 0,
                    "statut": a.get_status_display()
                }
                for a in attendances
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_attendance_stats(self, days: int = 7) -> ToolResult:
        """Statistiques de pointage"""
        start = time.time()
        try:
            from hr.models import Attendance
            from django.db.models import Count, Avg, Sum
            from datetime import date, timedelta

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            start_date = date.today() - timedelta(days=days)
            attendances = Attendance.objects.filter(
                organization=self.organization,
                date__gte=start_date
            )

            stats = attendances.aggregate(
                total_pointages=Count('id'),
                presents=Count('id', filter=models.Q(status='present')),
                absents=Count('id', filter=models.Q(status='absent')),
                retards=Count('id', filter=models.Q(status='late')),
                heures_moyennes=Avg('total_hours')
            )

            result = {
                "periode_jours": days,
                "total_pointages": stats['total_pointages'] or 0,
                "presents": stats['presents'] or 0,
                "absents": stats['absents'] or 0,
                "retards": stats['retards'] or 0,
                "heures_moyennes_par_jour": float(stats['heures_moyennes'] or 0)
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === PRODUITS ===
    def _search_products(self, query: str = "") -> ToolResult:
        """Recherche de produits"""
        start = time.time()
        try:
            from inventory.models import Product, Stock
            from django.db.models import Q

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            products = Product.objects.filter(organization=self.organization)

            if query:
                products = products.filter(
                    Q(name__icontains=query) | Q(sku__icontains=query)
                )

            products = products[:10]

            results = []
            for p in products:
                total_stock = sum(s.quantity for s in Stock.objects.filter(product=p))
                results.append({
                    "nom": p.name,
                    "sku": p.sku,
                    "categorie": p.category.name if p.category else None,
                    "prix_achat": float(p.purchase_price),
                    "prix_vente": float(p.selling_price),
                    "stock": float(total_stock),
                    "unite": p.get_unit_display()
                })

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_product_details(self, product_name: str = "") -> ToolResult:
        """Détails complets d'un produit"""
        start = time.time()
        try:
            from inventory.models import Product, Stock

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            product = Product.objects.filter(
                name__icontains=product_name,
                organization=self.organization
            ).first()

            if not product:
                return ToolResult(success=False, data=None, error=f"Produit '{product_name}' non trouvé")

            stocks = Stock.objects.filter(product=product)
            total_stock = sum(s.quantity for s in stocks)

            result = {
                "nom": product.name,
                "sku": product.sku,
                "description": product.description,
                "categorie": product.category.name if product.category else None,
                "prix_achat": float(product.purchase_price),
                "prix_vente": float(product.selling_price),
                "unite": product.get_unit_display(),
                "stock_total": float(total_stock),
                "stock_min": float(product.min_stock_level),
                "stock_max": float(product.max_stock_level),
                "alerte_stock_bas": total_stock <= product.min_stock_level,
                "stocks_par_entrepot": [
                    {
                        "entrepot": s.warehouse.name,
                        "quantite": float(s.quantity),
                        "emplacement": s.location
                    }
                    for s in stocks
                ]
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
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

            products = Product.objects.filter(organization=self.organization)
            low_stock = []

            for p in products:
                total_stock = Stock.objects.filter(product=p).aggregate(Sum('quantity'))['quantity__sum'] or 0
                if p.min_stock_level and total_stock <= p.min_stock_level:
                    low_stock.append({
                        "nom": p.name,
                        "sku": p.sku,
                        "stock_actuel": float(total_stock),
                        "stock_min": float(p.min_stock_level),
                        "categorie": p.category.name if p.category else None
                    })

            return ToolResult(success=True, data=low_stock, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === CATÉGORIES ===
    def _list_categories(self) -> ToolResult:
        """Liste des catégories de produits"""
        start = time.time()
        try:
            from inventory.models import Category

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            categories = Category.objects.filter(organization=self.organization, is_active=True)

            results = [
                {
                    "nom": c.name,
                    "code": c.code,
                    "description": c.description,
                    "nombre_produits": c.products.count()
                }
                for c in categories
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === ENTREPÔTS ===
    def _list_warehouses(self) -> ToolResult:
        """Liste des entrepôts"""
        start = time.time()
        try:
            from inventory.models import Warehouse

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            warehouses = Warehouse.objects.filter(organization=self.organization, is_active=True)

            results = [
                {
                    "nom": w.name,
                    "code": w.code,
                    "ville": w.city,
                    "responsable": w.manager_name,
                    "telephone": w.phone
                }
                for w in warehouses
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === MOUVEMENTS ===
    def _get_recent_movements(self, limit: int = 20) -> ToolResult:
        """Mouvements de stock récents"""
        start = time.time()
        try:
            from inventory.models import Movement

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            movements = Movement.objects.filter(
                organization=self.organization
            ).order_by('-movement_date')[:limit]

            results = [
                {
                    "type": m.get_movement_type_display(),
                    "produit": m.product.name,
                    "quantite": float(m.quantity),
                    "entrepot": m.warehouse.name,
                    "date": m.movement_date.strftime('%Y-%m-%d %H:%M'),
                    "reference": m.reference
                }
                for m in movements
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === VENTES ===
    def _get_recent_sales(self, limit: int = 20) -> ToolResult:
        """Ventes récentes"""
        start = time.time()
        try:
            from inventory.models import Sale

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            sales = Sale.objects.filter(
                organization=self.organization
            ).order_by('-sale_date')[:limit]

            results = [
                {
                    "numero": s.sale_number,
                    "client": s.customer.name if s.customer else "Client occasionnel",
                    "date": s.sale_date.strftime('%Y-%m-%d %H:%M'),
                    "sous_total": float(s.subtotal),
                    "remise": float(s.discount_amount),
                    "tva": float(s.tax_amount),
                    "total": float(s.total_amount),
                    "paye": float(s.paid_amount),
                    "statut": s.get_payment_status_display()
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
            from django.db.models import Sum, Count, Avg
            from datetime import date, timedelta

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            start_date = date.today() - timedelta(days=days)
            sales = Sale.objects.filter(
                organization=self.organization,
                sale_date__gte=start_date
            )

            stats = sales.aggregate(
                nombre_ventes=Count('id'),
                chiffre_affaires=Sum('total_amount'),
                total_paye=Sum('paid_amount'),
                vente_moyenne=Avg('total_amount')
            )

            result = {
                "periode_jours": days,
                "nombre_ventes": stats['nombre_ventes'] or 0,
                "chiffre_affaires": float(stats['chiffre_affaires'] or 0),
                "total_paye": float(stats['total_paye'] or 0),
                "vente_moyenne": float(stats['vente_moyenne'] or 0),
                "creances": float((stats['chiffre_affaires'] or 0) - (stats['total_paye'] or 0))
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_top_selling_products(self, limit: int = 10) -> ToolResult:
        """Produits les plus vendus"""
        start = time.time()
        try:
            from inventory.models import SaleItem
            from django.db.models import Sum, Count

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            top_products = SaleItem.objects.filter(
                sale__organization=self.organization
            ).values(
                'product__name', 'product__sku'
            ).annotate(
                quantite_vendue=Sum('quantity'),
                nombre_ventes=Count('id'),
                chiffre_affaires=Sum('total')
            ).order_by('-quantite_vendue')[:limit]

            results = [
                {
                    "produit": p['product__name'],
                    "sku": p['product__sku'],
                    "quantite_vendue": float(p['quantite_vendue']),
                    "nombre_ventes": p['nombre_ventes'],
                    "chiffre_affaires": float(p['chiffre_affaires'])
                }
                for p in top_products
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_credit_sales(self) -> ToolResult:
        """Ventes à crédit en cours"""
        start = time.time()
        try:
            from inventory.models import CreditSale

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            credit_sales = CreditSale.objects.filter(
                organization=self.organization,
                status__in=['pending', 'partial', 'overdue']
            ).order_by('due_date')[:20]

            results = [
                {
                    "vente": cs.sale.sale_number,
                    "client": cs.customer.name,
                    "montant_total": float(cs.total_amount),
                    "montant_paye": float(cs.paid_amount),
                    "montant_restant": float(cs.remaining_amount),
                    "echeance": str(cs.due_date),
                    "statut": cs.get_status_display()
                }
                for cs in credit_sales
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === CLIENTS ===
    def _list_customers(self) -> ToolResult:
        """Liste tous les clients"""
        start = time.time()
        try:
            from inventory.models import Customer

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            customers = Customer.objects.filter(
                organization=self.organization,
                is_active=True
            )[:50]

            results = [
                {
                    "nom": c.name,
                    "code": c.code,
                    "telephone": c.phone,
                    "email": c.email,
                    "ville": c.city,
                    "limite_credit": float(c.credit_limit)
                }
                for c in customers
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _search_customers(self, query: str = "") -> ToolResult:
        """Recherche de clients"""
        start = time.time()
        try:
            from inventory.models import Customer
            from django.db.models import Q

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            customers = Customer.objects.filter(organization=self.organization)

            if query:
                customers = customers.filter(
                    Q(name__icontains=query) | Q(code__icontains=query) | Q(phone__icontains=query)
                )

            customers = customers[:10]

            results = [
                {
                    "nom": c.name,
                    "code": c.code,
                    "telephone": c.phone,
                    "email": c.email,
                    "ville": c.city
                }
                for c in customers
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_customers_with_debt(self) -> ToolResult:
        """Clients avec dettes"""
        start = time.time()
        try:
            from inventory.models import Customer, CreditSale
            from django.db.models import Sum

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            customers_debt = CreditSale.objects.filter(
                organization=self.organization,
                status__in=['pending', 'partial', 'overdue']
            ).values('customer__name').annotate(
                dette_totale=Sum('remaining_amount')
            ).order_by('-dette_totale')[:20]

            results = [
                {
                    "client": c['customer__name'],
                    "dette_totale": float(c['dette_totale'])
                }
                for c in customers_debt
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === FOURNISSEURS ===
    def _list_suppliers(self) -> ToolResult:
        """Liste des fournisseurs"""
        start = time.time()
        try:
            from inventory.models import Supplier

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            suppliers = Supplier.objects.filter(
                organization=self.organization,
                is_active=True
            )[:50]

            results = [
                {
                    "nom": s.name,
                    "code": s.code,
                    "telephone": s.phone,
                    "email": s.email,
                    "ville": s.city,
                    "contact": s.contact_person
                }
                for s in suppliers
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === COMMANDES ===
    def _get_supplier_orders(self, status: str = "") -> ToolResult:
        """Commandes fournisseurs"""
        start = time.time()
        try:
            from inventory.models import Order

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            orders = Order.objects.filter(organization=self.organization)

            if status:
                orders = orders.filter(status=status)

            orders = orders.order_by('-order_date')[:20]

            results = [
                {
                    "numero": o.order_number,
                    "fournisseur": o.supplier.name,
                    "date_commande": str(o.order_date),
                    "date_livraison_prevue": str(o.expected_delivery_date) if o.expected_delivery_date else None,
                    "montant_total": float(o.total_amount),
                    "statut": o.get_status_display(),
                    "entrepot": o.warehouse.name
                }
                for o in orders
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === DÉPENSES ===
    def _get_recent_expenses(self, limit: int = 20) -> ToolResult:
        """Dépenses récentes"""
        start = time.time()
        try:
            from inventory.models import Expense

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            expenses = Expense.objects.filter(
                organization=self.organization
            ).order_by('-expense_date')[:limit]

            results = [
                {
                    "description": e.description,
                    "montant": float(e.amount),
                    "categorie": e.category.name if e.category else None,
                    "date": str(e.expense_date),
                    "beneficiaire": e.beneficiaire,
                    "mode_paiement": e.get_payment_method_display()
                }
                for e in expenses
            ]

            return ToolResult(success=True, data=results, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def _get_expense_stats(self, days: int = 30) -> ToolResult:
        """Statistiques des dépenses"""
        start = time.time()
        try:
            from inventory.models import Expense
            from django.db.models import Sum, Count, Avg
            from datetime import date, timedelta

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            start_date = date.today() - timedelta(days=days)
            expenses = Expense.objects.filter(
                organization=self.organization,
                expense_date__gte=start_date
            )

            stats = expenses.aggregate(
                total_depenses=Sum('amount'),
                nombre_depenses=Count('id'),
                depense_moyenne=Avg('amount')
            )

            # Dépenses par catégorie
            by_category = expenses.values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')[:5]

            result = {
                "periode_jours": days,
                "total_depenses": float(stats['total_depenses'] or 0),
                "nombre_depenses": stats['nombre_depenses'] or 0,
                "depense_moyenne": float(stats['depense_moyenne'] or 0),
                "top_categories": [
                    {
                        "categorie": cat['category__name'] or "Non catégorisé",
                        "total": float(cat['total'])
                    }
                    for cat in by_category
                ]
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    # === RAPPORTS FINANCIERS ===
    def _get_financial_summary(self, days: int = 30) -> ToolResult:
        """Bilan financier global"""
        start = time.time()
        try:
            from inventory.models import Sale, Expense
            from django.db.models import Sum
            from datetime import date, timedelta

            if not self.organization:
                return ToolResult(success=False, data=None, error="Organisation non définie")

            start_date = date.today() - timedelta(days=days)

            # Ventes
            sales = Sale.objects.filter(
                organization=self.organization,
                sale_date__gte=start_date
            )
            sales_stats = sales.aggregate(
                chiffre_affaires=Sum('total_amount'),
                encaissements=Sum('paid_amount')
            )

            # Dépenses
            expenses = Expense.objects.filter(
                organization=self.organization,
                expense_date__gte=start_date
            )
            expenses_total = expenses.aggregate(total=Sum('amount'))['total'] or 0

            ca = float(sales_stats['chiffre_affaires'] or 0)
            encaisse = float(sales_stats['encaissements'] or 0)
            depenses = float(expenses_total)

            result = {
                "periode_jours": days,
                "chiffre_affaires": ca,
                "encaissements": encaisse,
                "creances": ca - encaisse,
                "depenses": depenses,
                "benefice_brut": ca - depenses,
                "benefice_net": encaisse - depenses
            }

            return ToolResult(success=True, data=result, execution_time_ms=int((time.time() - start) * 1000))
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
                        "content": f"""⛔ RAPPEL CRITIQUE - ZÉRO HALLUCINATION:
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
