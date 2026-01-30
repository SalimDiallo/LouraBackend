from rest_framework import serializers
from decimal import Decimal
from .models import (
    # Inventory models
    Category, Warehouse, Supplier, Product, Stock,
    Movement, Order, OrderItem, StockCount, StockCountItem, Alert,
    # Sales models
    Customer, Sale, SaleItem, Payment,
    ExpenseCategory, Expense,
    ProformaInvoice, ProformaItem,
    PurchaseOrder, PurchaseOrderItem,
    DeliveryNote, DeliveryNoteItem,
    CreditSale
)
from .serializers_base import InventoryBaseSerializer, InventoryListSerializer


# ===============================
# CATEGORY SERIALIZERS
# ===============================

class CategorySerializer(InventoryBaseSerializer):
    """Serializer for Category model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    # For reading: return parent ID as string
    parent = serializers.SerializerMethodField(read_only=True)
    # For writing: accept parent ID (UUID or null)
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='parent',
        write_only=True,
        required=False,
        allow_null=True
    )
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'organization', 'name', 'code', 'description', 'parent', 'parent_id', 'parent_name',
            'product_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_parent are now inherited from InventoryBaseSerializer

    def get_product_count(self, obj):
        return obj.products.count()

    def to_internal_value(self, data):
        """Handle parent field - map 'parent' to 'parent_id' for backward compatibility"""
        # If 'parent' is provided but not 'parent_id', use it
        if 'parent' in data and 'parent_id' not in data:
            data = data.copy()
            parent_value = data.pop('parent', None)
            if parent_value and parent_value != '':
                data['parent_id'] = parent_value
            else:
                data['parent_id'] = None
        return super().to_internal_value(data)


# ===============================
# WAREHOUSE SERIALIZERS
# ===============================

class WarehouseSerializer(InventoryBaseSerializer):
    """Serializer for Warehouse model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    total_stock_value = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            'id', 'organization', 'name', 'code', 'address', 'city', 'country',
            'manager_name', 'phone', 'email', 'product_count', 'total_stock_value',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization are inherited from InventoryBaseSerializer

    def get_product_count(self, obj):
        return obj.stocks.values('product').distinct().count()

    def get_total_stock_value(self, obj):
        from django.db.models import Sum, F
        total = obj.stocks.aggregate(
            total=Sum(F('quantity') * F('product__purchase_price'))
        )['total'] or 0
        return float(total)


# ===============================
# SUPPLIER SERIALIZERS
# ===============================

class SupplierSerializer(InventoryBaseSerializer):
    """Serializer for Supplier model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    total_orders_amount = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'organization', 'name', 'code', 'email', 'phone',
            'address', 'city', 'country', 'contact_person', 'tax_id',
            'website', 'postal_code',
            'payment_terms', 'notes', 'order_count', 'total_orders_amount',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization are inherited from InventoryBaseSerializer

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_orders_amount(self, obj):
        from django.db.models import Sum
        total = obj.orders.aggregate(total=Sum('total_amount'))['total'] or 0
        return float(total)


# ===============================
# PRODUCT SERIALIZERS
# ===============================

class StockSerializer(InventoryBaseSerializer):
    """Serializer for Stock model"""

    id = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    unit_cost = serializers.DecimalField(source='product.purchase_price', read_only=True, max_digits=12, decimal_places=2)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'unit_cost',
            'warehouse', 'warehouse_name', 'warehouse_code',
            'quantity', 'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_product, get_warehouse are inherited from InventoryBaseSerializer


class ProductSerializer(InventoryBaseSerializer):
    """Serializer for Product model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    # For reading: return category ID as string
    category = serializers.SerializerMethodField(read_only=True)
    # For writing: accept category ID (UUID or null)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    stocks = StockSerializer(many=True, read_only=True)
    total_stock = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'organization', 'category', 'category_id', 'category_name', 'name', 'sku',
            'description', 'purchase_price', 'selling_price', 'unit',
            'min_stock_level', 'max_stock_level', 'barcode', 'image_url',
            'notes', 'stocks', 'total_stock', 'stock_value', 'is_low_stock',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_category are inherited from InventoryBaseSerializer

    def get_total_stock(self, obj):
        return float(obj.get_total_stock())

    def get_stock_value(self, obj):
        return float(obj.get_total_stock() * obj.purchase_price)

    def get_is_low_stock(self, obj):
        return obj.is_low_stock()

    def to_internal_value(self, data):
        """Handle category field - map 'category' to 'category_id' for backward compatibility"""
        # If 'category' is provided but not 'category_id', use it
        if 'category' in data and 'category_id' not in data:
            data = data.copy()
            category_value = data.pop('category', None)
            if category_value and category_value != '':
                data['category_id'] = category_value
            else:
                data['category_id'] = None
        return super().to_internal_value(data)


class ProductListSerializer(InventoryBaseSerializer):
    """Lightweight serializer for product lists"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'organization', 'name', 'sku', 'category_name',
            'purchase_price', 'selling_price', 'unit', 'total_stock',
            'is_active'
        ]

    # get_id, get_organization are inherited from InventoryBaseSerializer

    def get_total_stock(self, obj):
        return float(obj.get_total_stock())


# ===============================
# MOVEMENT SERIALIZERS
# ===============================

class MovementSerializer(InventoryBaseSerializer):
    """Serializer for Movement model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    destination_warehouse = serializers.SerializerMethodField()
    destination_warehouse_name = serializers.CharField(source='destination_warehouse.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    # Commande associée (pour les entrées)
    order = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    supplier_name = serializers.SerializerMethodField()
    # Vente associée (pour les sorties)
    sale = serializers.SerializerMethodField()
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Movement
        fields = [
            'id', 'organization', 'product', 'product_name', 'product_sku',
            'warehouse', 'warehouse_name', 'movement_type', 'movement_type_display',
            'quantity', 'reference', 'notes', 'movement_date',
            'destination_warehouse', 'destination_warehouse_name',
            'order', 'order_number', 'supplier_name',  # Liaison commande/fournisseur
            'sale', 'sale_number', 'customer_name',  # Liaison vente/client
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_product, get_warehouse, get_order, get_sale are inherited from InventoryBaseSerializer

    def get_destination_warehouse(self, obj):
        return str(obj.destination_warehouse.id) if obj.destination_warehouse else None

    def get_supplier_name(self, obj):
        return obj.order.supplier.name if obj.order and obj.order.supplier else None

    def get_customer_name(self, obj):
        return obj.sale.customer.name if obj.sale and obj.sale.customer else None


class MovementCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating movements"""

    class Meta:
        model = Movement
        fields = [
            'product', 'warehouse', 'movement_type', 'quantity',
            'reference', 'notes', 'movement_date', 'destination_warehouse'
        ]

    def create(self, validated_data):
        """Create a movement with the organization from the view"""
        return Movement.objects.create(**validated_data)


# ===============================
# ORDER SERIALIZERS
# ===============================

class OrderItemSerializer(InventoryBaseSerializer):
    """Serializer for OrderItem model"""

    id = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'received_quantity', 'total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_order, get_product are inherited from InventoryBaseSerializer

    def get_total(self, obj):
        return float(obj.get_total())


class OrderSerializer(InventoryBaseSerializer):
    """Serializer for Order model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'organization', 'supplier', 'supplier_name', 'warehouse',
            'warehouse_name', 'order_number', 'order_date', 'expected_delivery_date',
            'actual_delivery_date', 'status', 'status_display', 'total_amount',
            'notes', 'items', 'item_count',
            # Transport
            'transport_mode', 'transport_company', 'tracking_number',
            'transport_cost', 'transport_included', 'transport_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_supplier, get_warehouse are inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


class OrderListSerializer(InventoryBaseSerializer):
    """Lightweight serializer for order lists"""

    id = serializers.SerializerMethodField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'supplier_name', 'warehouse_name',
            'order_date', 'expected_delivery_date', 'status', 'status_display',
            'total_amount', 'item_count',
            # Transport (pour affichage)
            'transport_mode', 'transport_cost', 'transport_included'
        ]

    # get_id is inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items"""

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price']


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating orders"""

    items = OrderItemCreateSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = [
            'supplier', 'warehouse', 'order_number', 'order_date',
            'expected_delivery_date', 'status', 'total_amount', 'notes', 'items',
            # Transport
            'transport_mode', 'transport_company', 'tracking_number',
            'transport_cost', 'transport_included', 'transport_notes'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)

        # Create order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()
            # Create new items
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        return instance


# ===============================
# STOCK COUNT SERIALIZERS
# ===============================

class StockCountItemSerializer(InventoryBaseSerializer):
    """Serializer for StockCountItem model"""

    id = serializers.SerializerMethodField()
    stock_count = serializers.SerializerMethodField()
    # product est en lecture pour afficher l'ID
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=False
    )
    product_id = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    difference = serializers.SerializerMethodField()

    class Meta:
        model = StockCountItem
        fields = [
            'id', 'stock_count', 'product', 'product_id', 'product_name', 'product_sku',
            'expected_quantity', 'counted_quantity', 'difference', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id is inherited from InventoryBaseSerializer

    def get_stock_count(self, obj):
        return str(obj.stock_count.id) if obj.stock_count else None

    def get_product_id(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_difference(self, obj):
        return float(obj.get_difference())

    def to_representation(self, instance):
        """Override to always return product as string ID"""
        ret = super().to_representation(instance)
        # Convertir product en string pour la lecture
        if instance.product:
            ret['product'] = str(instance.product.id)
        return ret


class StockCountSerializer(InventoryBaseSerializer):
    """Serializer for StockCount model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    warehouse = serializers.SerializerMethodField()
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        source='warehouse',
        write_only=True,
        required=False
    )
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = StockCountItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = StockCount
        fields = [
            'id', 'organization', 'warehouse', 'warehouse_id', 'warehouse_name', 'count_number',
            'count_date', 'status', 'status_display', 'notes', 'items',
            'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_warehouse are inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


# ===============================
# ALERT SERIALIZERS
# ===============================

class AlertSerializer(InventoryBaseSerializer):
    """Serializer for Alert model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'organization', 'product', 'product_name', 'product_sku',
            'warehouse', 'warehouse_name', 'alert_type', 'alert_type_display',
            'severity', 'severity_display', 'message', 'is_resolved',
            'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_product, get_warehouse are inherited from InventoryBaseSerializer

# ===============================
# CUSTOMER SERIALIZERS
# ===============================

class CustomerSerializer(InventoryBaseSerializer):
    """Serializer for Customer model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    total_debt = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'organization', 'name', 'code', 'email', 'phone',
            'secondary_phone', 'address', 'city', 'country', 'tax_id',
            'credit_limit', 'total_debt', 'notes', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization are inherited from InventoryBaseSerializer

    def get_total_debt(self, obj):
        return float(obj.get_total_debt())


# ===============================
# SALE SERIALIZERS
# ===============================

class SaleItemSerializer(InventoryBaseSerializer):
    """Serializer for SaleItem model"""

    id = serializers.SerializerMethodField()
    sale = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = SaleItem
        fields = [
            'id', 'sale', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'discount_type', 'discount_value',
            'discount_amount', 'total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'discount_amount', 'total', 'created_at', 'updated_at']

    # get_id, get_sale, get_product are inherited from InventoryBaseSerializer


class SaleItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating sale items"""
    
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price', 'discount_type', 'discount_value']


class SaleSerializer(InventoryBaseSerializer):
    """Serializer for Sale model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = SaleItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'organization', 'customer', 'customer_name', 'warehouse',
            'warehouse_name', 'sale_number', 'sale_date', 'subtotal',
            'discount_type', 'discount_value', 'discount_amount',
            'tax_rate', 'tax_amount', 'total_amount', 'paid_amount',
            'remaining_amount', 'payment_status', 'payment_status_display',
            'payment_method', 'payment_method_display', 'is_credit_sale',
            'notes', 'items', 'item_count', 'payments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subtotal', 'discount_amount', 'tax_amount',
                           'total_amount', 'created_at', 'updated_at']

    # get_id, get_organization, get_customer, get_warehouse are inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()

    def get_remaining_amount(self, obj):
        return float(obj.get_remaining_amount())

    def get_payments(self, obj):
        """Return list of payments for this sale"""
        payments = obj.payments.all().order_by('-payment_date')
        return [
            {
                'id': str(p.id),
                'receipt_number': p.receipt_number,
                'amount': float(p.amount),
                'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                'payment_method': p.payment_method,
                'payment_method_display': p.get_payment_method_display(),
                'reference': p.reference,
                'notes': p.notes,
            }
            for p in payments
        ]


class SaleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sales"""
    
    items = SaleItemCreateSerializer(many=True, required=False)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True
    )
    sale_number = serializers.CharField(required=False, allow_blank=True)
    
    due_date = serializers.DateField(required=False, write_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'customer', 'warehouse', 'sale_number', 'sale_date',
            'discount_type', 'discount_value', 'tax_rate',
            'paid_amount', 'payment_method', 'is_credit_sale', 'due_date', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        from django.utils import timezone
        import uuid
        
        items_data = validated_data.pop('items', [])
        
        # Auto-générer sale_number si non fourni
        if not validated_data.get('sale_number'):
            org = validated_data.get('organization')
            
            # Trouver le dernier numéro et incrémenter
            last = Sale.objects.filter(organization=org).order_by('-created_at').first()
            if last and last.sale_number:
                try:
                    num = int(last.sale_number.split('-')[-1])
                    new_number = f"VTE-{num + 1:06d}"
                except (ValueError, IndexError):
                    new_number = f"VTE-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            else:
                new_number = "VTE-000001"
            
            # Vérifier l'unicité et générer un numéro unique si nécessaire
            while Sale.objects.filter(sale_number=new_number).exists():
                # Ajouter un suffixe unique si le numéro existe déjà
                new_number = f"VTE-{timezone.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
            
            validated_data['sale_number'] = new_number
        
        # Filtrer les champs qui ne sont pas dans le modèle Sale (comme due_date)
        sale_data = {k: v for k, v in validated_data.items() if k != 'due_date'}
        sale = Sale.objects.create(**sale_data)
        
        for item_data in items_data:
            SaleItem.objects.create(sale=sale, **item_data)
        
        sale.calculate_totals()
        sale.save()
        
        return sale
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                SaleItem.objects.create(sale=instance, **item_data)
        
        instance.calculate_totals()
        instance.save()
        
        return instance


class SaleListSerializer(InventoryBaseSerializer):
    """Lightweight serializer for sale lists"""

    id = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'sale_number', 'customer_name', 'warehouse_name',
            'sale_date', 'total_amount', 'paid_amount',
            'payment_status', 'payment_status_display', 'item_count'
        ]

    # get_id is inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


# ===============================
# PAYMENT SERIALIZERS
# ===============================

class PaymentSerializer(InventoryBaseSerializer):
    """Serializer for Payment model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    sale = serializers.SerializerMethodField()
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'organization', 'sale', 'sale_number', 'receipt_number',
            'payment_date', 'amount', 'payment_method', 'payment_method_display',
            'reference', 'customer_name', 'customer_phone', 'notes','is_credit_payment'
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_sale are inherited from InventoryBaseSerializer


# ===============================
# EXPENSE SERIALIZERS
# ===============================

class ExpenseCategorySerializer(InventoryBaseSerializer):
    """Serializer for ExpenseCategory model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    expense_count = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'organization', 'name', 'description', 'expense_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization are inherited from InventoryBaseSerializer

    def get_expense_count(self, obj):
        return obj.expenses.count()


class ExpenseSerializer(InventoryBaseSerializer):
    """Serializer for Expense model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ExpenseCategory.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'organization', 'category', 'category_id', 'category_name',
            'expense_number', 'description', 'amount', 'expense_date',
            'payment_method', 'payment_method_display', 'reference',
            'beneficiary', 'notes', 'receipt_image',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_category are inherited from InventoryBaseSerializer


# ===============================
# PROFORMA INVOICE SERIALIZERS
# ===============================

class ProformaItemSerializer(InventoryBaseSerializer):
    """Serializer for ProformaItem model"""

    id = serializers.SerializerMethodField()
    proforma = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = ProformaItem
        fields = [
            'id', 'proforma', 'product', 'product_name', 'product_sku',
            'description', 'quantity', 'unit_price', 'discount_amount', 'total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']

    # get_id, get_product are inherited from InventoryBaseSerializer

    def get_proforma(self, obj):
        return str(obj.proforma.id) if obj.proforma else None


class ProformaItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating proforma items"""
    
    class Meta:
        model = ProformaItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'discount_amount']


class ProformaInvoiceSerializer(InventoryBaseSerializer):
    """Serializer for ProformaInvoice model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    customer = serializers.SerializerMethodField()
    customer_name_display = serializers.SerializerMethodField()
    items = ProformaItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ProformaInvoice
        fields = [
            'id', 'organization', 'customer', 'customer_name_display',
            'client_name', 'client_email', 'client_phone', 'client_address',
            'proforma_number', 'issue_date', 'validity_date',
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount',
            'status', 'status_display', 'is_expired', 'conditions', 'notes',
            'converted_sale', 'items', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subtotal', 'total_amount', 'created_at', 'updated_at']

    # get_id, get_organization, get_customer are inherited from InventoryBaseSerializer

    def get_customer_name_display(self, obj):
        if obj.customer:
            return obj.customer.name
        return obj.client_name

    def get_item_count(self, obj):
        return obj.items.count()

    def get_is_expired(self, obj):
        return obj.is_expired()


class ProformaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating proforma invoices"""
    
    items = ProformaItemCreateSerializer(many=True, required=False)
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        required=False,
        allow_null=True
    )
    proforma_number = serializers.CharField(required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False)
    validity_date = serializers.DateField(required=False)
    validity_days = serializers.IntegerField(write_only=True, required=False, default=30)
    
    class Meta:
        model = ProformaInvoice
        fields = [
            'customer', 'client_name', 'client_email', 'client_phone', 'client_address',
            'proforma_number', 'issue_date', 'validity_date', 'validity_days',
            'discount_amount', 'tax_amount', 'status', 'conditions', 'notes', 'items'
        ]
    
    def create(self, validated_data):
        from django.utils import timezone
        import uuid
        
        items_data = validated_data.pop('items', [])
        validity_days = validated_data.pop('validity_days', 30)
        
        # Auto-générer proforma_number si non fourni
        if not validated_data.get('proforma_number'):
            org = validated_data.get('organization')
            
            # Trouver le dernier numéro et incrémenter
            last = ProformaInvoice.objects.filter(organization=org).order_by('-created_at').first()
            if last and last.proforma_number:
                try:
                    num = int(last.proforma_number.split('-')[-1])
                    new_number = f"PRO-{num + 1:06d}"
                except (ValueError, IndexError):
                    new_number = f"PRO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            else:
                new_number = "PRO-000001"
            
            # Vérifier l'unicité
            while ProformaInvoice.objects.filter(proforma_number=new_number).exists():
                new_number = f"PRO-{timezone.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
            
            validated_data['proforma_number'] = new_number
        
        # Auto-générer issue_date si non fourni
        if not validated_data.get('issue_date'):
            validated_data['issue_date'] = timezone.now().date()
        
        # Auto-générer validity_date si non fourni
        if not validated_data.get('validity_date'):
            issue = validated_data.get('issue_date', timezone.now().date())
            from datetime import timedelta
            validated_data['validity_date'] = issue + timedelta(days=validity_days)
        
        proforma = ProformaInvoice.objects.create(**validated_data)
        
        subtotal = Decimal('0.00')
        for item_data in items_data:
            item = ProformaItem.objects.create(proforma=proforma, **item_data)
            subtotal += item.total
        
        proforma.subtotal = subtotal
        proforma.total_amount = subtotal - proforma.discount_amount + proforma.tax_amount
        proforma.save()
        
        return proforma


# ===============================
# PURCHASE ORDER SERIALIZERS
# ===============================

class PurchaseOrderItemSerializer(InventoryBaseSerializer):
    """Serializer for PurchaseOrderItem model"""

    id = serializers.SerializerMethodField()
    purchase_order = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'received_quantity', 'total',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']

    # get_id, get_product are inherited from InventoryBaseSerializer

    def get_purchase_order(self, obj):
        return str(obj.purchase_order.id) if obj.purchase_order else None


class PurchaseOrderSerializer(InventoryBaseSerializer):
    """Serializer for PurchaseOrder model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'organization', 'supplier', 'supplier_name', 'warehouse',
            'warehouse_name', 'order_number', 'order_date', 'expected_delivery_date',
            'subtotal', 'shipping_cost', 'tax_amount', 'total_amount',
            'status', 'status_display', 'payment_terms', 'notes',
            'items', 'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subtotal', 'total_amount', 'created_at', 'updated_at']

    # get_id, get_organization, get_supplier, get_warehouse are inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


# ===============================
# DELIVERY NOTE SERIALIZERS
# ===============================

class DeliveryNoteItemSerializer(InventoryBaseSerializer):
    """Serializer for DeliveryNoteItem model"""

    id = serializers.SerializerMethodField()
    delivery_note = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = DeliveryNoteItem
        fields = [
            'id', 'delivery_note', 'product', 'product_name', 'product_sku',
            'quantity', 'delivered_quantity', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_product are inherited from InventoryBaseSerializer

    def get_delivery_note(self, obj):
        return str(obj.delivery_note.id) if obj.delivery_note else None


class DeliveryNoteSerializer(InventoryBaseSerializer):
    """Serializer for DeliveryNote model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    sale = serializers.SerializerMethodField()
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    items = DeliveryNoteItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DeliveryNote
        fields = [
            'id', 'organization', 'sale', 'sale_number', 'delivery_number',
            'delivery_date', 'recipient_name', 'recipient_phone', 'delivery_address',
            'carrier_name', 'driver_name', 'vehicle_info',
            'status', 'status_display', 'sender_signature', 'recipient_signature',
            'delivered_at', 'notes', 'items', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # get_id, get_organization, get_sale are inherited from InventoryBaseSerializer

    def get_item_count(self, obj):
        return obj.items.count()


# ===============================
# CREDIT SALE SERIALIZERS
# ===============================



class CreditSaleSerializer(InventoryBaseSerializer):
    """Serializer for CreditSale model"""

    id = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    sale = serializers.SerializerMethodField()
    sale_number = serializers.CharField(source='sale.sale_number', read_only=True)
    customer = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    payments = serializers.SerializerMethodField()
    payment_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = CreditSale
        fields = [
            'id', 'organization', 'sale', 'sale_number', 'customer',
            'customer_name', 'customer_phone', 'total_amount', 'paid_amount',
            'remaining_amount', 'due_date', 'grace_period_days',
            'status', 'status_display', 'last_reminder_date', 'reminder_count',
            'days_until_due', 'is_overdue', 'notes', 'payments', 'payment_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'remaining_amount', 'created_at', 'updated_at']

    # get_id, get_organization, get_sale, get_customer are inherited from InventoryBaseSerializer

    def get_payments(self, obj):
        """Return list of payments for this credit sale via the sale relationship"""
        if obj.sale:
            payments = obj.sale.payments.all().order_by('-payment_date')
            return [
                {
                    'id': str(p.id),
                    'receipt_number': p.receipt_number,
                    'amount': float(p.amount),
                    'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                    'payment_method': p.payment_method,
                    'payment_method_display': p.get_payment_method_display(),
                    'reference': p.reference,
                    'notes': p.notes,
                }
                for p in payments
            ]
        return []

    def get_payment_count(self, obj):
        if obj.sale:
            return obj.sale.payments.count()
        return 0

    def get_days_until_due(self, obj):
        from django.utils import timezone
        if not obj.due_date:
            return None  # No due date set
        delta = obj.due_date - timezone.now().date()
        return delta.days

    def get_is_overdue(self, obj):
        from django.utils import timezone
        if not obj.due_date:
            return False  # No due date means cannot be overdue
        return obj.due_date < timezone.now().date() and obj.status not in ['paid', 'cancelled']

