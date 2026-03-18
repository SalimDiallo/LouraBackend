"""
AI Tools - HR Module
====================
Outils pour la gestion des ressources humaines.
Inclut des outils de LECTURE (statistiques, listes) et d'ÉCRITURE (création d'employés, etc.)

Pour ajouter un nouvel outil HR:
1. Définir la fonction avec @register_tool
2. Premier argument = organization (automatique)
3. Les autres arguments = paramètres que GPT peut passer
"""

from ai.tools.registry import register_tool


# ============================================================
# OUTILS DE LECTURE (is_read_only=True)
# ============================================================

@register_tool(
    name="liste_employes",
    description="Liste les employés de l'organisation avec leurs informations (nom, email, poste, département, statut). Utilise cet outil quand l'utilisateur demande la liste des employés, combien il y en a, ou cherche un employé.",
    category="hr",
    parameters={
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Terme de recherche optionnel pour filtrer par nom ou email"
            },
            "status": {
                "type": "string",
                "enum": ["active", "inactive", "on_leave", "terminated"],
                "description": "Filtrer par statut d'emploi"
            },
            "department": {
                "type": "string",
                "description": "Filtrer par nom de département"
            },
            "limit": {
                "type": "integer",
                "description": "Nombre maximum de résultats (défaut: 20)",
                "default": 20
            }
        },
        "required": [],
    },
)
def list_employees(organization, search: str = None, status: str = None,
                   department: str = None, limit: int = 20) -> dict:
    """Liste les employés avec filtres optionnels."""
    from hr.models import Employee
    from django.db.models import Q

    qs = Employee.objects.filter(organization=organization)

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    if status:
        qs = qs.filter(employment_status=status)

    if department:
        qs = qs.filter(department__name__icontains=department)

    employees = qs.select_related('department', 'position')[:limit]

    results = []
    for e in employees:
        results.append({
            "id": str(e.id),
            "nom": f"{e.first_name} {e.last_name}",
            "email": e.email,
            "poste": e.position.title if e.position else "Non défini",
            "departement": e.department.name if e.department else "Non assigné",
            "statut": e.employment_status or "actif",
            "telephone": e.phone or "Non renseigné",
        })

    return {
        "total": qs.count(),
        "employes": results,
        "message": f"{len(results)} employé(s) trouvé(s)" + (f" sur {qs.count()}" if qs.count() > len(results) else ""),
    }


@register_tool(
    name="statistiques_rh",
    description="Donne les statistiques globales RH : nombre d'employés, répartition par statut, nombre de départements, congés en cours, etc. Utilise cet outil quand l'utilisateur demande un résumé RH ou des chiffres globaux.",
    category="hr",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_hr_stats(organization) -> dict:
    """Statistiques RH globales."""
    from hr.models import Employee, Department, LeaveRequest
    from django.utils import timezone

    employees = Employee.objects.filter(organization=organization)
    now = timezone.now()

    total = employees.count()
    active = employees.filter(employment_status='active').count()
    on_leave = employees.filter(employment_status='on_leave').count()
    inactive = employees.filter(employment_status='inactive').count()
    terminated = employees.filter(employment_status='terminated').count()
    departments_count = Department.objects.filter(organization=organization, is_active=True).count()

    # Congés en cours
    try:
        pending_leaves = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='pending',
        ).count()
        approved_leaves = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='approved',
            start_date__lte=now.date(),
            end_date__gte=now.date(),
        ).count()
    except Exception:
        pending_leaves = 0
        approved_leaves = 0

    return {
        "total_employes": total,
        "employes_actifs": active,
        "en_conge": on_leave,
        "inactifs": inactive,
        "licencies": terminated,
        "total_departements": departments_count,
        "conges_en_attente": pending_leaves,
        "conges_en_cours": approved_leaves,
    }


@register_tool(
    name="liste_departements",
    description="Liste tous les départements de l'organisation avec leur responsable et nombre d'employés.",
    category="hr",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def list_departments(organization) -> dict:
    """Liste les départements."""
    from hr.models import Department, Employee

    departments = Department.objects.filter(organization=organization, is_active=True)

    results = []
    for d in departments:
        employee_count = Employee.objects.filter(department=d, organization=organization).count()
        results.append({
            "id": str(d.id),
            "nom": d.name,
            "code": d.code or "",
            "description": d.description or "",
            "responsable": d.get_head_name() if hasattr(d, 'get_head_name') else "Non défini",
            "nombre_employes": employee_count,
        })

    return {
        "total": len(results),
        "departements": results,
    }


@register_tool(
    name="conges_en_attente",
    description="Liste les demandes de congé en attente d'approbation. Utile quand l'utilisateur veut voir les congés à approuver.",
    category="hr",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "approved", "rejected"],
                "description": "Filtrer par statut (défaut: pending)",
                "default": "pending"
            }
        },
        "required": [],
    },
)
def list_leave_requests(organization, status: str = "pending") -> dict:
    """Liste les demandes de congé."""
    from hr.models import LeaveRequest

    qs = LeaveRequest.objects.filter(
        employee__organization=organization,
        status=status,
    ).select_related('employee', 'leave_type').order_by('-created_at')[:20]

    results = []
    for lr in qs:
        results.append({
            "id": str(lr.id),
            "employe": f"{lr.employee.first_name} {lr.employee.last_name}",
            "type_conge": lr.leave_type.name if lr.leave_type else (lr.title or "Non spécifié"),
            "date_debut": str(lr.start_date),
            "date_fin": str(lr.end_date),
            "jours": lr.total_days if hasattr(lr, 'total_days') else "N/A",
            "statut": lr.status,
            "raison": lr.reason or "",
        })

    return {
        "total": len(results),
        "demandes": results,
    }


# ============================================================
# OUTILS D'ÉCRITURE (is_read_only=False, requires_confirmation=True)
# ============================================================

@register_tool(
    name="creer_employe",
    description=(
        "Crée un nouvel employé dans l'organisation. "
        "Demande au minimum: prénom, nom, email. "
        "Optionnel: téléphone, département, poste. "
        "Utilise cet outil quand l'utilisateur demande d'ajouter/créer un employé."
    ),
    category="hr",
    parameters={
        "type": "object",
        "properties": {
            "first_name": {
                "type": "string",
                "description": "Prénom de l'employé"
            },
            "last_name": {
                "type": "string",
                "description": "Nom de famille de l'employé"
            },
            "email": {
                "type": "string",
                "description": "Adresse email de l'employé"
            },
            "phone": {
                "type": "string",
                "description": "Numéro de téléphone (optionnel)"
            },
            "department_name": {
                "type": "string",
                "description": "Nom du département (optionnel, doit exister)"
            },
            "position_title": {
                "type": "string",
                "description": "Titre du poste (optionnel, doit exister)"
            },
        },
        "required": ["first_name", "last_name", "email"],
    },
    requires_confirmation=False,
    is_read_only=False,
)
def create_employee(organization, first_name: str, last_name: str, email: str,
                    phone: str = None, department_name: str = None,
                    position_title: str = None) -> dict:
    """Crée un nouvel employé."""
    from hr.models import Employee, Department, Position

    # Vérifier que l'email n'existe pas déjà
    if Employee.objects.filter(email=email, organization=organization).exists():
        return {
            "success": False,
            "error": f"Un employé avec l'email '{email}' existe déjà dans cette organisation.",
        }

    # Résoudre le département
    department = None
    if department_name:
        department = Department.objects.filter(
            organization=organization,
            name__icontains=department_name,
            is_active=True,
        ).first()
        if not department:
            return {
                "success": False,
                "error": f"Département '{department_name}' introuvable. "
                         f"Départements disponibles : {', '.join(Department.objects.filter(organization=organization, is_active=True).values_list('name', flat=True)[:10])}",
            }

    # Résoudre le poste
    position = None
    if position_title:
        position = Position.objects.filter(
            organization=organization,
            title__icontains=position_title,
            is_active=True,
        ).first()
        if not position:
            return {
                "success": False,
                "error": f"Poste '{position_title}' introuvable. "
                         f"Postes disponibles : {', '.join(Position.objects.filter(organization=organization, is_active=True).values_list('title', flat=True)[:10])}",
            }

    # Créer l'employé
    employee = Employee.objects.create_user(
        email=email,
        organization=organization,
        first_name=first_name,
        last_name=last_name,
        phone=phone or "",
        department=department,
        position=position,
        employment_status='active',
        password=None,  # Pas de mot de passe par défaut
    )

    return {
        "success": True,
        "message": f"✅ Employé '{first_name} {last_name}' créé avec succès !",
        "employe": {
            "id": str(employee.id),
            "nom_complet": f"{first_name} {last_name}",
            "email": email,
            "departement": department.name if department else "Non assigné",
            "poste": position.title if position else "Non défini",
        }
    }


@register_tool(
    name="creer_demande_conge",
    description=(
        "Crée une demande de congé pour un employé. "
        "Nécessite: email de l'employé, date de début, date de fin. "
        "Optionnel: type de congé, raison. "
        "Utilise cet outil quand l'utilisateur demande de poser un congé ou faire une demande de congé."
    ),
    category="hr",
    parameters={
        "type": "object",
        "properties": {
            "employee_email": {
                "type": "string",
                "description": "Email de l'employé qui demande le congé"
            },
            "start_date": {
                "type": "string",
                "description": "Date de début du congé (format YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "description": "Date de fin du congé (format YYYY-MM-DD)"
            },
            "leave_type_name": {
                "type": "string",
                "description": "Type de congé (ex: 'Congé annuel', 'Maladie'). Optionnel."
            },
            "reason": {
                "type": "string",
                "description": "Raison de la demande de congé"
            },
        },
        "required": ["employee_email", "start_date", "end_date"],
    },
    requires_confirmation=False,
    is_read_only=False,
)
def create_leave_request(organization, employee_email: str, start_date: str,
                         end_date: str, leave_type_name: str = None,
                         reason: str = None) -> dict:
    """Crée une demande de congé."""
    from hr.models import Employee, LeaveRequest, LeaveType
    from datetime import datetime

    # Trouver l'employé
    employee = Employee.objects.filter(
        organization=organization,
        email__icontains=employee_email,
    ).first()

    if not employee:
        return {
            "success": False,
            "error": f"Employé avec l'email '{employee_email}' introuvable.",
        }

    # Parser les dates
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return {
            "success": False,
            "error": "Format de date invalide. Utilisez YYYY-MM-DD.",
        }

    if end < start:
        return {
            "success": False,
            "error": "La date de fin doit être après la date de début.",
        }

    # Résoudre le type de congé
    leave_type = None
    if leave_type_name:
        leave_type = LeaveType.objects.filter(
            organization=organization,
            name__icontains=leave_type_name,
        ).first()

    # Créer la demande
    leave_data = {
        "employee": employee,
        "start_date": start,
        "end_date": end,
        "reason": reason or "",
        "status": "pending",
    }
    if leave_type:
        leave_data["leave_type"] = leave_type

    leave_request = LeaveRequest.objects.create(**leave_data)

    total_days = (end - start).days + 1

    return {
        "success": True,
        "message": f"✅ Demande de congé créée pour {employee.first_name} {employee.last_name}",
        "demande": {
            "id": str(leave_request.id),
            "employe": f"{employee.first_name} {employee.last_name}",
            "type": leave_type.name if leave_type else "Non spécifié",
            "date_debut": str(start),
            "date_fin": str(end),
            "jours": total_days,
            "statut": "En attente d'approbation",
        }
    }
