# INVENTORY - Documentation

## Vue d'ensemble

L'application **inventory** gère la gestion complète des stocks et des ventes : produits, catégories, entrepôts, fournisseurs, mouvements de stock, commandes d'approvisionnement, inventaires physiques, alertes de stock, clients, ventes et paiements.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/inventory/`
- **Modèles** : 16 modèles (Category, Warehouse, Supplier, Product, Stock, Movement, Order, OrderItem, StockCount, StockCountItem, Alert, Customer, Sale, SaleItem, Payment, CreditSale)
- **ViewSets** : ~15 ViewSets
- **Endpoints** : ~100 endpoints
- **Dépendances** : `core` (Organization)

## Modèles de données

### Category

**Description** : Catégorie de produits (hiérarchie possible).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom de la catégorie
- `code` (CharField) : Code unique
- `description` (TextField) : Description
- `parent` (ForeignKey to self, nullable) : Catégorie parente
- `is_active` (BooleanField) : Catégorie active

### Warehouse

**Description** : Entrepôt de stockage.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom de l'entrepôt
- `code` (CharField) : Code unique
- `address`, `city`, `country` (CharField/TextField) : Adresse
- `manager_name` (CharField) : Nom du responsable
- `phone`, `email` (CharField) : Contact
- `is_active` (BooleanField) : Entrepôt actif

### Supplier

**Description** : Fournisseur.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom du fournisseur
- `code` (CharField) : Code unique
- `email`, `phone` (CharField) : Contact
- `address`, `city`, `country`, `postal_code`, `website` (CharField/TextField) : Coordonnées
- `contact_person` (CharField) : Personne de contact
- `tax_id` (CharField) : Numéro d'identification fiscale
- `payment_terms` (CharField) : Conditions de paiement
- `notes` (TextField) : Notes
- `is_active` (BooleanField) : Fournisseur actif

### Product

**Description** : Produit en stock.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `category` (ForeignKey, nullable) : Catégorie
- `name` (CharField) : Nom du produit
- `sku` (CharField) : Code produit unique (SKU)
- `description` (TextField) : Description
- `purchase_price` (DecimalField) : Prix d'achat unitaire
- `selling_price` (DecimalField) : Prix de vente unitaire
- `unit` (CharField) : Unité (unit, kg, l, m, etc.)
- `min_stock_level` (DecimalField) : Niveau minimum de stock (alerte)
- `max_stock_level` (DecimalField) : Niveau maximum de stock
- `barcode` (CharField) : Code-barres
- `image_url` (URLField) : URL de l'image
- `notes` (TextField) : Notes
- `is_active` (BooleanField) : Produit actif

**Méthodes importantes** :
- `get_total_stock()` : Retourne le stock total dans tous les entrepôts
- `is_low_stock()` : Vérifie si le stock est en dessous du minimum

### Stock

**Description** : Quantité d'un produit dans un entrepôt.

**Champs principaux** :
- `product` (ForeignKey) : Produit
- `warehouse` (ForeignKey) : Entrepôt
- `quantity` (DecimalField) : Quantité
- `location` (CharField) : Emplacement dans l'entrepôt

**Contrainte** : Unique ensemble (product, warehouse)

### Movement

**Description** : Mouvement de stock (entrée, sortie, transfert, ajustement).

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `product` (ForeignKey) : Produit
- `warehouse` (ForeignKey) : Entrepôt
- `movement_type` (CharField) : Type (in, out, transfer, adjustment)
- `quantity` (DecimalField) : Quantité
- `reference` (CharField) : Référence du mouvement
- `notes` (TextField) : Notes
- `movement_date` (DateTimeField) : Date du mouvement
- `destination_warehouse` (ForeignKey, nullable) : Entrepôt de destination (pour transferts)
- `order` (ForeignKey, nullable) : Commande associée (pour entrées)
- `sale` (ForeignKey, nullable) : Vente associée (pour sorties)

### Order

**Description** : Commande d'approvisionnement.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `supplier` (ForeignKey) : Fournisseur
- `warehouse` (ForeignKey) : Entrepôt de destination
- `order_number` (CharField, unique) : Numéro de commande
- `order_date` (DateField) : Date de commande
- `expected_delivery_date`, `actual_delivery_date` (DateField) : Dates de livraison
- `status` (CharField) : Statut (draft, pending, confirmed, received, cancelled)
- `total_amount` (DecimalField) : Montant total
- `notes` (TextField) : Notes
- `transport_mode`, `transport_company`, `tracking_number`, `transport_cost` (CharField/DecimalField) : Informations de transport
- `transport_included` (BooleanField) : Frais inclus dans le prix
- `transport_notes` (TextField) : Notes transport

**Méthodes importantes** :
- `calculate_total()` : Calcule le total (produits + transport si non inclus)

### OrderItem

**Description** : Ligne de commande.

**Champs principaux** :
- `order` (ForeignKey) : Commande
- `product` (ForeignKey) : Produit
- `quantity` (DecimalField) : Quantité commandée
- `unit_price` (DecimalField) : Prix unitaire
- `received_quantity` (DecimalField) : Quantité reçue

**Méthodes importantes** :
- `get_total()` : Retourne le total de la ligne (quantity * unit_price)

### StockCount

**Description** : Inventaire physique.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `warehouse` (ForeignKey) : Entrepôt
- `count_number` (CharField, unique) : Numéro d'inventaire
- `count_date` (DateField) : Date de comptage
- `status` (CharField) : Statut (draft, planned, in_progress, completed, validated, cancelled)
- `notes` (TextField) : Notes

### StockCountItem

**Description** : Ligne d'inventaire.

**Champs principaux** :
- `stock_count` (ForeignKey) : Inventaire
- `product` (ForeignKey) : Produit
- `expected_quantity` (DecimalField) : Quantité attendue (système)
- `counted_quantity` (DecimalField) : Quantité comptée (physique)
- `notes` (TextField) : Notes

**Méthodes importantes** :
- `get_difference()` : Retourne la différence (counted - expected)

### Alert

**Description** : Alerte de stock.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `product` (ForeignKey) : Produit
- `warehouse` (ForeignKey, nullable) : Entrepôt
- `alert_type` (CharField) : Type (stock_warning, low_stock, out_of_stock, overstock, high_value_low_stock, no_movement, expiring_soon)
- `severity` (CharField) : Sévérité (low, medium, high, critical)
- `message` (TextField) : Message d'alerte
- `is_resolved` (BooleanField) : Alerte résolue
- `resolved_at` (DateTimeField) : Date de résolution

### Customer

**Description** : Client de l'entreprise.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `name` (CharField) : Nom du client
- `code` (CharField) : Code client
- `email`, `phone`, `secondary_phone` (CharField) : Contact
- `address`, `city`, `country` (CharField/TextField) : Adresse
- `tax_id` (CharField) : NIF/RCCM
- `credit_limit` (DecimalField) : Limite de crédit
- `notes` (TextField) : Notes
- `is_active` (BooleanField) : Client actif

**Méthodes importantes** :
- `get_total_debt()` : Retourne le montant total dû par le client

### Sale

**Description** : Vente de produits avec support des remises et TVA.

**Champs principaux** :
- `organization` (ForeignKey) : Organisation
- `customer` (ForeignKey, nullable) : Client
- `warehouse` (ForeignKey) : Entrepôt
- `sale_number` (CharField, unique) : Numéro de vente
- `sale_date` (DateTimeField) : Date de vente
- `subtotal` (DecimalField) : Sous-total
- `discount_type` (CharField) : Type de remise (percentage, fixed)
- `discount_value` (DecimalField) : Valeur de la remise
- `discount_amount` (DecimalField) : Montant de la remise
- `tax_rate` (DecimalField) : Taux de TVA (%)
- `tax_amount` (DecimalField) : Montant TVA
- `total_amount` (DecimalField) : Montant total
- `paid_amount` (DecimalField) : Montant payé
- `payment_status` (CharField) : Statut (pending, partial, paid, cancelled)
- `payment_method` (CharField) : Méthode (cash, bank_transfer, mobile_money, check, card, credit, other)
- `notes` (TextField) : Notes

### SaleItem

**Description** : Ligne de vente.

**Champs principaux** :
- `sale` (ForeignKey) : Vente
- `product` (ForeignKey) : Produit
- `quantity` (DecimalField) : Quantité vendue
- `unit_price` (DecimalField) : Prix unitaire
- `discount_type` (CharField) : Type de remise (percentage, fixed, none)
- `discount_value` (DecimalField) : Valeur de la remise
- `discount_amount` (DecimalField) : Montant de la remise
- `subtotal` (DecimalField) : Sous-total (quantity * unit_price)
- `total` (DecimalField) : Total (subtotal - discount)

### Payment

**Description** : Paiement d'une vente.

**Champs principaux** :
- `sale` (ForeignKey) : Vente
- `payment_method` (CharField) : Méthode de paiement
- `amount` (DecimalField) : Montant
- `payment_date` (DateTimeField) : Date de paiement
- `reference` (CharField) : Référence du paiement
- `notes` (TextField) : Notes

### CreditSale

**Description** : Vente à crédit (gestion des dettes clients).

**Champs principaux** :
- `sale` (ForeignKey) : Vente
- `customer` (ForeignKey) : Client
- `due_date` (DateField) : Date d'échéance
- `status` (CharField) : Statut (pending, partial, paid, overdue, cancelled)
- `remaining_amount` (DecimalField) : Montant restant dû
- `notes` (TextField) : Notes

## API Endpoints

### Principaux ViewSets

- **CategoryViewSet** : CRUD catégories
- **WarehouseViewSet** : CRUD entrepôts
- **SupplierViewSet** : CRUD fournisseurs
- **ProductViewSet** : CRUD produits + `low_stock` action
- **StockViewSet** : CRUD stocks
- **MovementViewSet** : CRUD mouvements
- **OrderViewSet** : CRUD commandes + `confirm`, `receive`, `cancel` actions
- **StockCountViewSet** : CRUD inventaires + `validate`, `cancel` actions
- **AlertViewSet** : CRUD alertes + `resolve`, `generate_alerts` actions
- **CustomerViewSet** : CRUD clients
- **SaleViewSet** : CRUD ventes + `export_pdf`, `cancel` actions
- **PaymentViewSet** : CRUD paiements
- **CreditSaleViewSet** : CRUD ventes à crédit + `mark_paid`, `mark_overdue` actions

Tous les ViewSets suivent le pattern standard avec filtrage par organisation.

## Serializers

- CategorySerializer, WarehouseSerializer, SupplierSerializer
- ProductSerializer, ProductCreateSerializer, ProductListSerializer
- StockSerializer, MovementSerializer
- OrderSerializer, OrderCreateSerializer, OrderItemSerializer
- StockCountSerializer, StockCountItemSerializer
- AlertSerializer
- CustomerSerializer
- SaleSerializer, SaleCreateSerializer, SaleItemSerializer
- PaymentSerializer, CreditSaleSerializer

## Permissions

Utilise le système de permissions personnalisé de `core` avec des permissions spécifiques :
- `inventory.view_products`, `inventory.create_products`, `inventory.update_products`, `inventory.delete_products`
- `inventory.view_stock`, `inventory.manage_stock`
- `inventory.view_orders`, `inventory.create_orders`, `inventory.approve_orders`
- `inventory.view_sales`, `inventory.create_sales`, `inventory.manage_sales`
- etc.

## Services/Utilities

- **inventory/pdf_base.py** : PDFGeneratorMixin pour l'export PDF des ventes

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Gestion des produits** : Catalogue complet avec catégories, SKU, prix, niveaux de stock
2. **Gestion des stocks** : Multi-entrepôts, mouvements tracés, inventaires physiques
3. **Approvisionnement** : Commandes fournisseurs avec transport, réception partielle/totale
4. **Alertes automatiques** : Stock bas, rupture, surstock, produits sans mouvement
5. **Ventes** : POS complet avec remises, TVA, paiements partiels, ventes à crédit
6. **Clients** : Gestion des clients avec limite de crédit, suivi des dettes

## Points d'attention

### Stock multi-entrepôts
- Un produit peut avoir plusieurs stocks (un par entrepôt)
- `Product.get_total_stock()` agrège tous les stocks

### Mouvements de stock
- Les mouvements sont liés aux commandes (entrées) et aux ventes (sorties)
- Les transferts entre entrepôts utilisent `destination_warehouse`

### Commandes avec transport
- Les frais de transport peuvent être inclus ou non dans le prix des produits
- `Order.calculate_total()` tient compte de `transport_included`

### Ventes avec remises
- Remise globale sur la vente (percentage ou fixed)
- Remise par ligne de vente (SaleItem)
- TVA appliquée après remise

### Ventes à crédit
- Création automatique d'un CreditSale si payment_method='credit'
- Suivi des paiements partiels
- Statut overdue si date dépassée

### Alertes automatiques
- Action `generate_alerts` pour créer les alertes de stock
- Types d'alertes variés (stock_warning, low_stock, out_of_stock, overstock, high_value_low_stock, no_movement, expiring_soon)
- Résolution manuelle des alertes

### Export PDF
- Les ventes peuvent être exportées en PDF (factures)
- Utilise PDFGeneratorMixin
