"""
Inventory Permissions - Liste des permissions du module Inventory
=================================================================

Ce module définit TOUTES les permissions du module Inventory.
Il est utilisé par le PermissionRegistry pour synchroniser avec la base de données.

Architecture :
    - PERMISSIONS : Liste des permissions (pour le registry)
    - Classes de permission : Héritent de core.permissions (pour les views)
    - PREDEFINED_ROLES : Rôles prédéfinis pour Inventory

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

PERMISSIONS = [
    # === CATEGORIES ===
    {'code': 'inventory.view_categories', 'name': 'Voir les catégories', 'category': 'Catégories', 'description': 'Peut consulter les catégories de produits'},
    {'code': 'inventory.create_categories', 'name': 'Créer des catégories', 'category': 'Catégories', 'description': 'Peut créer des catégories'},
    {'code': 'inventory.update_categories', 'name': 'Modifier des catégories', 'category': 'Catégories', 'description': 'Peut modifier des catégories'},
    {'code': 'inventory.delete_categories', 'name': 'Supprimer des catégories', 'category': 'Catégories', 'description': 'Peut supprimer des catégories'},

    # === WAREHOUSES ===
    {'code': 'inventory.view_warehouses', 'name': 'Voir les entrepôts', 'category': 'Entrepôts', 'description': 'Peut consulter les entrepôts'},
    {'code': 'inventory.create_warehouses', 'name': 'Créer des entrepôts', 'category': 'Entrepôts', 'description': 'Peut créer des entrepôts'},
    {'code': 'inventory.update_warehouses', 'name': 'Modifier des entrepôts', 'category': 'Entrepôts', 'description': 'Peut modifier des entrepôts'},
    {'code': 'inventory.delete_warehouses', 'name': 'Supprimer des entrepôts', 'category': 'Entrepôts', 'description': 'Peut supprimer des entrepôts'},

    # === SUPPLIERS ===
    {'code': 'inventory.view_suppliers', 'name': 'Voir les fournisseurs', 'category': 'Fournisseurs', 'description': 'Peut consulter les fournisseurs'},
    {'code': 'inventory.create_suppliers', 'name': 'Créer des fournisseurs', 'category': 'Fournisseurs', 'description': 'Peut créer des fournisseurs'},
    {'code': 'inventory.update_suppliers', 'name': 'Modifier des fournisseurs', 'category': 'Fournisseurs', 'description': 'Peut modifier des fournisseurs'},
    {'code': 'inventory.delete_suppliers', 'name': 'Supprimer des fournisseurs', 'category': 'Fournisseurs', 'description': 'Peut supprimer des fournisseurs'},

    # === PRODUCTS ===
    {'code': 'inventory.view_products', 'name': 'Voir les produits', 'category': 'Produits', 'description': 'Peut consulter les produits'},
    {'code': 'inventory.create_products', 'name': 'Créer des produits', 'category': 'Produits', 'description': 'Peut créer des produits'},
    {'code': 'inventory.update_products', 'name': 'Modifier des produits', 'category': 'Produits', 'description': 'Peut modifier des produits'},
    {'code': 'inventory.delete_products', 'name': 'Supprimer des produits', 'category': 'Produits', 'description': 'Peut supprimer des produits'},

    # === STOCK ===
    {'code': 'inventory.view_stock', 'name': 'Voir les stocks', 'category': 'Stocks', 'description': 'Peut consulter les niveaux de stock'},
    {'code': 'inventory.manage_stock', 'name': 'Gérer les stocks', 'category': 'Stocks', 'description': 'Peut gérer les entrées/sorties de stock'},
    {'code': 'inventory.adjust_stock', 'name': 'Ajuster les stocks', 'category': 'Stocks', 'description': 'Peut ajuster les quantités de stock'},

    # === MOVEMENTS ===
    {'code': 'inventory.view_movements', 'name': 'Voir les mouvements', 'category': 'Mouvements', 'description': 'Peut consulter les mouvements de stock'},
    {'code': 'inventory.create_movements', 'name': 'Créer des mouvements', 'category': 'Mouvements', 'description': 'Peut créer des mouvements'},
    {'code': 'inventory.update_movements', 'name': 'Modifier des mouvements', 'category': 'Mouvements', 'description': 'Peut modifier des mouvements'},
    {'code': 'inventory.delete_movements', 'name': 'Annuler des mouvements', 'category': 'Mouvements', 'description': 'Peut annuler des mouvements'},

    # === ORDERS ===
    {'code': 'inventory.view_orders', 'name': 'Voir les commandes', 'category': 'Commandes', 'description': 'Peut consulter les commandes fournisseurs'},
    {'code': 'inventory.create_orders', 'name': 'Créer des commandes', 'category': 'Commandes', 'description': 'Peut créer des commandes'},
    {'code': 'inventory.update_orders', 'name': 'Modifier des commandes', 'category': 'Commandes', 'description': 'Peut modifier des commandes'},
    {'code': 'inventory.delete_orders', 'name': 'Annuler des commandes', 'category': 'Commandes', 'description': 'Peut annuler des commandes'},
    {'code': 'inventory.receive_orders', 'name': 'Réceptionner des commandes', 'category': 'Commandes', 'description': 'Peut réceptionner des commandes'},

    # === STOCK COUNTS ===
    {'code': 'inventory.view_stock_counts', 'name': 'Voir les inventaires', 'category': 'Inventaires', 'description': 'Peut consulter les inventaires physiques'},
    {'code': 'inventory.create_stock_counts', 'name': 'Créer des inventaires', 'category': 'Inventaires', 'description': 'Peut créer des sessions d\'inventaire'},
    {'code': 'inventory.validate_stock_counts', 'name': 'Valider des inventaires', 'category': 'Inventaires', 'description': 'Peut valider et appliquer les écarts d\'inventaire'},

    # === SALES ===
    {'code': 'inventory.view_sales', 'name': 'Voir les ventes', 'category': 'Ventes', 'description': 'Peut consulter les ventes'},
    {'code': 'inventory.create_sales', 'name': 'Créer des ventes', 'category': 'Ventes', 'description': 'Peut créer des ventes'},
    {'code': 'inventory.update_sales', 'name': 'Modifier des ventes', 'category': 'Ventes', 'description': 'Peut modifier des ventes'},
    {'code': 'inventory.delete_sales', 'name': 'Annuler des ventes', 'category': 'Ventes', 'description': 'Peut annuler des ventes'},

    # === CUSTOMERS ===
    {'code': 'inventory.view_customers', 'name': 'Voir les clients', 'category': 'Clients', 'description': 'Peut consulter les clients'},
    {'code': 'inventory.create_customers', 'name': 'Créer des clients', 'category': 'Clients', 'description': 'Peut créer des clients'},
    {'code': 'inventory.update_customers', 'name': 'Modifier des clients', 'category': 'Clients', 'description': 'Peut modifier des clients'},
    {'code': 'inventory.delete_customers', 'name': 'Supprimer des clients', 'category': 'Clients', 'description': 'Peut supprimer des clients'},

    # === PAYMENTS ===
    {'code': 'inventory.view_payments', 'name': 'Voir les paiements', 'category': 'Paiements', 'description': 'Peut consulter les paiements'},
    {'code': 'inventory.create_payments', 'name': 'Enregistrer des paiements', 'category': 'Paiements', 'description': 'Peut enregistrer des paiements'},

    # === REPORTS ===
    {'code': 'inventory.view_reports', 'name': 'Voir les rapports', 'category': 'Rapports', 'description': 'Peut consulter les rapports'},
    {'code': 'inventory.export_reports', 'name': 'Exporter les rapports', 'category': 'Rapports', 'description': 'Peut exporter les rapports'},
]


# ===============================
# CODES DE PERMISSION (HELPER)
# ===============================

PERMISSION_CODES = [p['code'] for p in PERMISSIONS]


# ===============================
# CLASSES DE PERMISSION (VIEWS)
# ===============================

class CategoryPermission(BaseCRUDPermission):
    """Permission CRUD pour les catégories."""
    permission_prefix = 'inventory'
    permission_resource = 'categories'


class WarehousePermission(BaseCRUDPermission):
    """Permission CRUD pour les entrepôts."""
    permission_prefix = 'inventory'
    permission_resource = 'warehouses'


class SupplierPermission(BaseCRUDPermission):
    """Permission CRUD pour les fournisseurs."""
    permission_prefix = 'inventory'
    permission_resource = 'suppliers'


class ProductPermission(BaseCRUDPermission):
    """Permission CRUD pour les produits."""
    permission_prefix = 'inventory'
    permission_resource = 'products'


class StockPermission(BaseCRUDPermission):
    """Permission CRUD pour les stocks."""
    permission_prefix = 'inventory'
    permission_resource = 'stock'


class MovementPermission(BaseCRUDPermission):
    """Permission CRUD pour les mouvements."""
    permission_prefix = 'inventory'
    permission_resource = 'movements'


class OrderPermission(BaseCRUDPermission):
    """Permission CRUD pour les commandes."""
    permission_prefix = 'inventory'
    permission_resource = 'orders'


class StockCountPermission(BaseCRUDPermission):
    """Permission CRUD pour les inventaires."""
    permission_prefix = 'inventory'
    permission_resource = 'stock_counts'


class SalePermission(BaseCRUDPermission):
    """Permission CRUD pour les ventes."""
    permission_prefix = 'inventory'
    permission_resource = 'sales'


class CustomerPermission(BaseCRUDPermission):
    """Permission CRUD pour les clients."""
    permission_prefix = 'inventory'
    permission_resource = 'customers'


class PaymentPermission(BaseCRUDPermission):
    """Permission CRUD pour les paiements."""
    permission_prefix = 'inventory'
    permission_resource = 'payments'


# ===============================
# PERMISSIONS SPÉCIALES
# ===============================

class IsInventoryAdmin(IsAdminUser):
    """Vérifie que l'utilisateur est un Admin."""
    pass


class IsAdminUserOrEmployee(IsAdminOrEmployee):
    """Alias pour compatibilité."""
    pass


# ===============================
# RÔLES PRÉDÉFINIS INVENTORY
# ===============================

PREDEFINED_ROLES = {
    'inventory_admin': {
        'name': 'Administrateur Inventaire',
        'description': 'Accès complet au module inventaire',
        'permissions': PERMISSION_CODES,
        'is_system_role': True,
    },

    'inventory_manager': {
        'name': 'Gestionnaire Inventaire',
        'description': 'Gestion quotidienne des stocks et ventes',
        'permissions': [
            # Catégories (lecture)
            'inventory.view_categories',
            # Entrepôts (lecture)
            'inventory.view_warehouses',
            # Fournisseurs
            'inventory.view_suppliers', 'inventory.create_suppliers', 'inventory.update_suppliers',
            # Produits
            'inventory.view_products', 'inventory.create_products', 'inventory.update_products',
            # Stock
            'inventory.view_stock', 'inventory.manage_stock', 'inventory.adjust_stock',
            # Mouvements
            'inventory.view_movements', 'inventory.create_movements', 'inventory.update_movements',
            # Commandes
            'inventory.view_orders', 'inventory.create_orders', 'inventory.update_orders', 'inventory.receive_orders',
            # Inventaires
            'inventory.view_stock_counts', 'inventory.create_stock_counts', 'inventory.validate_stock_counts',
            # Ventes
            'inventory.view_sales', 'inventory.create_sales', 'inventory.update_sales',
            # Clients
            'inventory.view_customers', 'inventory.create_customers', 'inventory.update_customers',
            # Paiements
            'inventory.view_payments', 'inventory.create_payments',
            # Rapports
            'inventory.view_reports', 'inventory.export_reports',
        ],
        'is_system_role': True,
    },

    'sales_agent': {
        'name': 'Agent Commercial',
        'description': 'Gestion des ventes et clients',
        'permissions': [
            'inventory.view_categories',
            'inventory.view_products',
            'inventory.view_stock',
            'inventory.view_sales', 'inventory.create_sales',
            'inventory.view_customers', 'inventory.create_customers', 'inventory.update_customers',
            'inventory.view_payments', 'inventory.create_payments',
        ],
        'is_system_role': True,
    },

    'warehouse_operator': {
        'name': 'Magasinier',
        'description': 'Gestion des stocks et réceptions',
        'permissions': [
            'inventory.view_categories',
            'inventory.view_warehouses',
            'inventory.view_products',
            'inventory.view_stock', 'inventory.manage_stock',
            'inventory.view_movements', 'inventory.create_movements',
            'inventory.view_orders', 'inventory.receive_orders',
            'inventory.view_stock_counts', 'inventory.create_stock_counts',
        ],
        'is_system_role': True,
    },

    'inventory_viewer': {
        'name': 'Consultation Inventaire',
        'description': 'Lecture seule sur l\'inventaire',
        'permissions': [
            'inventory.view_categories',
            'inventory.view_warehouses',
            'inventory.view_suppliers',
            'inventory.view_products',
            'inventory.view_stock',
            'inventory.view_movements',
            'inventory.view_orders',
            'inventory.view_stock_counts',
            'inventory.view_sales',
            'inventory.view_customers',
            'inventory.view_payments',
            'inventory.view_reports',
        ],
        'is_system_role': True,
    },
}


# ===============================
# EXPORTS PUBLICS
# ===============================

__all__ = [
    # Données
    'PERMISSIONS',
    'PERMISSION_CODES',
    'PREDEFINED_ROLES',
    # Classes de permission CRUD
    'CategoryPermission',
    'WarehousePermission',
    'SupplierPermission',
    'ProductPermission',
    'StockPermission',
    'MovementPermission',
    'OrderPermission',
    'StockCountPermission',
    'SalePermission',
    'CustomerPermission',
    'PaymentPermission',
    # Permissions spéciales
    'IsInventoryAdmin',
    'IsAdminUserOrEmployee',
]
