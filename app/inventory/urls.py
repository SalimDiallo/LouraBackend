from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Inventory ViewSets
    CategoryViewSet,
    WarehouseViewSet,
    SupplierViewSet,
    ProductViewSet,
    StockViewSet,
    MovementViewSet,
    OrderViewSet,
    StockCountViewSet,
    StockCountItemViewSet,
    AlertViewSet,
    InventoryStatsViewSet,
    # Sales ViewSets
    CustomerViewSet,
    SaleViewSet,
    PaymentViewSet,
    ExpenseCategoryViewSet,
    ExpenseViewSet,
    ProformaInvoiceViewSet,
    PurchaseOrderViewSet,
    DeliveryNoteViewSet,
    CreditSaleViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'movements', MovementViewSet, basename='movement')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'stock-counts', StockCountViewSet, basename='stockcount')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'stats', InventoryStatsViewSet, basename='stats')

# Sales & Commercial Documents
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'proformas', ProformaInvoiceViewSet, basename='proforma')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'delivery-notes', DeliveryNoteViewSet, basename='delivery-note')
router.register(r'credit-sales', CreditSaleViewSet, basename='credit-sale')

# Manual nested routes for stock count items
stock_count_items_list = StockCountItemViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
stock_count_items_detail = StockCountItemViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    path('', include(router.urls)),
    # Nested routes for stock count items
    path('stock-counts/<uuid:stock_count_pk>/items/', stock_count_items_list, name='stockcount-items-list'),
    path('stock-counts/<uuid:stock_count_pk>/items/<uuid:pk>/', stock_count_items_detail, name='stockcount-items-detail'),
]
