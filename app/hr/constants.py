"""
Constants for HR app - Permissions and Roles
"""

# ====================================
# PERMISSIONS DEFINITIONS
# ====================================

PERMISSIONS = {
    # Employee Permissions
    'can_view_employee': {
        'name': 'Voir les employés',
        'category': 'Employés',
        'description': 'Peut consulter la liste et les détails des employés'
    },
    'can_create_employee': {
        'name': 'Créer des employés',
        'category': 'Employés',
        'description': 'Peut créer de nouveaux employés'
    },
    'can_update_employee': {
        'name': 'Modifier des employés',
        'category': 'Employés',
        'description': 'Peut modifier les informations des employés'
    },
    'can_delete_employee': {
        'name': 'Supprimer des employés',
        'category': 'Employés',
        'description': 'Peut supprimer des employés'
    },
    'can_activate_employee': {
        'name': 'Activer/Désactiver des employés',
        'category': 'Employés',
        'description': 'Peut activer ou désactiver des comptes employés'
    },
    'can_manage_employee_permissions': {
        'name': 'Gérer les permissions des employés',
        'category': 'Employés',
        'description': 'Peut attribuer ou retirer des permissions aux employés'
    },

    # Department Permissions
    'can_view_department': {
        'name': 'Voir les départements',
        'category': 'Départements',
        'description': 'Peut consulter la liste et les détails des départements'
    },
    'can_create_department': {
        'name': 'Créer des départements',
        'category': 'Départements',
        'description': 'Peut créer de nouveaux départements'
    },
    'can_update_department': {
        'name': 'Modifier des départements',
        'category': 'Départements',
        'description': 'Peut modifier les informations des départements'
    },
    'can_delete_department': {
        'name': 'Supprimer des départements',
        'category': 'Départements',
        'description': 'Peut supprimer des départements'
    },

    # Position Permissions
    'can_view_position': {
        'name': 'Voir les postes',
        'category': 'Postes',
        'description': 'Peut consulter la liste et les détails des postes'
    },
    'can_create_position': {
        'name': 'Créer des postes',
        'category': 'Postes',
        'description': 'Peut créer de nouveaux postes'
    },
    'can_update_position': {
        'name': 'Modifier des postes',
        'category': 'Postes',
        'description': 'Peut modifier les informations des postes'
    },
    'can_delete_position': {
        'name': 'Supprimer des postes',
        'category': 'Postes',
        'description': 'Peut supprimer des postes'
    },

    # Contract Permissions
    'can_view_contract': {
        'name': 'Voir les contrats',
        'category': 'Contrats',
        'description': 'Peut consulter la liste et les détails des contrats'
    },
    'can_create_contract': {
        'name': 'Créer des contrats',
        'category': 'Contrats',
        'description': 'Peut créer de nouveaux contrats'
    },
    'can_update_contract': {
        'name': 'Modifier des contrats',
        'category': 'Contrats',
        'description': 'Peut modifier les informations des contrats'
    },
    'can_delete_contract': {
        'name': 'Supprimer des contrats',
        'category': 'Contrats',
        'description': 'Peut supprimer des contrats'
    },

    # Leave Permissions
    'can_view_leave': {
        'name': 'Voir les congés',
        'category': 'Congés',
        'description': 'Peut consulter la liste et les détails des congés'
    },
    'can_create_leave': {
        'name': 'Créer des demandes de congé',
        'category': 'Congés',
        'description': 'Peut créer des demandes de congé'
    },
    'can_update_leave': {
        'name': 'Modifier des congés',
        'category': 'Congés',
        'description': 'Peut modifier des demandes de congé'
    },
    'can_delete_leave': {
        'name': 'Supprimer des congés',
        'category': 'Congés',
        'description': 'Peut supprimer des demandes de congé'
    },
    'can_approve_leave': {
        'name': 'Approuver des congés',
        'category': 'Congés',
        'description': 'Peut approuver ou rejeter des demandes de congé'
    },
    'can_manage_leave_types': {
        'name': 'Gérer les types de congé',
        'category': 'Congés',
        'description': 'Peut créer et modifier les types de congé'
    },
    'can_manage_leave_balances': {
        'name': 'Gérer les soldes de congé',
        'category': 'Congés',
        'description': 'Peut modifier les soldes de congé des employés'
    },

    # Payroll Permissions
    'can_view_payroll': {
        'name': 'Voir la paie',
        'category': 'Paie',
        'description': 'Peut consulter les informations de paie'
    },
    'can_create_payroll': {
        'name': 'Créer des bulletins de paie',
        'category': 'Paie',
        'description': 'Peut créer des bulletins de paie'
    },
    'can_update_payroll': {
        'name': 'Modifier la paie',
        'category': 'Paie',
        'description': 'Peut modifier les informations de paie'
    },
    'can_delete_payroll': {
        'name': 'Supprimer des bulletins de paie',
        'category': 'Paie',
        'description': 'Peut supprimer des bulletins de paie'
    },
    'can_process_payroll': {
        'name': 'Traiter la paie',
        'category': 'Paie',
        'description': 'Peut marquer les bulletins comme payés'
    },

    # Role Permissions
    'can_view_role': {
        'name': 'Voir les rôles',
        'category': 'Rôles',
        'description': 'Peut consulter la liste et les détails des rôles'
    },
    'can_create_role': {
        'name': 'Créer des rôles',
        'category': 'Rôles',
        'description': 'Peut créer de nouveaux rôles'
    },
    'can_update_role': {
        'name': 'Modifier des rôles',
        'category': 'Rôles',
        'description': 'Peut modifier les rôles existants'
    },
    'can_delete_role': {
        'name': 'Supprimer des rôles',
        'category': 'Rôles',
        'description': 'Peut supprimer des rôles'
    },
    'can_assign_role': {
        'name': 'Attribuer des rôles',
        'category': 'Rôles',
        'description': 'Peut attribuer des rôles aux employés'
    },

    # Reports Permissions
    'can_view_reports': {
        'name': 'Voir les rapports',
        'category': 'Rapports',
        'description': 'Peut consulter les rapports et statistiques'
    },
    'can_export_reports': {
        'name': 'Exporter les rapports',
        'category': 'Rapports',
        'description': 'Peut exporter les rapports en PDF/Excel'
    },
}


# ====================================
# PREDEFINED ROLES
# ====================================

PREDEFINED_ROLES = {
    'super_admin': {
        'name': 'Super Administrateur',
        'description': 'Accès complet à toutes les fonctionnalités',
        'permissions': list(PERMISSIONS.keys()),  # Toutes les permissions
        'is_system_role': True,
    },

    'hr_admin': {
        'name': 'Administrateur RH',
        'description': 'Gestion complète des ressources humaines',
        'permissions': [
            # Employees
            'can_view_employee', 'can_create_employee', 'can_update_employee',
            'can_delete_employee', 'can_activate_employee',
            # Departments
            'can_view_department', 'can_create_department', 'can_update_department',
            'can_delete_department',
            # Positions
            'can_view_position', 'can_create_position', 'can_update_position',
            'can_delete_position',
            # Contracts
            'can_view_contract', 'can_create_contract', 'can_update_contract',
            'can_delete_contract',
            # Leaves
            'can_view_leave', 'can_create_leave', 'can_update_leave',
            'can_delete_leave', 'can_approve_leave', 'can_manage_leave_types',
            'can_manage_leave_balances',
            # Payroll
            'can_view_payroll', 'can_create_payroll', 'can_update_payroll',
            'can_delete_payroll', 'can_process_payroll',
            # Roles
            'can_view_role', 'can_create_role', 'can_update_role',
            'can_assign_role',
            # Reports
            'can_view_reports', 'can_export_reports',
        ],
        'is_system_role': True,
    },

    'hr_manager': {
        'name': 'Manager RH',
        'description': 'Gestion quotidienne des RH',
        'permissions': [
            # Employees
            'can_view_employee', 'can_create_employee', 'can_update_employee',
            # Departments
            'can_view_department', 'can_update_department',
            # Positions
            'can_view_position',
            # Contracts
            'can_view_contract', 'can_create_contract', 'can_update_contract',
            # Leaves
            'can_view_leave', 'can_create_leave', 'can_update_leave',
            'can_approve_leave',
            # Payroll
            'can_view_payroll',
            # Roles
            'can_view_role',
            # Reports
            'can_view_reports', 'can_export_reports',
        ],
        'is_system_role': True,
    },

    'manager': {
        'name': 'Manager d\'équipe',
        'description': 'Gestion d\'une équipe',
        'permissions': [
            # Employees (own team only)
            'can_view_employee',
            # Departments
            'can_view_department',
            # Leaves (team)
            'can_view_leave', 'can_create_leave', 'can_approve_leave',
            # Reports
            'can_view_reports',
        ],
        'is_system_role': True,
    },

    'employee': {
        'name': 'Employé',
        'description': 'Accès de base pour les employés',
        'permissions': [
            # Own data only
            'can_view_employee',  # Own profile
            'can_view_department',
            # Leaves (own)
            'can_view_leave', 'can_create_leave',
            # Payroll (own)
            'can_view_payroll',
        ],
        'is_system_role': True,
    },

    'readonly': {
        'name': 'Lecture seule',
        'description': 'Consultation uniquement',
        'permissions': [
            'can_view_employee',
            'can_view_department',
            'can_view_position',
            'can_view_leave',
            'can_view_reports',
        ],
        'is_system_role': True,
    },
}
