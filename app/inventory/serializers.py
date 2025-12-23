from rest_framework import serializers
from .models import (
    Category, Warehouse, Supplier, Product, Stock,
    Movement, Order, OrderItem, StockCount, StockCountItem, Alert
)


# ===============================
# CATEGORY SERIALIZERS
# ===============================

class CategorySerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_parent(self, obj):
        return str(obj.parent.id) if obj.parent else None

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

class WarehouseSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

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

class SupplierSerializer(serializers.ModelSerializer):
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
            'payment_terms', 'notes', 'order_count', 'total_orders_amount',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_order_count(self, obj):
        return obj.orders.count()

    def get_total_orders_amount(self, obj):
        from django.db.models import Sum
        total = obj.orders.aggregate(total=Sum('total_amount'))['total'] or 0
        return float(total)


# ===============================
# PRODUCT SERIALIZERS
# ===============================

class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""

    id = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    warehouse = serializers.SerializerMethodField()
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id', 'product', 'warehouse', 'warehouse_name', 'warehouse_code',
            'quantity', 'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_product(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_warehouse(self, obj):
        return str(obj.warehouse.id) if obj.warehouse else None


class ProductSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_category(self, obj):
        return str(obj.category.id) if obj.category else None

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


class ProductListSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_total_stock(self, obj):
        return float(obj.get_total_stock())


# ===============================
# MOVEMENT SERIALIZERS
# ===============================

class MovementSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Movement
        fields = [
            'id', 'organization', 'product', 'product_name', 'product_sku',
            'warehouse', 'warehouse_name', 'movement_type', 'movement_type_display',
            'quantity', 'reference', 'notes', 'movement_date',
            'destination_warehouse', 'destination_warehouse_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_product(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_warehouse(self, obj):
        return str(obj.warehouse.id) if obj.warehouse else None

    def get_destination_warehouse(self, obj):
        return str(obj.destination_warehouse.id) if obj.destination_warehouse else None


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

class OrderItemSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_order(self, obj):
        return str(obj.order.id) if obj.order else None

    def get_product(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_total(self, obj):
        return float(obj.get_total())


class OrderSerializer(serializers.ModelSerializer):
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
            'notes', 'items', 'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_supplier(self, obj):
        return str(obj.supplier.id) if obj.supplier else None

    def get_warehouse(self, obj):
        return str(obj.warehouse.id) if obj.warehouse else None

    def get_item_count(self, obj):
        return obj.items.count()


class OrderListSerializer(serializers.ModelSerializer):
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
            'total_amount', 'item_count'
        ]

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

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
            'expected_delivery_date', 'status', 'total_amount', 'notes', 'items'
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

class StockCountItemSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

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


class StockCountSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_warehouse(self, obj):
        return str(obj.warehouse.id) if obj.warehouse else None

    def get_item_count(self, obj):
        return obj.items.count()


# ===============================
# ALERT SERIALIZERS
# ===============================

class AlertSerializer(serializers.ModelSerializer):
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

    def get_id(self, obj):
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        return str(obj.organization.id) if obj.organization else None

    def get_product(self, obj):
        return str(obj.product.id) if obj.product else None

    def get_warehouse(self, obj):
        return str(obj.warehouse.id) if obj.warehouse else None
