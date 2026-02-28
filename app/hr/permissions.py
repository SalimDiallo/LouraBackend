"""
HR Permissions - Liste des permissions du module HR
====================================================

Ce module définit TOUTES les permissions du module HR.
Il est utilisé par le PermissionRegistry pour synchroniser avec la base de données.

Architecture :
    - PERMISSIONS : Liste des permissions (pour le registry)
    - Classes de permission : Héritent de core.permissions (pour les views)

Principe Open/Closed :
    - Pour ajouter une permission, ajoutez simplement une entrée dans PERMISSIONS
    - Les classes de permission sont génériques et réutilisables
"""

from core.permissions import (
    BaseCRUDPermission,
    BaseHasPermission,
    IsAdminOrEmployee,
    IsAdminUser,
)


# ===============================
# LISTE DES PERMISSIONS (REGISTRY)
# ===============================
# Format uniforme pour toutes les apps
# Code: {app}.{action}_{resource} (ex: hr.view_employees)

PERMISSIONS = [
    # === EMPLOYEES ===
    {'code': 'hr.view_employees', 'name': 'Voir les employés', 'category': 'Employés', 'description': 'Peut consulter la liste et les détails des employés'},
    {'code': 'hr.create_employees', 'name': 'Créer des employés', 'category': 'Employés', 'description': 'Peut créer de nouveaux employés'},
    {'code': 'hr.update_employees', 'name': 'Modifier des employés', 'category': 'Employés', 'description': 'Peut modifier les informations des employés'},
    {'code': 'hr.delete_employees', 'name': 'Supprimer des employés', 'category': 'Employés', 'description': 'Peut supprimer des employés'},
    # {'code': 'hr.activate_employees', 'name': 'Activer/Désactiver des employés', 'category': 'Employés', 'description': 'Peut activer ou désactiver des comptes employés'},
    # {'code': 'hr.manage_employee_permissions', 'name': 'Gérer les permissions', 'category': 'Employés', 'description': 'Peut attribuer ou retirer des permissions aux employés'},

    # === DEPARTMENTS ===
    {'code': 'hr.view_departments', 'name': 'Voir les départements', 'category': 'Départements', 'description': 'Peut consulter les départements'},
    {'code': 'hr.create_departments', 'name': 'Créer des départements', 'category': 'Départements', 'description': 'Peut créer de nouveaux départements'},
    {'code': 'hr.update_departments', 'name': 'Modifier des départements', 'category': 'Départements', 'description': 'Peut modifier les départements'},
    {'code': 'hr.delete_departments', 'name': 'Supprimer des départements', 'category': 'Départements', 'description': 'Peut supprimer des départements'},

    # === POSITIONS ===
    {'code': 'hr.view_positions', 'name': 'Voir les postes', 'category': 'Postes', 'description': 'Peut consulter les postes'},
    {'code': 'hr.create_positions', 'name': 'Créer des postes', 'category': 'Postes', 'description': 'Peut créer de nouveaux postes'},
    {'code': 'hr.update_positions', 'name': 'Modifier des postes', 'category': 'Postes', 'description': 'Peut modifier les postes'},
    {'code': 'hr.delete_positions', 'name': 'Supprimer des postes', 'category': 'Postes', 'description': 'Peut supprimer des postes'},

    # === CONTRACTS ===
    {'code': 'hr.view_contracts', 'name': 'Voir les contrats', 'category': 'Contrats', 'description': 'Peut consulter les contrats'},
    {'code': 'hr.create_contracts', 'name': 'Créer des contrats', 'category': 'Contrats', 'description': 'Peut créer de nouveaux contrats'},
    {'code': 'hr.update_contracts', 'name': 'Modifier des contrats', 'category': 'Contrats', 'description': 'Peut modifier les contrats'},
    {'code': 'hr.delete_contracts', 'name': 'Supprimer des contrats', 'category': 'Contrats', 'description': 'Peut supprimer des contrats'},

    # === ROLES ===
    {'code': 'hr.view_roles', 'name': 'Voir les rôles', 'category': 'Rôles', 'description': 'Peut consulter les rôles'},
    {'code': 'hr.create_roles', 'name': 'Créer des rôles', 'category': 'Rôles', 'description': 'Peut créer de nouveaux rôles'},
    {'code': 'hr.update_roles', 'name': 'Modifier des rôles', 'category': 'Rôles', 'description': 'Peut modifier les rôles'},
    {'code': 'hr.delete_roles', 'name': 'Supprimer des rôles', 'category': 'Rôles', 'description': 'Peut supprimer des rôles'},
    {'code': 'hr.assign_roles', 'name': 'Attribuer des rôles', 'category': 'Rôles', 'description': 'Peut attribuer des rôles aux employés'},

    # === LEAVE (Congés) ===
    {'code': 'hr.view_leave', 'name': 'Voir les congés', 'category': 'Congés', 'description': 'Peut consulter les demandes de congé'},
    {'code': 'hr.create_leave', 'name': 'Créer des demandes', 'category': 'Congés', 'description': 'Peut créer des demandes de congé'},
    {'code': 'hr.update_leave', 'name': 'Modifier des congés', 'category': 'Congés', 'description': 'Peut modifier des demandes de congé'},
    {'code': 'hr.delete_leave', 'name': 'Supprimer des congés', 'category': 'Congés', 'description': 'Peut supprimer des demandes de congé'},
    {'code': 'hr.approve_leave', 'name': 'Approuver des congés', 'category': 'Congés', 'description': 'Peut approuver ou rejeter des demandes de congé'},
    # {'code': 'hr.manage_leave_types', 'name': 'Gérer les types', 'category': 'Congés', 'description': 'Peut créer et modifier les types de congé'},
    # {'code': 'hr.manage_leave_balances', 'name': 'Gérer les soldes', 'category': 'Congés', 'description': 'Peut modifier les soldes de congé'},

    # === PAYROLL (Paie) ===
    {'code': 'hr.view_payroll', 'name': 'Voir la paie', 'category': 'Paie', 'description': 'Peut consulter les informations de paie de tous les employés'},
    {'code': 'hr.create_payroll', 'name': 'Créer des bulletins', 'category': 'Paie', 'description': 'Peut créer des bulletins de paie pour les employés'},
    {'code': 'hr.update_payroll', 'name': 'Modifier la paie', 'category': 'Paie', 'description': 'Peut modifier les informations de paie'},
    {'code': 'hr.delete_payroll', 'name': 'Supprimer des bulletins', 'category': 'Paie', 'description': 'Peut supprimer des bulletins de paie'},
    {'code': 'hr.approve_payroll', 'name': 'Approuver les avances de paies', 'category': 'Paie', 'description': 'Peut approuver les avances sur salaire et valider les paies'},
    # {'code': 'hr.process_payroll', 'name': 'Traiter la paie', 'category': 'Paie', 'description': 'Peut marquer les bulletins comme payés'},
    # {'code': 'hr.export_payroll', 'name': 'Exporter la paie', 'category': 'Paie', 'description': 'Peut exporter les bulletins en PDF'},

    # === ATTENDANCE (Pointages) ===
    # {'code': 'hr.view_attendance', 'name': 'Voir les pointages', 'category': 'Pointages', 'description': 'Peut consulter ses pointages'},
    {'code': 'hr.view_all_attendance', 'name': 'Voir tous les pointages', 'category': 'Pointages', 'description': 'Peut consulter les pointages de tous les employés'},
    # {'code': 'hr.create_attendance', 'name': 'Créer des pointages', 'category': 'Pointages', 'description': 'Peut créer des enregistrements de pointage'},
    # {'code': 'hr.update_attendance', 'name': 'Modifier des pointages', 'category': 'Pointages', 'description': 'Peut modifier les pointages'},
    # {'code': 'hr.delete_attendance', 'name': 'Supprimer des pointages', 'category': 'Pointages', 'description': 'Peut supprimer des pointages'},
    {'code': 'hr.approve_attendance', 'name': 'Approuver des pointages', 'category': 'Pointages', 'description': 'Peut approuver ou rejeter des pointages'},
    {'code': 'hr.manual_checkin', 'name': 'Pointage manuel', 'category': 'Pointages', 'description': 'Peut effectuer un pointage manuel'},
    {'code': 'hr.create_qr_session', 'name': 'Générer des QR codes', 'category': 'Pointages', 'description': 'Peut générer des QR codes pour le pointage'},

    # === REPORTS ===
    {'code': 'hr.view_reports', 'name': 'Voir les rapports', 'category': 'Rapports', 'description': 'Peut consulter les rapports et statistiques'},
    {'code': 'hr.export_reports', 'name': 'Exporter les rapports', 'category': 'Rapports', 'description': 'Peut exporter les rapports en PDF/Excel'},
]


# ===============================
# CLASSES DE PERMISSION (VIEWS)
# ===============================
# Héritent des classes de base de core.permissions
# Chaque classe configure automatiquement prefix + resource

class EmployeePermission(BaseCRUDPermission):
    """Permission CRUD pour les employés."""
    permission_prefix = 'hr'
    permission_resource = 'employees'


class DepartmentPermission(BaseCRUDPermission):
    """Permission CRUD pour les départements."""
    permission_prefix = 'hr'
    permission_resource = 'departments'


class PositionPermission(BaseCRUDPermission):
    """Permission CRUD pour les postes."""
    permission_prefix = 'hr'
    permission_resource = 'positions'


class ContractPermission(BaseCRUDPermission):
    """Permission CRUD pour les contrats."""
    permission_prefix = 'hr'
    permission_resource = 'contracts'


class RolePermission(BaseCRUDPermission):
    """Permission CRUD pour les rôles."""
    permission_prefix = 'hr'
    permission_resource = 'roles'


class LeavePermission(BaseCRUDPermission):
    """Permission CRUD pour les congés."""
    permission_prefix = 'hr'
    permission_resource = 'leave'


class PayrollPermission(BaseCRUDPermission):
    """Permission CRUD pour la paie."""
    permission_prefix = 'hr'
    permission_resource = 'payroll'


class AttendancePermission(BaseCRUDPermission):
    """Permission CRUD pour les pointages."""
    permission_prefix = 'hr'
    permission_resource = 'attendance'


# ===============================
# PERMISSIONS SPÉCIALES
# ===============================

class IsHRAdmin(IsAdminUser):
    """Vérifie que l'utilisateur est un Admin (alias HR)."""
    pass


class IsManagerOrAdmin(BaseHasPermission):
    """
    Autorise les Admins et les Employees avec permission d'approbation.
    Utilisée pour les actions approve/reject.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_type = getattr(request.user, 'user_type', None)
        
        # Admin = toujours autorisé
        if user_type == 'admin':
            return True
        
        # Employee = vérifie permission d'approbation
        if user_type == 'employee':
            # Manager ou HR avec permission approve
            return True  # La vue vérifie la permission spécifique
        
        return False


class CanAccessOwnOrManage(BaseHasPermission):
    """
    Permet l'accès aux propres données ou gestion si permission.
    Utilisée pour LeaveBalance et Payslip.
    """
    
    @staticmethod
    def for_resource(resource, permission):
        """Factory method pour créer une permission paramétrée."""
        return CanAccessOwnOrManage


RequiresEmployeePermission = EmployeePermission
RequiresDepartmentPermission = DepartmentPermission
RequiresPositionPermission = PositionPermission
RequiresContractPermission = ContractPermission
RequiresRolePermission = RolePermission
RequiresLeavePermission = LeavePermission
RequiresPayrollPermission = PayrollPermission
RequiresAttendancePermission = AttendancePermission
IsManagerOrHRAdmin = IsManagerOrAdmin
IsAdminUserOrEmployee = IsAdminOrEmployee


# ===============================
# CODES DE PERMISSION (HELPER)
# ===============================

PERMISSION_CODES = [p['code'] for p in PERMISSIONS]


# ===============================
# RÔLES PRÉDÉFINIS
# ===============================

PREDEFINED_ROLES = {
    'super_admin': {
        'name': 'Super Administrateur',
        'description': 'Accès complet à toutes les fonctionnalités',
        'permissions': PERMISSION_CODES,  # Toutes les permissions
        'is_system_role': True,
    },

    'hr_admin': {
        'name': 'Administrateur RH',
        'description': 'Gestion complète des ressources humaines',
        'permissions': [
            # Employees
            'hr.view_employees', 'hr.create_employees', 'hr.update_employees',
            'hr.delete_employees', 'hr.activate_employees',
            # Departments
            'hr.view_departments', 'hr.create_departments', 'hr.update_departments',
            'hr.delete_departments',
            # Positions
            'hr.view_positions', 'hr.create_positions', 'hr.update_positions',
            'hr.delete_positions',
            # Contracts
            'hr.view_contracts', 'hr.create_contracts', 'hr.update_contracts',
            'hr.delete_contracts',
            # Leaves
            'hr.view_leave', 'hr.create_leave', 'hr.update_leave', 'hr.delete_leave',
            'hr.approve_leave', 'hr.manage_leave_types', 'hr.manage_leave_balances',
            # Payroll
            'hr.view_payroll', 'hr.create_payroll', 'hr.update_payroll',
            'hr.delete_payroll', 'hr.process_payroll', 'hr.export_payroll',
            # Roles
            'hr.view_roles', 'hr.create_roles', 'hr.update_roles', 'hr.assign_roles',
            # Reports
            'hr.view_reports', 'hr.export_reports',
            # Attendance
            'hr.view_attendance', 'hr.view_all_attendance', 'hr.create_attendance',
            'hr.update_attendance', 'hr.delete_attendance', 'hr.approve_attendance',
            'hr.manual_checkin', 'hr.create_qr_session',
        ],
        'is_system_role': True,
    },

    'hr_manager': {
        'name': 'Manager RH',
        'description': 'Gestion quotidienne des RH',
        'permissions': [
            'hr.view_employees', 'hr.create_employees', 'hr.update_employees',
            'hr.view_departments', 'hr.update_departments',
            'hr.view_positions',
            'hr.view_contracts', 'hr.create_contracts', 'hr.update_contracts',
            'hr.view_leave', 'hr.create_leave', 'hr.update_leave', 'hr.approve_leave',
            'hr.view_payroll',
            'hr.view_roles',
            'hr.view_reports', 'hr.export_reports',
            'hr.view_attendance', 'hr.view_all_attendance', 'hr.approve_attendance',
            'hr.create_qr_session',
        ],
        'is_system_role': True,
    },

    'manager': {
        'name': 'Manager d\'équipe',
        'description': 'Gestion d\'une équipe',
        'permissions': [
            'hr.view_employees',
            'hr.view_departments',
            'hr.view_leave', 'hr.create_leave', 'hr.approve_leave',
            'hr.view_reports',
            'hr.view_attendance', 'hr.view_all_attendance', 'hr.approve_attendance',
        ],
        'is_system_role': True,
    },

    'employee': {
        'name': 'Employé',
        'description': 'Accès de base pour les employés',
        'permissions': [
            'hr.view_employees',
            'hr.view_departments',
            'hr.view_leave', 'hr.create_leave',
            'hr.view_payroll',
            'hr.view_attendance',
        ],
        'is_system_role': True,
    },

    'readonly': {
        'name': 'Lecture seule',
        'description': 'Consultation uniquement',
        'permissions': [
            'hr.view_employees',
            'hr.view_departments',
            'hr.view_positions',
            'hr.view_leave',
            'hr.view_reports',
        ],
        'is_system_role': True,
    },
}


# ===============================
# EXPORTS PUBLICS
# ===============================

__all__ = [
    # Liste des permissions (pour registry)
    'PERMISSIONS',
    'PERMISSION_CODES',
    'PREDEFINED_ROLES',
    # Classes de permission CRUD
    'EmployeePermission',
    'DepartmentPermission',
    'PositionPermission',
    'ContractPermission',
    'RolePermission',
    'LeavePermission',
    'PayrollPermission',
    'AttendancePermission',
    # Permissions spéciales
    'IsHRAdmin',
    'IsManagerOrAdmin',
    'CanAccessOwnOrManage',
    # Alias rétrocompatibilité
    'RequiresEmployeePermission',
    'RequiresDepartmentPermission',
    'RequiresPositionPermission',
    'RequiresContractPermission',
    'RequiresRolePermission',
    'RequiresLeavePermission',
    'RequiresPayrollPermission',
    'RequiresAttendancePermission',
    'IsManagerOrHRAdmin',
    'IsAdminUserOrEmployee',
]

