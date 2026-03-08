from django.contrib import admin
from .models import (
    Category, Expense, Warehouse, Supplier, Product, Stock,
    Movement, Order, OrderItem, StockCount, StockCountItem, Alert
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


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

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'description', 'amount', 'expense_date', 'payment_method']
    list_filter = ['category', 'payment_method', 'organization']
    search_fields = ['expense_number', 'description', 'beneficiary', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'expense_date'