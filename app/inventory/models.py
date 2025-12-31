from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from lourabackend.models import TimeStampedModel
from core.models import Organization


# ===============================
# CATEGORY MANAGEMENT
# ===============================

class Category(TimeStampedModel):
    """
    Category: Catégories de produits
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='inventory_categories'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, help_text="Code unique de la catégorie")
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_categories'
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = [['organization', 'name']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ===============================
# WAREHOUSE MANAGEMENT
# ===============================

class Warehouse(TimeStampedModel):
    """
    Warehouse: Entrepôts de stockage
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='warehouses'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    manager_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_warehouses'
        verbose_name = "Entrepôt"
        verbose_name_plural = "Entrepôts"
        unique_together = [['organization', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ===============================
# SUPPLIER MANAGEMENT
# ===============================

class Supplier(TimeStampedModel):
    """
    Supplier: Fournisseurs
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='suppliers'
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="Numéro d'identification fiscale")
    payment_terms = models.CharField(max_length=200, blank=True, help_text="Conditions de paiement")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_suppliers'
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        unique_together = [['organization', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ===============================
# PRODUCT MANAGEMENT
# ===============================

class Product(TimeStampedModel):
    """
    Product: Produits en stock
    """
    UNIT_CHOICES = [
        ('unit', 'Unité'),
        ('kg', 'Kilogramme'),
        ('g', 'Gramme'),
        ('l', 'Litre'),
        ('ml', 'Millilitre'),
        ('m', 'Mètre'),
        ('m2', 'Mètre carré'),
        ('m3', 'Mètre cube'),
        ('box', 'Boîte'),
        ('pack', 'Pack'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, help_text="Code produit unique (SKU)")
    description = models.TextField(blank=True)

    # Pricing
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prix d'achat unitaire"
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Prix de vente unitaire"
    )

    # Stock
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='unit')
    min_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Niveau minimum de stock (alerte)"
    )
    max_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Niveau maximum de stock"
    )

    # Additional info
    barcode = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_products'
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        unique_together = [['organization', 'sku']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_total_stock(self):
        """Retourne le stock total dans tous les entrepôts"""
        return self.stocks.aggregate(
            total=models.Sum('quantity')
        )['total'] or Decimal('0.00')

    def is_low_stock(self):
        """Vérifie si le stock est en dessous du minimum"""
        return self.get_total_stock() <= self.min_stock_level


# ===============================
# STOCK MANAGEMENT
# ===============================

class Stock(TimeStampedModel):
    """
    Stock: Quantités de produits par entrepôt
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    location = models.CharField(max_length=100, blank=True, help_text="Emplacement dans l'entrepôt")

    class Meta:
        db_table = 'inventory_stocks'
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        unique_together = [['product', 'warehouse']]
        ordering = ['product', 'warehouse']

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}: {self.quantity}"


# ===============================
# MOVEMENT MANAGEMENT
# ===============================

class Movement(TimeStampedModel):
    """
    Movement: Mouvements de stock (entrées/sorties)
    """
    MOVEMENT_TYPE_CHOICES = [
        ('in', 'Entrée'),
        ('out', 'Sortie'),
        ('transfer', 'Transfert'),
        ('adjustment', 'Ajustement'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='inventory_movements'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reference = models.CharField(max_length=100, blank=True, help_text="Référence du mouvement")
    notes = models.TextField(blank=True)
    movement_date = models.DateTimeField()

    # Pour les transferts
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transfers'
    )
    
    # Liaison avec une commande (pour les entrées via réception de commande)
    order = models.ForeignKey(
        'inventory.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        help_text="Commande associée (automatique pour les entrées de réception)"
    )
    
    # Liaison avec une vente (pour les mouvements de sortie générés par ventes)
    sale = models.ForeignKey(
        'inventory.Sale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movements',
        help_text="Vente associée (automatique pour les sorties de vente)"
    )

    class Meta:
        db_table = 'inventory_movements'
        verbose_name = "Mouvement"
        verbose_name_plural = "Mouvements"
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"


# ===============================
# ORDER MANAGEMENT
# ===============================

class Order(TimeStampedModel):
    """
    Order: Commandes d'approvisionnement
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('received', 'Reçue'),
        ('cancelled', 'Annulée'),
    ]

    TRANSPORT_MODE_CHOICES = [
        ('', 'Non spécifié'),
        ('routier', 'Routier'),
        ('maritime', 'Maritime'),
        ('aerien', 'Aérien'),
        ('ferroviaire', 'Ferroviaire'),
        ('retrait', 'Retrait sur place'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='inventory_orders'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    order_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)

    # Champs Transport
    transport_mode = models.CharField(
        max_length=50,
        choices=TRANSPORT_MODE_CHOICES,
        blank=True,
        default='',
        verbose_name="Mode de transport"
    )
    transport_company = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name="Transporteur"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="Numéro de suivi"
    )
    transport_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Frais de transport"
    )
    transport_included = models.BooleanField(
        default=False,
        verbose_name="Frais de transport inclus dans le prix des produits"
    )
    transport_notes = models.TextField(
        blank=True,
        default='',
        verbose_name="Notes transport"
    )

    class Meta:
        db_table = 'inventory_orders'
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-order_date']

    def __str__(self):
        return f"Commande {self.order_number} - {self.supplier.name}"

    def calculate_total(self):
        """Calcule le total de la commande (produits + transport si non inclus)"""
        items_total = self.items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or Decimal('0.00')
        
        # Ajouter les frais de transport si non inclus dans le prix
        if not self.transport_included and self.transport_cost:
            return items_total + self.transport_cost
        return items_total


class OrderItem(TimeStampedModel):
    """
    OrderItem: Lignes de commande
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        db_table = 'inventory_order_items'
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"
        ordering = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_total(self):
        """Retourne le total de la ligne"""
        return self.quantity * self.unit_price


# ===============================
# STOCK COUNT (INVENTORY) MANAGEMENT
# ===============================

class StockCount(TimeStampedModel):
    """
    StockCount: Inventaire physique
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('planned', 'Planifié'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('validated', 'Validé'),
        ('cancelled', 'Annulé'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='stock_counts'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_counts'
    )
    count_number = models.CharField(max_length=100, unique=True)
    count_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_stock_counts'
        verbose_name = "Inventaire"
        verbose_name_plural = "Inventaires"
        ordering = ['-count_date']

    def __str__(self):
        return f"Inventaire {self.count_number} - {self.warehouse.name}"


class StockCountItem(TimeStampedModel):
    """
    StockCountItem: Lignes d'inventaire
    """
    stock_count = models.ForeignKey(
        StockCount,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='count_items'
    )
    expected_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Quantité attendue (système)"
    )
    counted_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Quantité comptée (physique)"
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_stock_count_items'
        verbose_name = "Ligne d'inventaire"
        verbose_name_plural = "Lignes d'inventaire"
        unique_together = [['stock_count', 'product']]
        ordering = ['stock_count', 'product']

    def __str__(self):
        return f"{self.product.name}: {self.counted_quantity}"

    def get_difference(self):
        """Retourne la différence entre attendu et compté"""
        return self.counted_quantity - self.expected_quantity


# ===============================
# ALERT MANAGEMENT
# ===============================

class Alert(TimeStampedModel):
    """
    Alert: Alertes de stock (stocks bas, péremption, etc.)
    """
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Stock bas'),
        ('out_of_stock', 'Rupture de stock'),
        ('overstock', 'Surstock'),
        ('expiring_soon', 'Expiration proche'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='inventory_alerts'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'inventory_alerts'
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.name}"


# ===============================
# SALES & COMMERCIAL DOCUMENTS
# ===============================
# Modèles pour la gestion des ventes, clients, paiements, factures, etc.


# ===============================
# CUSTOMER MANAGEMENT
# ===============================

class Customer(TimeStampedModel):
    """
    Customer: Clients de l'entreprise
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='customers'
    )
    name = models.CharField(max_length=200, verbose_name="Nom")
    code = models.CharField(max_length=50, blank=True, verbose_name="Code client")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    secondary_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone secondaire")
    address = models.TextField(blank=True, verbose_name="Adresse")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    country = models.CharField(max_length=100, blank=True, default="Guinée")
    tax_id = models.CharField(max_length=50, blank=True, verbose_name="NIF/RCCM")
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Limite de crédit"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_customers'
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        unique_together = [['organization', 'code']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code or 'N/A'})"

    def get_total_debt(self):
        """Retourne le montant total dû par le client"""
        from django.db.models import Sum
        total = self.credit_sales.filter(
            status__in=['pending', 'partial']
        ).aggregate(
            total=Sum('remaining_amount')
        )['total'] or Decimal('0.00')
        return total


# ===============================
# SALE MANAGEMENT (Ventes avec remises)
# ===============================

class Sale(TimeStampedModel):
    """
    Sale: Vente de produits avec support des remises
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('partial', 'Partiellement payé'),
        ('paid', 'Payé'),
        ('cancelled', 'Annulé'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('credit', 'À crédit'),
        ('other', 'Autre'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='sales'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales',
        null=True,
        blank=True,
        verbose_name="Client"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name="Entrepôt"
    )
    sale_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de vente")
    sale_date = models.DateTimeField(default=timezone.now, verbose_name="Date de vente")
    
    # Montants
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Sous-total"
    )
    
    # Remise globale sur le panier
    discount_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Pourcentage'), ('fixed', 'Montant fixe')],
        default='fixed',
        verbose_name="Type de remise"
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Valeur de la remise"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant de la remise"
    )
    
    # TVA (si applicable)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name="Taux de TVA (%)"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant TVA"
    )
    
    # Total final
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant total"
    )
    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant payé"
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Statut de paiement"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name="Mode de paiement"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    is_credit_sale = models.BooleanField(default=False, verbose_name="Vente à crédit")

    class Meta:
        db_table = 'inventory_sales'
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"
        ordering = ['-sale_date']

    def __str__(self):
        return f"Vente {self.sale_number} - {self.total_amount}"

    def calculate_totals(self):
        """Calcule les totaux de la vente"""
        # Calculer le sous-total (somme des lignes)
        from django.db.models import Sum, F
        lines_total = self.items.aggregate(
            total=Sum(F('quantity') * F('unit_price') - F('discount_amount'))
        )['total'] or Decimal('0.00')
        
        self.subtotal = lines_total
        
        # Appliquer la remise globale
        if self.discount_type == 'percentage':
            self.discount_amount = (self.subtotal * self.discount_value) / Decimal('100')
        else:
            self.discount_amount = self.discount_value
        
        after_discount = self.subtotal - self.discount_amount
        
        # Appliquer la TVA
        self.tax_amount = (after_discount * self.tax_rate) / Decimal('100')
        
        # Total final
        self.total_amount = after_discount + self.tax_amount
        
        # Mettre à jour le statut de paiement
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'pending'

    def get_remaining_amount(self):
        """Montant restant à payer"""
        return max(self.total_amount - self.paid_amount, Decimal('0.00'))


class SaleItem(TimeStampedModel):
    """
    SaleItem: Ligne de vente avec remise par produit
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire"
    )
    
    # Remise par produit
    discount_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Pourcentage'), ('fixed', 'Montant fixe')],
        default='fixed',
        verbose_name="Type de remise"
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Valeur de la remise"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant de la remise"
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Total ligne"
    )

    class Meta:
        db_table = 'inventory_sale_items'
        verbose_name = "Ligne de vente"
        verbose_name_plural = "Lignes de vente"
        ordering = ['sale', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def calculate_total(self):
        """Calcule le total de la ligne"""
        line_total = self.quantity * self.unit_price
        
        if self.discount_type == 'percentage':
            self.discount_amount = (line_total * self.discount_value) / Decimal('100')
        else:
            self.discount_amount = min(self.discount_value, line_total)
        
        self.total = line_total - self.discount_amount

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)


# ===============================
# PAYMENT MANAGEMENT (Reçus de paiement)
# ===============================

class Payment(TimeStampedModel):
    """
    Payment: Paiement/Reçu pour une vente
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('other', 'Autre'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments',
        null=True,
        blank=True
    )
    receipt_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de reçu")
    payment_date = models.DateTimeField(default=timezone.now, verbose_name="Date de paiement")
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name="Mode de paiement"
    )
    reference = models.CharField(max_length=200, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True)
    
    # Info client (peut être différent de celui de la vente)
    customer_name = models.CharField(max_length=200, blank=True, verbose_name="Nom du client")
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")

    class Meta:
        db_table = 'inventory_payments'
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Reçu {self.receipt_number} - {self.amount}"


# ===============================
# EXPENSE MANAGEMENT (Gestion des dépenses)
# ===============================

class ExpenseCategory(TimeStampedModel):
    """
    ExpenseCategory: Catégories de dépenses
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='expense_categories'
    )
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'inventory_expense_categories'
        verbose_name = "Catégorie de dépense"
        verbose_name_plural = "Catégories de dépenses"
        unique_together = [['organization', 'name']]
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(TimeStampedModel):
    """
    Expense: Dépenses de l'entreprise
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('other', 'Autre'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="Catégorie"
    )
    expense_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro")
    description = models.CharField(max_length=500, verbose_name="Description")
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant"
    )
    expense_date = models.DateField(verbose_name="Date de dépense")
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name="Mode de paiement"
    )
    reference = models.CharField(max_length=200, blank=True, verbose_name="Référence/Facture")
    beneficiary = models.CharField(max_length=200, blank=True, verbose_name="Bénéficiaire")
    notes = models.TextField(blank=True)
    receipt_image = models.URLField(max_length=500, blank=True, verbose_name="Image du reçu")

    class Meta:
        db_table = 'inventory_expenses'
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.description} - {self.amount}"


# ===============================
# PROFORMA INVOICE (Facture pro forma)
# ===============================

class ProformaInvoice(TimeStampedModel):
    """
    ProformaInvoice: Facture pro forma
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyée'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
        ('expired', 'Expirée'),
        ('converted', 'Convertie en vente'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='proforma_invoices'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='proforma_invoices',
        null=True,
        blank=True,
        verbose_name="Client"
    )
    # Info client pour les clients occasionnels
    client_name = models.CharField(max_length=200, blank=True, verbose_name="Nom du client")
    client_email = models.EmailField(blank=True, verbose_name="Email")
    client_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    client_address = models.TextField(blank=True, verbose_name="Adresse")
    
    proforma_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro pro forma")
    issue_date = models.DateField(verbose_name="Date d'émission")
    validity_date = models.DateField(verbose_name="Date de validité")
    
    # Montants
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Statut"
    )
    
    conditions = models.TextField(blank=True, verbose_name="Conditions de vente")
    notes = models.TextField(blank=True)
    
    # Vente liée (si convertie)
    converted_sale = models.ForeignKey(
        Sale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='from_proforma'
    )

    class Meta:
        db_table = 'inventory_proforma_invoices'
        verbose_name = "Facture pro forma"
        verbose_name_plural = "Factures pro forma"
        ordering = ['-issue_date']

    def __str__(self):
        return f"Proforma {self.proforma_number}"

    def is_expired(self):
        from django.utils import timezone
        return self.validity_date < timezone.now().date() and self.status not in ['converted', 'rejected']


class ProformaItem(TimeStampedModel):
    """
    ProformaItem: Ligne de facture pro forma
    """
    proforma = models.ForeignKey(
        ProformaInvoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='proforma_items'
    )
    description = models.CharField(max_length=500, blank=True, verbose_name="Description")
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        db_table = 'inventory_proforma_items'
        verbose_name = "Ligne pro forma"
        verbose_name_plural = "Lignes pro forma"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def calculate_total(self):
        self.total = (self.quantity * self.unit_price) - self.discount_amount

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)


# ===============================
# PURCHASE ORDER (Bon de commande amélioré)
# ===============================

class PurchaseOrder(TimeStampedModel):
    """
    PurchaseOrder: Bon de commande pour achats
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('sent', 'Envoyé'),
        ('partial', 'Partiellement livré'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name="Fournisseur"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name="Entrepôt de destination"
    )
    
    order_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de commande")
    order_date = models.DateField(verbose_name="Date de commande")
    expected_delivery_date = models.DateField(null=True, blank=True, verbose_name="Date de livraison prévue")
    
    # Montants
    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Frais de livraison"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Statut"
    )
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name="Conditions de paiement")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_purchase_orders'
        verbose_name = "Bon de commande"
        verbose_name_plural = "Bons de commande"
        ordering = ['-order_date']

    def __str__(self):
        return f"BC {self.order_number} - {self.supplier.name}"


class PurchaseOrderItem(TimeStampedModel):
    """
    PurchaseOrderItem: Ligne de bon de commande
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        db_table = 'inventory_purchase_order_items'
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ===============================
# DELIVERY NOTE (Bon de livraison)
# ===============================

class DeliveryNote(TimeStampedModel):
    """
    DeliveryNote: Bon de livraison
    """
    STATUS_CHOICES = [
        ('pending', 'En préparation'),
        ('ready', 'Prêt'),
        ('in_transit', 'En cours de livraison'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='delivery_notes'
    )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='delivery_notes',
        verbose_name="Vente"
    )
    delivery_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de livraison")
    delivery_date = models.DateField(verbose_name="Date de livraison")
    
    # Destinataire
    recipient_name = models.CharField(max_length=200, verbose_name="Nom du destinataire")
    recipient_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    delivery_address = models.TextField(verbose_name="Adresse de livraison")
    
    # Transporteur
    carrier_name = models.CharField(max_length=200, blank=True, verbose_name="Transporteur")
    driver_name = models.CharField(max_length=200, blank=True, verbose_name="Nom du chauffeur")
    vehicle_info = models.CharField(max_length=200, blank=True, verbose_name="Véhicule")
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    # Signatures (URLs vers les images)
    sender_signature = models.URLField(max_length=500, blank=True, verbose_name="Signature expéditeur")
    recipient_signature = models.URLField(max_length=500, blank=True, verbose_name="Signature destinataire")
    
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Livré le")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_delivery_notes'
        verbose_name = "Bon de livraison"
        verbose_name_plural = "Bons de livraison"
        ordering = ['-delivery_date']

    def __str__(self):
        return f"BL {self.delivery_number}"


class DeliveryNoteItem(TimeStampedModel):
    """
    DeliveryNoteItem: Ligne de bon de livraison
    """
    delivery_note = models.ForeignKey(
        DeliveryNote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='delivery_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    delivered_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Quantité livrée"
    )
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'inventory_delivery_note_items'
        verbose_name = "Ligne de livraison"
        verbose_name_plural = "Lignes de livraison"

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


# ===============================
# CREDIT SALE (Vente à crédit)
# ===============================

class CreditSale(TimeStampedModel):
    """
    CreditSale: Vente à crédit avec suivi des paiements
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('partial', 'Partiellement payé'),
        ('paid', 'Payé'),
        ('overdue', 'En retard'),
        ('cancelled', 'Annulé'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='credit_sales'
    )
    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name='credit_info',
        verbose_name="Vente"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='credit_sales',
        verbose_name="Client"
    )
    
    # Montants
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant total"
    )
    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant payé"
    )
    remaining_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant restant"
    )
    
    # Échéances
    due_date = models.DateField(verbose_name="Date d'échéance")
    grace_period_days = models.PositiveIntegerField(default=0, verbose_name="Jours de grâce")
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    # Rappels
    last_reminder_date = models.DateField(null=True, blank=True, verbose_name="Dernier rappel")
    reminder_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de rappels")
    
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_credit_sales'
        verbose_name = "Vente à crédit"
        verbose_name_plural = "Ventes à crédit"
        ordering = ['due_date']

    def __str__(self):
        return f"Crédit {self.sale.sale_number} - {self.remaining_amount} restant"

    def update_status(self):
        """Met à jour le statut basé sur les paiements et la date"""
        from django.utils import timezone
        
        self.remaining_amount = self.total_amount - self.paid_amount
        
        if self.remaining_amount <= 0:
            self.status = 'paid'
        elif self.paid_amount > 0:
            if self.due_date < timezone.now().date():
                self.status = 'overdue'
            else:
                self.status = 'partial'
        else:
            if self.due_date < timezone.now().date():
                self.status = 'overdue'
            else:
                self.status = 'pending'

    def save(self, *args, **kwargs):
        self.remaining_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)


class CreditPayment(TimeStampedModel):
    """
    CreditPayment: Paiement partiel pour une vente à crédit
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Espèces'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Chèque'),
        ('card', 'Carte bancaire'),
        ('other', 'Autre'),
    ]

    credit_sale = models.ForeignKey(
        CreditSale,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="Vente à crédit"
    )
    payment_date = models.DateField(verbose_name="Date de paiement")
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash',
        verbose_name="Mode de paiement"
    )
    reference = models.CharField(max_length=200, blank=True, verbose_name="Référence")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_credit_payments'
        verbose_name = "Paiement de crédit"
        verbose_name_plural = "Paiements de crédit"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Paiement {self.amount} - {self.credit_sale}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update credit sale after payment
        self.credit_sale.paid_amount = self.credit_sale.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        self.credit_sale.update_status()
        self.credit_sale.save()


# Import Supplier from main models for reference
from .models import Supplier
