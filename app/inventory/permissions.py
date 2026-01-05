"""
Inventory Permissions
=====================
Définition des permissions pour le module Inventory.
"""

PERMISSIONS = [
    # Categories
    {'code': 'inventory.view_categories', 'name': 'Voir les catégories', 'category': 'Catégories'},
    {'code': 'inventory.create_categories', 'name': 'Créer des catégories', 'category': 'Catégories'},
    {'code': 'inventory.update_categories', 'name': 'Modifier des catégories', 'category': 'Catégories'},
    {'code': 'inventory.delete_categories', 'name': 'Supprimer des catégories', 'category': 'Catégories'},

    # Warehouses
    {'code': 'inventory.view_warehouses', 'name': 'Voir les entrepôts', 'category': 'Entrepôts'},
    {'code': 'inventory.create_warehouses', 'name': 'Créer des entrepôts', 'category': 'Entrepôts'},
    {'code': 'inventory.update_warehouses', 'name': 'Modifier des entrepôts', 'category': 'Entrepôts'},
    {'code': 'inventory.delete_warehouses', 'name': 'Supprimer des entrepôts', 'category': 'Entrepôts'},

    # Suppliers
    {'code': 'inventory.view_suppliers', 'name': 'Voir les fournisseurs', 'category': 'Fournisseurs'},
    {'code': 'inventory.create_suppliers', 'name': 'Créer des fournisseurs', 'category': 'Fournisseurs'},
    {'code': 'inventory.update_suppliers', 'name': 'Modifier des fournisseurs', 'category': 'Fournisseurs'},
    {'code': 'inventory.delete_suppliers', 'name': 'Supprimer des fournisseurs', 'category': 'Fournisseurs'},

    # Products
    {'code': 'inventory.view_products', 'name': 'Voir les produits', 'category': 'Produits'},
    {'code': 'inventory.create_products', 'name': 'Créer des produits', 'category': 'Produits'},
    {'code': 'inventory.update_products', 'name': 'Modifier des produits', 'category': 'Produits'},
    {'code': 'inventory.delete_products', 'name': 'Supprimer des produits', 'category': 'Produits'},

    # Stock
    {'code': 'inventory.view_stock', 'name': 'Voir les stocks', 'category': 'Stocks'},
    {'code': 'inventory.manage_stock', 'name': 'Gérer les stocks', 'category': 'Stocks'},
    {'code': 'inventory.adjust_stock', 'name': 'Ajuster les stocks', 'category': 'Stocks'},

    # Movements
    {'code': 'inventory.view_movements', 'name': 'Voir les mouvements', 'category': 'Mouvements'},
    {'code': 'inventory.create_movements', 'name': 'Créer des mouvements', 'category': 'Mouvements'},
    {'code': 'inventory.update_movements', 'name': 'Modifier des mouvements', 'category': 'Mouvements'},
    {'code': 'inventory.delete_movements', 'name': 'Annuler des mouvements', 'category': 'Mouvements'},

    # Orders
    {'code': 'inventory.view_orders', 'name': 'Voir les commandes', 'category': 'Commandes'},
    {'code': 'inventory.create_orders', 'name': 'Créer des commandes', 'category': 'Commandes'},
    {'code': 'inventory.update_orders', 'name': 'Modifier des commandes', 'category': 'Commandes'},
    {'code': 'inventory.delete_orders', 'name': 'Annuler des commandes', 'category': 'Commandes'},
    {'code': 'inventory.receive_orders', 'name': 'Réceptionner des commandes', 'category': 'Commandes'},

    # Stock Counts
    {'code': 'inventory.view_stock_counts', 'name': 'Voir les inventaires', 'category': 'Inventaires'},
    {'code': 'inventory.create_stock_counts', 'name': 'Créer des inventaires', 'category': 'Inventaires'},
    {'code': 'inventory.validate_stock_counts', 'name': 'Valider des inventaires', 'category': 'Inventaires'},

    # Sales
    {'code': 'inventory.view_sales', 'name': 'Voir les ventes', 'category': 'Ventes'},
    {'code': 'inventory.create_sales', 'name': 'Créer des ventes', 'category': 'Ventes'},
    {'code': 'inventory.update_sales', 'name': 'Modifier des ventes', 'category': 'Ventes'},
    {'code': 'inventory.delete_sales', 'name': 'Annuler des ventes', 'category': 'Ventes'},

    # Customers
    {'code': 'inventory.view_customers', 'name': 'Voir les clients', 'category': 'Clients'},
    {'code': 'inventory.create_customers', 'name': 'Créer des clients', 'category': 'Clients'},
    {'code': 'inventory.update_customers', 'name': 'Modifier des clients', 'category': 'Clients'},
    {'code': 'inventory.delete_customers', 'name': 'Supprimer des clients', 'category': 'Clients'},

    # Payments
    {'code': 'inventory.view_payments', 'name': 'Voir les paiements', 'category': 'Paiements'},
    {'code': 'inventory.create_payments', 'name': 'Enregistrer des paiements', 'category': 'Paiements'},

    # Reports
    {'code': 'inventory.view_reports', 'name': 'Voir les rapports', 'category': 'Rapports'},
    {'code': 'inventory.export_reports', 'name': 'Exporter les rapports', 'category': 'Rapports'},
]
