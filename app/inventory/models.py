from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

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

    class Meta:
        db_table = 'inventory_orders'
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-order_date']

    def __str__(self):
        return f"Commande {self.order_number} - {self.supplier.name}"

    def calculate_total(self):
        """Calcule le total de la commande"""
        total = self.items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or Decimal('0.00')
        return total


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
