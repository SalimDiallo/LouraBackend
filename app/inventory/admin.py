from django.contrib import admin
from .models import (
    Category, Expense, ExpenseCategory,
    Warehouse, Supplier, Product, Stock,
    Movement, Order, OrderItem, StockCount, StockCountItem, Alert,
    Customer, Sale, SaleItem, Payment, DeliveryNote, DeliveryNoteItem,
    CreditSale, ProformaInvoice, PurchaseOrder, PurchaseOrderItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'description', 'amount', 'expense_date', 'payment_method']
    list_filter = ['category', 'payment_method', 'organization']
    search_fields = ['expense_number', 'description', 'beneficiary', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'expense_date'


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'city']
    search_fields = ['name', 'code', 'address']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization']
    search_fields = ['name', 'code', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'organization', 'category', 'purchase_price', 'selling_price', 'is_active']
    list_filter = ['is_active', 'organization', 'category', 'unit']
    search_fields = ['name', 'sku', 'barcode']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'location', 'updated_at']
    list_filter = ['warehouse', 'product__organization']
    search_fields = ['product__name', 'warehouse__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'movement_type', 'quantity', 'movement_date', 'reference']
    list_filter = ['movement_type', 'organization', 'warehouse']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'movement_date'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'warehouse', 'order_date', 'status', 'total_amount']
    list_filter = ['status', 'organization', 'supplier', 'warehouse']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]


class StockCountItemInline(admin.TabularInline):
    model = StockCountItem
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ['count_number', 'warehouse', 'count_date', 'status']
    list_filter = ['status', 'organization', 'warehouse']
    search_fields = ['count_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'count_date'
    inlines = [StockCountItemInline]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_type', 'severity', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'organization']
    search_fields = ['product__name', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization', 'email', 'phone']
    list_filter = ['organization']
    search_fields = ['name', 'code', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at']


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'customer', 'sale_date', 'total_amount', 'payment_status']
    list_filter = ['payment_status', 'organization', 'customer']
    search_fields = ['sale_number', 'customer__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'sale_date'
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['sale', 'product', 'quantity', 'unit_price', 'discount_type', 'discount_amount', 'total']
    list_filter = ['sale', 'product']
    search_fields = ['sale__sale_number', 'product__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'sale', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'organization']
    search_fields = ['receipt_number', 'customer_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'


class DeliveryNoteItemInline(admin.TabularInline):
    model = DeliveryNoteItem
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DeliveryNote)
class DeliveryNoteAdmin(admin.ModelAdmin):
    list_display = ['delivery_number', 'sale', 'recipient_name', 'delivery_date']
    list_filter = ['organization', 'sale']
    search_fields = ['delivery_number', 'recipient_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'delivery_date'
    inlines = [DeliveryNoteItemInline]


@admin.register(DeliveryNoteItem)
class DeliveryNoteItemAdmin(admin.ModelAdmin):
    list_display = ['delivery_note', 'product', 'quantity', 'delivered_quantity']
    list_filter = ['delivery_note', 'product']
    search_fields = ['delivery_note__delivery_number', 'product__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ['sale', 'status', 'due_date']
    list_filter = ['status', 'organization']
    search_fields = ['sale__sale_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'


@admin.register(ProformaInvoice)
class ProformaInvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['id']
    list_filter = []
    search_fields = []
    readonly_fields = ['id', 'created_at', 'updated_at']


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'warehouse', 'order_date', 'status', 'total_amount']
    list_filter = ['status', 'organization', 'supplier', 'warehouse']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'unit_price', 'received_quantity']
    list_filter = ['purchase_order', 'product']
    search_fields = ['purchase_order__order_number', 'product__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
