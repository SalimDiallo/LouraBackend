"""
Permission Dependencies - Définition des dépendances entre permissions
=======================================================================

Ce module définit quelles permissions dépendent d'autres permissions.
Utilisé pour valider la cohérence lors de la création/modification de rôles.

Architecture:
    - PERMISSION_DEPENDENCIES: Dict mapping permission code -> list of required permissions
    - validate_permission_dependencies(): Fonction de validation
    - get_all_required_permissions(): Fonction pour collecter toutes les dépendances

Exemple:
    'inventory.manage_stock' dépend de:
        - 'inventory.view_products'
        - 'inventory.view_warehouses'
        - 'inventory.view_suppliers'
"""


# ===============================
# DÉFINITION DES DÉPENDANCES
# ===============================

PERMISSION_DEPENDENCIES = {
    # Inventory: manage_stock requires view access to related entities
    'inventory.manage_stock': [
        'inventory.view_products',
        'inventory.view_warehouses',
        'inventory.view_suppliers',
    ],
    
    # Futures dépendances peuvent être ajoutées ici
    # 'hr.approve_payroll': ['hr.view_payroll'],
    # 'inventory.validate_stock_counts': ['inventory.view_stock_counts', 'inventory.view_stock'],
}


# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def get_missing_dependencies(permission_codes: list) -> dict:
    """
    Vérifie quelles permissions ont des dépendances manquantes.
    
    Args:
        permission_codes: Liste des codes de permission à vérifier
        
    Returns:
        Dict mapping permission code -> list of missing dependencies
    """
    permission_set = set(permission_codes)
    missing = {}
    
    for code in permission_codes:
        if code in PERMISSION_DEPENDENCIES:
            deps = PERMISSION_DEPENDENCIES[code]
            missing_deps = [dep for dep in deps if dep not in permission_set]
            if missing_deps:
                missing[code] = missing_deps
    
    return missing


def get_all_required_permissions(permission_codes: list) -> list:
    """
    Retourne la liste complète des permissions incluant toutes les dépendances.
    
    Args:
        permission_codes: Liste des codes de permission initiale
        
    Returns:
        Liste complète incluant les dépendances
    """
    all_codes = set(permission_codes)
    
    def collect_deps(code, collected):
        if code in PERMISSION_DEPENDENCIES:
            for dep in PERMISSION_DEPENDENCIES[code]:
                if dep not in collected:
                    collected.add(dep)
                    collect_deps(dep, collected)
    
    for code in permission_codes:
        collect_deps(code, all_codes)
    
    return list(all_codes)


def validate_permission_dependencies(permission_codes: list, auto_add: bool = False) -> tuple:
    """
    Valide les dépendances de permissions.
    
    Args:
        permission_codes: Liste des codes de permission à valider
        auto_add: Si True, retourne la liste complète avec dépendances ajoutées
        
    Returns:
        Tuple (is_valid: bool, result: dict/list)
        - Si is_valid=False: result contient les erreurs
        - Si is_valid=True et auto_add=True: result contient la liste complète
        - Si is_valid=True et auto_add=False: result est None
    """
    missing = get_missing_dependencies(permission_codes)
    
    if missing:
        if auto_add:
            # Ajouter automatiquement les dépendances manquantes
            complete_list = get_all_required_permissions(permission_codes)
            return (True, complete_list)
        else:
            return (False, {
                'missing_dependencies': missing,
                'message': 'Certaines permissions ont des dépendances non satisfaites',
            })
    
    return (True, permission_codes if auto_add else None)


# ===============================
# EXPORTS
# ===============================

__all__ = [
    'PERMISSION_DEPENDENCIES',
    'get_missing_dependencies',
    'get_all_required_permissions',
    'validate_permission_dependencies',
]
