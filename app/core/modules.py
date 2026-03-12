"""
Module Registry System
======================
Ce fichier centralise la définition de tous les modules disponibles dans l'application.
Les modules sont automatiquement enregistrés dans la base de données via le management command.
"""

from typing import List, Dict, Any


class ModuleDefinition:
    """Classe représentant la définition d'un module"""

    def __init__(
        self,
        code: str,
        name: str,
        description: str,
        app_name: str,
        icon: str = "",
        category: str = "general",
        default_for_all: bool = False,
        default_categories: List[str] = None,
        requires_subscription_tier: str = "",
        depends_on: List[str] = None,
        is_core: bool = False,
        order: int = 0
    ):
        self.code = code
        self.name = name
        self.description = description
        self.app_name = app_name
        self.icon = icon
        self.category = category
        self.default_for_all = default_for_all
        self.default_categories = default_categories or []
        self.requires_subscription_tier = requires_subscription_tier
        self.depends_on = depends_on or []
        self.is_core = is_core
        self.order = order

    def to_dict(self) -> Dict[str, Any]:
        """Convertit la définition en dictionnaire pour la base de données"""
        return {
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'app_name': self.app_name,
            'icon': self.icon,
            'category': self.category,
            'default_for_all': self.default_for_all,
            'default_categories': self.default_categories,
            'requires_subscription_tier': self.requires_subscription_tier,
            'depends_on': self.depends_on,
            'is_core': self.is_core,
            'order': self.order,
            'is_active': True,
        }


class ModuleRegistry:
    """Registry centralisé de tous les modules de l'application"""

    _modules: List[ModuleDefinition] = []

    @classmethod
    def register(cls, module: ModuleDefinition):
        """Enregistre un nouveau module"""
        cls._modules.append(module)

    @classmethod
    def get_all_modules(cls) -> List[ModuleDefinition]:
        """Retourne tous les modules enregistrés"""
        return cls._modules

    @classmethod
    def get_module(cls, code: str) -> ModuleDefinition:
        """Récupère un module par son code"""
        for module in cls._modules:
            if module.code == code:
                return module
        return None

    @classmethod
    def get_modules_by_category(cls, category: str) -> List[ModuleDefinition]:
        """Récupère tous les modules d'une catégorie"""
        return [m for m in cls._modules if m.category == category]

    @classmethod
    def get_default_modules_for_category(cls, category_name: str) -> List[ModuleDefinition]:
        """Récupère les modules par défaut pour une catégorie d'organisation"""
        return [
            m for m in cls._modules
            if m.default_for_all or category_name in m.default_categories
        ]


# ===============================
# DÉFINITION DES MODULES RH
# ===============================

# Module de base : Gestion des employés (inclut départements et postes)
EMPLOYEES_MODULE = ModuleDefinition(
    code='hr.employees',
    name='Gestion des employés',
    description='Module complet pour gérer les employés, départements et postes de votre organisation',
    app_name='hr',
    icon='Users',
    category='hr',
    default_for_all=True,  # Activé pour toutes les catégories
    is_core=True,  # Module core qui ne peut pas être désactivé
    order=1
)

# Module de paie
PAYROLL_MODULE = ModuleDefinition(
    code='hr.payroll',
    name='Module de paie',
    description='Gestion complète de la paie : fiches de paie, périodes, avances sur salaire',
    app_name='hr',
    icon='DollarSign',
    category='hr',
    default_categories=[
        'Technologie',
        'Finance',
        'Services',
        'Commerce',
        'Industrie',
        'BTP',
        'Transports',
        'Santé',
        'Éducation'
    ],
    depends_on=['hr.employees'],
    order=2
)

# Module de congés
LEAVE_MODULE = ModuleDefinition(
    code='hr.leave',
    name='Module de congés',
    description='Gestion des demandes de congés, types de congés et soldes',
    app_name='hr',
    icon='Calendar',
    category='hr',
    default_categories=[
        'Technologie',
        'Finance',
        'Services',
        'Commerce',
        'Industrie',
        'BTP',
        'Transports',
        'Santé',
        'Éducation',
        'Restauration',
        'Média & Communication',
        'Immobilier',
        'Associatif'
    ],
    depends_on=['hr.employees'],
    order=3
)

# Module de pointage
ATTENDANCE_MODULE = ModuleDefinition(
    code='hr.attendance',
    name='Module de pointage',
    description='Suivi des présences, heures de travail, pointage QR Code',
    app_name='hr',
    icon='Clock',
    category='hr',
    default_categories=[
        'Commerce',
        'Industrie',
        'BTP',
        'Transports',
        'Restauration',
        'Santé',
        'Agriculture',
        'Energie'
    ],
    depends_on=['hr.employees'],
    order=4
)

# Module de contrats
CONTRACTS_MODULE = ModuleDefinition(
    code='hr.contracts',
    name='Gestion des contrats',
    description='Gestion des contrats de travail (CDI, CDD, Stage, etc.)',
    app_name='hr',
    icon='FileText',
    category='hr',
    default_categories=[
        'Technologie',
        'Finance',
        'Services',
        'Commerce',
        'Industrie',
        'BTP',
        'Santé',
        'Éducation'
    ],
    depends_on=['hr.employees'],
    order=5
)

# Module de permissions et rôles
PERMISSIONS_MODULE = ModuleDefinition(
    code='hr.permissions',
    name='Permissions et rôles',
    description='Gestion avancée des rôles et permissions personnalisées',
    app_name='hr',
    icon='Shield',
    category='hr',
    default_for_all=True,
    is_core=True,
    depends_on=['hr.employees'],
    order=6
)


# ===============================
# DÉFINITION DES MODULES INVENTORY
# ===============================

# Module 1 : Gestion du catalogue produits
PRODUCTS_MODULE = ModuleDefinition(
    code='inventory.products',
    name='Catalogue produits',
    description='Gestion complète du catalogue : produits, catégories, SKU, prix et descriptions',
    app_name='inventory',
    icon='Package',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Industrie',
        'BTP',
        'Agriculture',
        'Energie',
    ],
    is_core=False,
    order=10
)

# Module 2 : Gestion des entrepôts
WAREHOUSES_MODULE = ModuleDefinition(
    code='inventory.warehouses',
    name='Gestion des entrepôts',
    description='Gestion multi-entrepôts : emplacements, zones de stockage et organisation physique',
    app_name='inventory',
    icon='Warehouse',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Industrie',
        'BTP',
        'Agriculture',
    ],
    depends_on=['inventory.products'],
    order=11
)

# Module 3 : Mouvements de stock
MOVEMENTS_MODULE = ModuleDefinition(
    code='inventory.movements',
    name='Mouvements de stock',
    description='Suivi des mouvements : entrées, sorties, transferts entre entrepôts et inventaires',
    app_name='inventory',
    icon='ArrowLeftRight',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Industrie',
        'BTP',
        'Agriculture',
    ],
    depends_on=['inventory.products', 'inventory.warehouses'],
    order=12
)

# Module 4 : Gestion des achats
PURCHASES_MODULE = ModuleDefinition(
    code='inventory.purchases',
    name='Gestion des achats',
    description='Fournisseurs, bons de commande, réception de marchandises et suivi des achats',
    app_name='inventory',
    icon='ShoppingCart',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Industrie',
        'BTP',
    ],
    depends_on=['inventory.products', 'inventory.movements'],
    order=13
)

# Module 5 : Gestion des ventes
SALES_MODULE = ModuleDefinition(
    code='inventory.sales',
    name='Gestion des ventes',
    description='Clients, ventes, factures, paiements, devis et mouvements de sortie automatiques',
    app_name='inventory',
    icon='TrendingUp',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Agence de voyage',
    ],
    depends_on=['inventory.products', 'inventory.movements'],
    order=14
)

# Module 6 : Rapports et alertes
REPORTS_MODULE = ModuleDefinition(
    code='inventory.reports',
    name='Rapports et alertes',
    description='Rapports détaillés, tableaux de bord, alertes de stock bas et analyses avancées',
    app_name='inventory',
    icon='BarChart',
    category='inventory',
    default_categories=[
        'Commerce',
        'Restauration',
        'Industrie',
        'BTP',
    ],
    depends_on=['inventory.products'],
    order=15
)


# ===============================
# ENREGISTREMENT DES MODULES
# ===============================

def register_all_modules():
    """Enregistre tous les modules dans le registry"""
    modules = [
        # Modules RH
        EMPLOYEES_MODULE,
        PAYROLL_MODULE,
        LEAVE_MODULE,
        ATTENDANCE_MODULE,
        CONTRACTS_MODULE,
        PERMISSIONS_MODULE,
        # Modules Inventory
        PRODUCTS_MODULE,
        WAREHOUSES_MODULE,
        MOVEMENTS_MODULE,
        PURCHASES_MODULE,
        SALES_MODULE,
        REPORTS_MODULE,
    ]

    for module in modules:
        ModuleRegistry.register(module)


# Auto-enregistrement au chargement du module
register_all_modules()


# ===============================
# MAPPING CATÉGORIES -> MODULES
# ===============================

def get_category_module_mapping() -> Dict[str, List[str]]:
    """
    Retourne le mapping entre catégories d'organisations et modules recommandés.
    Utile pour la documentation et la visualisation.
    """
    return {
        'Technologie': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.contracts',
            'hr.permissions',
        ],
        'Finance': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.contracts',
            'hr.permissions'
        ],
        'Services': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.contracts',
            'hr.permissions'
        ],
        'Commerce': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.attendance',
            'hr.contracts',
            'hr.permissions',
            'inventory.products',
            'inventory.warehouses',
            'inventory.movements',
            'inventory.purchases',
            'inventory.sales',
            'inventory.reports',
        ],
        'Industrie': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.attendance',
            'hr.contracts',
            'hr.permissions',
            'inventory.products',
            'inventory.warehouses',
            'inventory.movements',
            'inventory.purchases',
            'inventory.reports',
        ],
        'BTP': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.attendance',
            'hr.contracts',
            'hr.permissions',
            'inventory.products',
            'inventory.warehouses',
            'inventory.movements',
            'inventory.purchases',
            'inventory.reports',
        ],
        'Transports': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.attendance',
            'hr.contracts',
            'hr.permissions'
        ],
        'Santé': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.attendance',
            'hr.contracts',
            'hr.permissions'
        ],
        'Éducation': [
            'hr.employees',
            'hr.payroll',
            'hr.leave',
            'hr.contracts',
            'hr.permissions'
        ],
        'Restauration': [
            'hr.employees',
            'hr.leave',
            'hr.attendance',
            'hr.permissions',
            'inventory.products',
            'inventory.warehouses',
            'inventory.movements',
            'inventory.purchases',
            'inventory.sales',
            'inventory.reports',
        ],
        'Agriculture': [
            'hr.employees',
            'hr.attendance',
            'hr.permissions',
            'inventory.products',
            'inventory.warehouses',
            'inventory.movements',
            'inventory.reports',
        ],
        'Energie': [
            'hr.employees',
            'hr.attendance',
            'hr.permissions',
            'inventory.products',
        ],
        'Média & Communication': [
            'hr.employees',
            'hr.leave',
            'hr.permissions'
        ],
        'Immobilier': [
            'hr.employees',
            'hr.leave',
            'hr.permissions'
        ],
        'Associatif': [
            'hr.employees',
            'hr.leave',
            'hr.permissions'
        ],
        'Agence de voyage': [
            'hr.employees',
            'hr.permissions',
            'inventory.sales',
        ],
        'Art & Culture': [
            'hr.employees',
            'hr.permissions'
        ],
    }
