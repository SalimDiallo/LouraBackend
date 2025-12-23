"""
Inventory Views - ViewSets pour la gestion des stocks

Ce module contient les ViewSets pour :
- Catégories de produits
- Entrepôts
- Fournisseurs
- Produits et Stocks
- Mouvements de stock
- Commandes d'approvisionnement
- Inventaires physiques
- Alertes de stock
"""

from datetime import timedelta
from django.db.models import Sum, F, Q, Count, Max, Func
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Models
from core.models import Organization
from .models import (
    Category, Warehouse, Supplier, Product, Stock,
    Movement, Order, OrderItem, StockCount, StockCountItem, Alert
)

# Serializers
from .serializers import (
    CategorySerializer, WarehouseSerializer, SupplierSerializer,
    ProductSerializer, ProductListSerializer, StockSerializer,
    MovementSerializer, MovementCreateUpdateSerializer,
    OrderSerializer, OrderListSerializer, OrderItemSerializer,
    OrderCreateUpdateSerializer,
    StockCountSerializer, StockCountItemSerializer, AlertSerializer
)

# Mixins
from core.mixins import (
    OrganizationResolverMixin,
    OrganizationQuerySetMixin,
    OrganizationCreateMixin,
    BaseOrganizationViewSetMixin,
)


# ===============================
# CATEGORY VIEWSET
# ===============================

class CategoryViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing product categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by parent category
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.select_related('parent', 'organization')

    @action(detail=False, methods=['get'])
    def tree(self, request, organization_slug=None):
        """Get categories as a tree structure"""
        organization = self.get_organization_from_request()

        # Get root categories (no parent)
        root_categories = Category.objects.filter(
            organization=organization,
            parent__isnull=True
        )

        def build_tree(category):
            return {
                'id': str(category.id),
                'name': category.name,
                'description': category.description,
                'is_active': category.is_active,
                'product_count': category.products.count(),
                'children': [build_tree(child) for child in category.subcategories.all()]
            }

        tree = [build_tree(cat) for cat in root_categories]
        return Response(tree)


# ===============================
# WAREHOUSE VIEWSET
# ===============================

class WarehouseViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing warehouses
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.prefetch_related('stocks')

    @action(detail=True, methods=['get'])
    def inventory(self, request, organization_slug=None, pk=None):
        """Get current inventory for a warehouse"""
        warehouse = self.get_object()

        stocks = Stock.objects.filter(
            warehouse=warehouse
        ).select_related('product', 'product__category').order_by('product__name')

        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, organization_slug=None, pk=None):
        """Get statistics for a warehouse"""
        warehouse = self.get_object()

        stats = {
            'product_count': warehouse.stocks.values('product').distinct().count(),
            'total_stock_value': warehouse.stocks.aggregate(
                total=Sum(F('quantity') * F('product__purchase_price'))
            )['total'] or 0,
            'low_stock_products': Product.objects.filter(
                stocks__warehouse=warehouse,
                stocks__quantity__lte=F('min_stock_level')
            ).count(),
            'out_of_stock_products': warehouse.stocks.filter(quantity=0).count(),
        }

        return Response(stats)


# ===============================
# SUPPLIER VIEWSET
# ===============================

class SupplierViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing suppliers
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Search by name, code, or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['get'])
    def orders(self, request, organization_slug=None, pk=None):
        """Get all orders for a supplier"""
        supplier = self.get_object()
        orders = supplier.orders.all().order_by('-order_date')
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


# ===============================
# PRODUCT VIEWSET
# ===============================

class ProductViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing products
    """
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.annotate(
                total_stock=Sum('stocks__quantity')
            ).filter(total_stock__lte=F('min_stock_level'))

        # Search by name or SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )

        return queryset.select_related('category', 'organization').prefetch_related('stocks__warehouse')

    @action(detail=True, methods=['get'])
    def stock_by_warehouse(self, request, organization_slug=None, pk=None):
        """Get stock levels by warehouse for a product"""
        product = self.get_object()
        stocks = product.stocks.select_related('warehouse')
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def movements(self, request, organization_slug=None, pk=None):
        """Get movement history for a product"""
        product = self.get_object()
        movements = product.movements.all().order_by('-movement_date')
        serializer = MovementSerializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def can_delete(self, request, organization_slug=None, pk=None):
        """Check if product can be deleted (no stock)"""
        product = self.get_object()
        total_stock = product.stocks.aggregate(total=Sum('quantity'))['total'] or 0
        has_movements = product.movements.exists()
        has_order_items = product.order_items.exists() if hasattr(product, 'order_items') else False
        
        can_delete = total_stock == 0 and not has_movements and not has_order_items
        
        reasons = []
        if total_stock > 0:
            reasons.append(f"Le produit a {total_stock} unités en stock")
        if has_movements:
            reasons.append("Le produit a un historique de mouvements")
        if has_order_items:
            reasons.append("Le produit est lié à des commandes")
        
        return Response({
            'can_delete': can_delete,
            'total_stock': total_stock,
            'has_movements': has_movements,
            'has_order_items': has_order_items,
            'reasons': reasons
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete a product only if it has no stock.
        Products with stock cannot be deleted to prevent data integrity issues.
        """
        product = self.get_object()
        
        # Calculer le stock total du produit
        total_stock = product.stocks.aggregate(total=Sum('quantity'))['total'] or 0
        
        if total_stock > 0:
            return Response(
                {
                    'error': f"Impossible de supprimer ce produit car il a {total_stock} unités en stock. "
                             f"Veuillez d'abord vider le stock via un mouvement de sortie ou d'ajustement."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier s'il y a des mouvements liés
        if product.movements.exists():
            return Response(
                {
                    'error': "Impossible de supprimer ce produit car il a un historique de mouvements. "
                             "Vous pouvez désactiver le produit à la place.",
                    'suggestion': 'deactivate'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


# ===============================
# STOCK VIEWSET
# ===============================

class StockViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing stock levels
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Stock doesn't have organization FK directly, filter through product
        organization = self.get_organization_from_request()
        queryset = Stock.objects.filter(product__organization=organization)

        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset.select_related('product', 'warehouse')


# ===============================
# MOVEMENT VIEWSET
# ===============================

class MovementViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing stock movements
    """
    queryset = Movement.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MovementCreateUpdateSerializer
        return MovementSerializer

    def perform_create(self, serializer):
        """Create movement with organization and update stock levels"""
        import logging
        from decimal import Decimal
        logger = logging.getLogger(__name__)

        # Récupérer l'organisation
        organization = self.get_organization_from_request()
        logger.info(f"Creating Movement for organization: {organization.name}")

        # Valider avant de sauvegarder
        product = serializer.validated_data.get('product')
        warehouse = serializer.validated_data.get('warehouse')
        movement_type = serializer.validated_data.get('movement_type')
        # Convertir la quantité en Decimal pour les comparaisons
        quantity = Decimal(str(serializer.validated_data.get('quantity', 0)))
        destination_warehouse = serializer.validated_data.get('destination_warehouse')

        # Vérifier le stock actuel pour les sorties et transferts
        if movement_type in ['out', 'transfer']:
            current_stock = Stock.objects.filter(
                product=product,
                warehouse=warehouse
            ).first()
            
            # Convertir en Decimal pour la comparaison
            current_quantity = Decimal(str(current_stock.quantity)) if current_stock else Decimal('0')
            
            if current_quantity < quantity:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'quantity': f"Stock insuffisant. Stock actuel: {float(current_quantity)}, quantité demandée: {float(quantity)}. "
                               f"Le stock ne peut pas devenir négatif."
                })

        # Sauvegarder le mouvement avec l'organisation
        movement = serializer.save(organization=organization)

        # Update stock based on movement type
        stock, created = Stock.objects.get_or_create(
            product=movement.product,
            warehouse=movement.warehouse,
            defaults={'quantity': Decimal('0')}
        )

        # Convertir les quantités en Decimal pour les opérations
        stock_quantity = Decimal(str(stock.quantity))
        movement_quantity = Decimal(str(movement.quantity))

        if movement.movement_type == 'in':
            stock.quantity = stock_quantity + movement_quantity
        elif movement.movement_type == 'out':
            stock.quantity = stock_quantity - movement_quantity
        elif movement.movement_type == 'adjustment':
            # Pour les ajustements, on vérifie aussi que le résultat ne soit pas négatif
            if movement_quantity < Decimal('0'):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'quantity': "La quantité d'ajustement ne peut pas être négative."
                })
            stock.quantity = movement_quantity
        elif movement.movement_type == 'transfer' and movement.destination_warehouse:
            # Decrease from source warehouse
            stock.quantity = stock_quantity - movement_quantity
            # Increase in destination warehouse
            dest_stock, created = Stock.objects.get_or_create(
                product=movement.product,
                warehouse=movement.destination_warehouse,
                defaults={'quantity': Decimal('0')}
            )
            dest_stock_quantity = Decimal(str(dest_stock.quantity))
            dest_stock.quantity = dest_stock_quantity + movement_quantity
            dest_stock.save()

        stock.save()
        logger.info(f"Movement {movement.id} created, stock updated")

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by movement type
        movement_type = self.request.query_params.get('type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(movement_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(movement_date__lte=end_date)

        return queryset.select_related(
            'product', 'warehouse', 'destination_warehouse', 'organization'
        ).order_by('-movement_date')


# ===============================
# ORDER VIEWSET
# ===============================

class OrderViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders
    """
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OrderCreateUpdateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """Override to add debug logging"""
        import logging
        logger = logging.getLogger(__name__)

        organization = self.get_organization_from_request()
        logger.info(f"Creating Order for organization: {organization.name} (ID: {organization.id})")
        logger.info(f"Serializer data: {serializer.validated_data}")

        serializer.save(organization=organization)

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        order_status = self.request.query_params.get('status')
        if order_status:
            queryset = queryset.filter(status=order_status)

        # Filter by supplier
        supplier_id = self.request.query_params.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return queryset.select_related('supplier', 'warehouse', 'organization').prefetch_related('items')

    @action(detail=True, methods=['post'])
    def confirm(self, request, organization_slug=None, pk=None):
        """Confirm an order"""
        order = self.get_object()

        if order.status != 'draft' and order.status != 'pending':
            return Response(
                {'error': 'Seules les commandes en brouillon ou en attente peuvent être confirmées'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'confirmed'
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def receive(self, request, organization_slug=None, pk=None):
        """Mark order as received and update stock"""
        order = self.get_object()

        if order.status != 'confirmed':
            return Response(
                {'error': 'Seules les commandes confirmées peuvent être reçues'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update order status
        order.status = 'received'
        order.actual_delivery_date = timezone.now().date()
        order.save()

        # Create stock movements for each item
        for item in order.items.all():
            Movement.objects.create(
                organization=order.organization,
                product=item.product,
                warehouse=order.warehouse,
                movement_type='in',
                quantity=item.quantity,
                reference=f"Commande {order.order_number}",
                movement_date=timezone.now()
            )

            # Update stock
            stock, created = Stock.objects.get_or_create(
                product=item.product,
                warehouse=order.warehouse,
                defaults={'quantity': 0}
            )
            stock.quantity += item.quantity
            stock.save()

            # Update received quantity
            item.received_quantity = item.quantity
            item.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, organization_slug=None, pk=None):
        """Cancel an order"""
        order = self.get_object()

        if order.status == 'received':
            return Response(
                {'error': 'Les commandes reçues ne peuvent pas être annulées'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, organization_slug=None, pk=None):
        """Export order as PDF"""
        from django.http import HttpResponse
        from .pdf_generator import generate_order_pdf
        
        order = self.get_object()
        pdf_buffer = generate_order_pdf(order)
        
        filename = f"Commande_{order.order_number}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ===============================
# STOCK COUNT VIEWSET
# ===============================

class StockCountViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing stock counts (physical inventory)
    """
    queryset = StockCount.objects.all()
    serializer_class = StockCountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status
        count_status = self.request.query_params.get('status')
        if count_status:
            queryset = queryset.filter(status=count_status)

        # Filter by warehouse
        warehouse_id = self.request.query_params.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        return queryset.select_related('warehouse', 'organization').prefetch_related('items')

    @action(detail=True, methods=['post'])
    def start(self, request, organization_slug=None, pk=None):
        """Start a stock count"""
        stock_count = self.get_object()

        if stock_count.status != 'planned':
            return Response(
                {'error': 'Seuls les inventaires planifiés peuvent être démarrés'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_count.status = 'in_progress'
        stock_count.save()

        serializer = self.get_serializer(stock_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, organization_slug=None, pk=None):
        """Complete a stock count"""
        stock_count = self.get_object()

        if stock_count.status != 'in_progress':
            return Response(
                {'error': 'Seuls les inventaires en cours peuvent être terminés'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_count.status = 'completed'
        stock_count.save()

        serializer = self.get_serializer(stock_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate(self, request, organization_slug=None, pk=None):
        """Validate a stock count and adjust stock levels"""
        stock_count = self.get_object()

        if stock_count.status != 'completed':
            return Response(
                {'error': 'Seuls les inventaires terminés peuvent être validés'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create adjustments for differences
        for item in stock_count.items.all():
            if item.get_difference() != 0:
                Movement.objects.create(
                    organization=stock_count.organization,
                    product=item.product,
                    warehouse=stock_count.warehouse,
                    movement_type='adjustment',
                    quantity=item.counted_quantity,
                    reference=f"Inventaire {stock_count.count_number}",
                    notes=f"Ajustement: attendu {item.expected_quantity}, compté {item.counted_quantity}",
                    movement_date=timezone.now()
                )

                # Update stock
                stock, created = Stock.objects.get_or_create(
                    product=item.product,
                    warehouse=stock_count.warehouse,
                    defaults={'quantity': 0}
                )
                stock.quantity = item.counted_quantity
                stock.save()

        stock_count.status = 'validated'
        stock_count.save()

        serializer = self.get_serializer(stock_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, organization_slug=None, pk=None):
        """Cancel a stock count"""
        stock_count = self.get_object()

        if stock_count.status in ['validated', 'cancelled']:
            return Response(
                {'error': 'Cet inventaire ne peut pas être annulé'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock_count.status = 'cancelled'
        stock_count.save()

        serializer = self.get_serializer(stock_count)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_items(self, request, organization_slug=None, pk=None):
        """
        Génère automatiquement tous les articles d'inventaire à partir du stock actuel de l'entrepôt.
        Options disponibles via le body de la requête:
        - include_zero_stock: bool (default: False) - Inclure les produits avec stock = 0
        - category_id: uuid (optional) - Filtrer par catégorie
        - overwrite: bool (default: False) - Remplacer les items existants
        """
        stock_count = self.get_object()

        # Vérifier le statut
        if stock_count.status not in ['planned', 'draft', 'in_progress']:
            return Response(
                {'error': 'Impossible de générer des articles pour cet inventaire (statut invalide)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Options de la requête
        include_zero_stock = request.data.get('include_zero_stock', False)
        category_id = request.data.get('category_id')
        overwrite = request.data.get('overwrite', False)

        # Si overwrite, supprimer les items existants
        if overwrite:
            stock_count.items.all().delete()
        
        # Récupérer les stocks de l'entrepôt
        warehouse = stock_count.warehouse
        organization = stock_count.organization
        
        # Base query: tous les produits actifs de l'organisation
        products_query = Product.objects.filter(
            organization=organization,
            is_active=True
        )
        
        # Filtrer par catégorie si spécifié
        if category_id:
            products_query = products_query.filter(category_id=category_id)
        
        # Récupérer les produits déjà dans l'inventaire
        existing_product_ids = set(
            stock_count.items.values_list('product_id', flat=True)
        )
        
        items_created = 0
        items_skipped = 0
        
        for product in products_query:
            # Ignorer si déjà dans l'inventaire
            if product.id in existing_product_ids:
                items_skipped += 1
                continue
            
            # Récupérer le stock actuel de ce produit dans cet entrepôt
            try:
                stock = Stock.objects.get(product=product, warehouse=warehouse)
                expected_qty = stock.quantity
            except Stock.DoesNotExist:
                expected_qty = 0
            
            # Si stock = 0 et qu'on ne veut pas inclure les stocks à 0, ignorer
            if expected_qty == 0 and not include_zero_stock:
                continue
            
            # Créer l'item d'inventaire
            StockCountItem.objects.create(
                stock_count=stock_count,
                product=product,
                expected_quantity=expected_qty,
                counted_quantity=0,  # À compter par l'utilisateur
                notes=f"Généré automatiquement - Stock système: {expected_qty}"
            )
            items_created += 1
        
        # Rafraîchir les données
        stock_count.refresh_from_db()
        serializer = self.get_serializer(stock_count)
        
        return Response({
            'stock_count': serializer.data,
            'items_created': items_created,
            'items_skipped': items_skipped,
            'total_items': stock_count.items.count(),
            'message': f'{items_created} article(s) généré(s) automatiquement'
        })

    @action(detail=True, methods=['post'])
    def auto_fill_counts(self, request, organization_slug=None, pk=None):
        """
        Remplit automatiquement les quantités comptées avec les quantités attendues.
        Utile pour les inventaires de contrôle rapide où seules les différences sont saisies.
        """
        stock_count = self.get_object()

        if stock_count.status not in ['planned', 'draft', 'in_progress']:
            return Response(
                {'error': 'Impossible de remplir automatiquement cet inventaire'},
                status=status.HTTP_400_BAD_REQUEST
            )

        items_updated = stock_count.items.update(counted_quantity=F('expected_quantity'))

        stock_count.refresh_from_db()
        serializer = self.get_serializer(stock_count)

        return Response({
            'stock_count': serializer.data,
            'items_updated': items_updated,
            'message': f'{items_updated} article(s) pré-rempli(s) avec les quantités attendues'
        })

    @action(detail=True, methods=['get'])
    def discrepancies(self, request, organization_slug=None, pk=None):
        """
        Retourne uniquement les articles avec des écarts entre quantité attendue et comptée.
        """
        stock_count = self.get_object()

        # Filtrer les items avec des écarts
        items_with_discrepancy = []
        for item in stock_count.items.all():
            diff = item.get_difference()
            if diff != 0:
                items_with_discrepancy.append({
                    'id': str(item.id),
                    'product': str(item.product.id),
                    'product_name': item.product.name,
                    'product_sku': item.product.sku,
                    'expected_quantity': float(item.expected_quantity),
                    'counted_quantity': float(item.counted_quantity),
                    'difference': float(diff),
                    'difference_value': float(diff * item.product.purchase_price),
                    'notes': item.notes,
                })

        # Statistiques
        total_positive = sum(i['difference'] for i in items_with_discrepancy if i['difference'] > 0)
        total_negative = sum(i['difference'] for i in items_with_discrepancy if i['difference'] < 0)
        total_value_impact = sum(i['difference_value'] for i in items_with_discrepancy)

        return Response({
            'count_number': stock_count.count_number,
            'warehouse_name': stock_count.warehouse.name,
            'status': stock_count.status,
            'discrepancy_count': len(items_with_discrepancy),
            'total_surplus': float(total_positive),
            'total_deficit': float(total_negative),
            'total_value_impact': float(total_value_impact),
            'items': items_with_discrepancy
        })

    @action(detail=True, methods=['get'])
    def summary(self, request, organization_slug=None, pk=None):
        """
        Retourne un résumé complet de l'inventaire avec statistiques détaillées.
        """
        stock_count = self.get_object()
        items = stock_count.items.all()

        # Calculs
        total_items = items.count()
        total_expected = sum(float(i.expected_quantity) for i in items)
        total_counted = sum(float(i.counted_quantity) for i in items)
        
        items_with_discrepancy = [i for i in items if i.get_difference() != 0]
        items_surplus = [i for i in items if i.get_difference() > 0]
        items_deficit = [i for i in items if i.get_difference() < 0]
        items_matched = [i for i in items if i.get_difference() == 0]
        
        # Valeurs
        total_expected_value = sum(float(i.expected_quantity * i.product.purchase_price) for i in items)
        total_counted_value = sum(float(i.counted_quantity * i.product.purchase_price) for i in items)
        
        return Response({
            'count_number': stock_count.count_number,
            'warehouse_name': stock_count.warehouse.name,
            'count_date': stock_count.count_date,
            'status': stock_count.status,
            'status_display': stock_count.get_status_display(),
            'notes': stock_count.notes,
            'statistics': {
                'total_items': total_items,
                'items_matched': len(items_matched),
                'items_with_discrepancy': len(items_with_discrepancy),
                'items_surplus': len(items_surplus),
                'items_deficit': len(items_deficit),
                'match_rate': round((len(items_matched) / total_items * 100) if total_items > 0 else 0, 2),
            },
            'quantities': {
                'total_expected': total_expected,
                'total_counted': total_counted,
                'net_difference': total_counted - total_expected,
            },
            'values': {
                'total_expected_value': round(total_expected_value, 2),
                'total_counted_value': round(total_counted_value, 2),
                'value_difference': round(total_counted_value - total_expected_value, 2),
            },
            'created_at': stock_count.created_at,
            'updated_at': stock_count.updated_at,
        })

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, organization_slug=None, pk=None):
        """Export stock count as PDF"""
        from django.http import HttpResponse
        from .pdf_generator import generate_stock_count_pdf
        
        stock_count = self.get_object()
        pdf_buffer = generate_stock_count_pdf(stock_count)
        
        filename = f"Inventaire_{stock_count.count_number}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ===============================
# STOCK COUNT ITEM VIEWSET
# ===============================

class StockCountItemViewSet(OrganizationResolverMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing stock count items (nested under stock-counts)
    """
    queryset = StockCountItem.objects.all()
    serializer_class = StockCountItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter items by stock_count if provided"""
        stock_count_pk = self.kwargs.get('stock_count_pk')
        if stock_count_pk:
            return StockCountItem.objects.filter(
                stock_count_id=stock_count_pk
            ).select_related('product', 'stock_count')
        return StockCountItem.objects.none()

    def get_stock_count(self):
        """Get the parent stock count"""
        stock_count_pk = self.kwargs.get('stock_count_pk')
        organization = self.get_organization_from_request()
        return StockCount.objects.get(
            pk=stock_count_pk,
            organization=organization
        )

    def perform_create(self, serializer):
        """Create item with the parent stock count"""
        stock_count = self.get_stock_count()
        
        # Vérifier que l'inventaire est éditable
        if stock_count.status not in ['draft', 'planned', 'in_progress']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {'error': 'Impossible d\'ajouter des articles à cet inventaire'}
            )
        
        serializer.save(stock_count=stock_count)

    def perform_update(self, serializer):
        """Validate before update"""
        stock_count = self.get_stock_count()
        
        if stock_count.status not in ['draft', 'planned', 'in_progress']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {'error': 'Impossible de modifier les articles de cet inventaire'}
            )
        
        serializer.save()

    def perform_destroy(self, instance):
        """Validate before delete"""
        stock_count = self.get_stock_count()
        
        if stock_count.status not in ['draft', 'planned', 'in_progress']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {'error': 'Impossible de supprimer des articles de cet inventaire'}
            )
        
        instance.delete()


# ===============================
# ALERT VIEWSET
# ===============================

class AlertViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing stock alerts
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved')
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')

        # Filter by alert type
        alert_type = self.request.query_params.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)

        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        return queryset.select_related('product', 'warehouse', 'organization').order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve(self, request, organization_slug=None, pk=None):
        """Resolve an alert"""
        alert = self.get_object()

        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()

        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request, organization_slug=None):
        """Generate alerts for low stock products"""
        organization = self.get_organization_from_request()

        # Find products with low stock
        products = Product.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            total_stock=Sum('stocks__quantity')
        ).filter(
            total_stock__lte=F('min_stock_level')
        )

        alerts_created = 0
        for product in products:
            # Check if alert already exists and is not resolved
            existing_alert = Alert.objects.filter(
                product=product,
                alert_type='low_stock',
                is_resolved=False
            ).first()

            if not existing_alert:
                total_stock = product.get_total_stock()

                if total_stock == 0:
                    alert_type = 'out_of_stock'
                    severity = 'critical'
                    message = f"Rupture de stock pour {product.name}"
                else:
                    alert_type = 'low_stock'
                    severity = 'high'
                    message = f"Stock bas pour {product.name}: {total_stock} {product.get_unit_display()}"

                Alert.objects.create(
                    organization=organization,
                    product=product,
                    alert_type=alert_type,
                    severity=severity,
                    message=message
                )
                alerts_created += 1

        return Response({
            'message': f'{alerts_created} alertes créées',
            'count': alerts_created
        })


# ===============================
# DASHBOARD / STATS VIEWSET
# ===============================

class InventoryStatsViewSet(OrganizationResolverMixin, viewsets.ViewSet):
    """
    ViewSet for inventory statistics and reports
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request, organization_slug=None):
        """Get inventory overview statistics"""
        organization = self.get_organization_from_request()

        total_products = Product.objects.filter(
            organization=organization,
            is_active=True
        ).count()

        total_stock_value = Stock.objects.filter(
            product__organization=organization
        ).aggregate(
            total=Sum(F('quantity') * F('product__purchase_price'))
        )['total'] or 0

        low_stock_count = Product.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            total_stock=Sum('stocks__quantity')
        ).filter(
            total_stock__lte=F('min_stock_level')
        ).count()

        active_alerts = Alert.objects.filter(
            organization=organization,
            is_resolved=False
        ).count()

        pending_orders = Order.objects.filter(
            organization=organization,
            status__in=['draft', 'pending', 'confirmed']
        ).count()

        warehouse_count = Warehouse.objects.filter(
            organization=organization,
            is_active=True
        ).count()

        return Response({
            'total_products': total_products,
            'total_stock_value': float(total_stock_value),
            'low_stock_count': low_stock_count,
            'active_alerts': active_alerts,
            'pending_orders': pending_orders,
            'warehouse_count': warehouse_count,
        })

    @action(detail=False, methods=['get'])
    def top_products(self, request, organization_slug=None):
        """Get top products by stock value"""
        organization = self.get_organization_from_request()

        products = Product.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            total_stock=Sum('stocks__quantity'),
            stock_value=Sum(F('stocks__quantity') * F('purchase_price'))
        ).order_by('-stock_value')[:10]

        data = [{
            'id': str(p.id),
            'name': p.name,
            'sku': p.sku,
            'total_stock': float(p.total_stock or 0),
            'stock_value': float(p.stock_value or 0),
        } for p in products]

        return Response(data)

    @action(detail=False, methods=['get'])
    def stock_by_warehouse(self, request, organization_slug=None):
        """Get stock distribution by warehouse"""
        organization = self.get_organization_from_request()
        
        warehouses = Warehouse.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            product_count=Count('stocks__product', distinct=True),
            total_quantity=Sum('stocks__quantity'),
            total_value=Sum(F('stocks__quantity') * F('stocks__product__purchase_price')),
            low_stock_count=Count(
                'stocks__product',
                filter=Q(stocks__quantity__lte=F('stocks__product__min_stock_level')),
                distinct=True
            ),
            out_of_stock_count=Count(
                'stocks__product',
                filter=Q(stocks__quantity=0),
                distinct=True
            )
        )
        
        data = [{
            'id': str(w.id),
            'name': w.name,
            'code': w.code,
            'product_count': w.product_count or 0,
            'total_quantity': float(w.total_quantity or 0),
            'total_value': float(w.total_value or 0),
            'low_stock_count': w.low_stock_count or 0,
            'out_of_stock_count': w.out_of_stock_count or 0,
        } for w in warehouses]
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def stock_by_category(self, request, organization_slug=None):
        """Get stock distribution by category"""
        organization = self.get_organization_from_request()
        
        categories = Category.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            product_count=Count('products', filter=Q(products__is_active=True), distinct=True),
            total_quantity=Sum('products__stocks__quantity'),
            total_value=Sum(F('products__stocks__quantity') * F('products__purchase_price')),
            low_stock_count=Count(
                'products',
                filter=Q(
                    products__is_active=True,
                    products__stocks__quantity__lte=F('products__min_stock_level')
                ),
                distinct=True
            )
        )
        
        # Ajouter les produits sans catégorie
        uncategorized = Product.objects.filter(
            organization=organization,
            is_active=True,
            category__isnull=True
        ).aggregate(
            product_count=Count('id', distinct=True),
            total_quantity=Sum('stocks__quantity'),
            total_value=Sum(F('stocks__quantity') * F('purchase_price')),
            low_stock_count=Count(
                'id',
                filter=Q(stocks__quantity__lte=F('min_stock_level')),
                distinct=True
            )
        )
        
        data = [{
            'id': str(c.id),
            'name': c.name,
            'product_count': c.product_count or 0,
            'total_quantity': float(c.total_quantity or 0),
            'total_value': float(c.total_value or 0),
            'low_stock_count': c.low_stock_count or 0,
        } for c in categories]
        
        # Ajouter la catégorie "Sans catégorie" si elle contient des produits
        if uncategorized['product_count'] and uncategorized['product_count'] > 0:
            data.append({
                'id': None,
                'name': 'Sans catégorie',
                'product_count': uncategorized['product_count'] or 0,
                'total_quantity': float(uncategorized['total_quantity'] or 0),
                'total_value': float(uncategorized['total_value'] or 0),
                'low_stock_count': uncategorized['low_stock_count'] or 0,
            })
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def movement_history(self, request, organization_slug=None):
        """Get movement history aggregated by day/type"""
        organization = self.get_organization_from_request()
        
        # Paramètres de période
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        movements = Movement.objects.filter(
            organization=organization,
            movement_date__gte=start_date
        ).annotate(
            date=TruncDate('movement_date')
        ).values('date', 'movement_type').annotate(
            count=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__purchase_price'))
        ).order_by('date', 'movement_type')
        
        # Regrouper par date
        history = {}
        for m in movements:
            date_str = m['date'].isoformat()
            if date_str not in history:
                history[date_str] = {
                    'date': date_str,
                    'in': {'count': 0, 'quantity': 0, 'value': 0},
                    'out': {'count': 0, 'quantity': 0, 'value': 0},
                    'transfer': {'count': 0, 'quantity': 0, 'value': 0},
                    'adjustment': {'count': 0, 'quantity': 0, 'value': 0},
                }
            
            movement_type = m['movement_type']
            history[date_str][movement_type] = {
                'count': m['count'],
                'quantity': float(m['total_quantity'] or 0),
                'value': float(m['total_value'] or 0),
            }
        
        # Convertir en liste triée
        data = list(history.values())
        data.sort(key=lambda x: x['date'])
        
        # Statistiques globales
        summary = Movement.objects.filter(
            organization=organization,
            movement_date__gte=start_date
        ).aggregate(
            total_movements=Count('id'),
            total_in=Count('id', filter=Q(movement_type='in')),
            total_out=Count('id', filter=Q(movement_type='out')),
            total_transfers=Count('id', filter=Q(movement_type='transfer')),
            total_adjustments=Count('id', filter=Q(movement_type='adjustment')),
        )
        
        return Response({
            'period_days': days,
            'start_date': start_date.isoformat(),
            'history': data,
            'summary': summary,
        })

    @action(detail=False, methods=['get'])
    def low_rotation_products(self, request, organization_slug=None):
        """Get products with low stock rotation (dormant stock)"""
        organization = self.get_organization_from_request()
        
        # Paramètres
        days = int(request.query_params.get('days', 90))
        limit = int(request.query_params.get('limit', 20))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Produits avec stock mais peu ou pas de mouvements de sortie récents
        products = Product.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            total_stock=Sum('stocks__quantity'),
            stock_value=Sum(F('stocks__quantity') * F('purchase_price')),
            recent_out_movements=Count(
                'movements',
                filter=Q(
                    movements__movement_type='out',
                    movements__movement_date__gte=cutoff_date
                )
            ),
            recent_out_quantity=Sum(
                'movements__quantity',
                filter=Q(
                    movements__movement_type='out',
                    movements__movement_date__gte=cutoff_date
                )
            ),
            last_movement_date=Max('movements__movement_date')
        ).filter(
            total_stock__gt=0
        ).order_by('recent_out_movements', '-stock_value')[:limit]
        
        data = [{
            'id': str(p.id),
            'name': p.name,
            'sku': p.sku,
            'category_name': p.category.name if p.category else None,
            'total_stock': float(p.total_stock or 0),
            'stock_value': float(p.stock_value or 0),
            'recent_out_movements': p.recent_out_movements or 0,
            'recent_out_quantity': float(p.recent_out_quantity or 0),
            'last_movement_date': p.last_movement_date.isoformat() if p.last_movement_date else None,
            'days_since_last_movement': (timezone.now().date() - p.last_movement_date.date()).days if p.last_movement_date else None,
        } for p in products]
        
        return Response({
            'period_days': days,
            'products': data,
        })

    @action(detail=False, methods=['get'])
    def stock_counts_summary(self, request, organization_slug=None):
        """Get summary of recent stock counts"""
        organization = self.get_organization_from_request()
        
        # Paramètres
        limit = int(request.query_params.get('limit', 10))
        
        # Récupérer les inventaires récents avec leurs statistiques
        stock_counts = StockCount.objects.filter(
            organization=organization
        ).select_related('warehouse').annotate(
            item_count=Count('items'),
            items_with_discrepancy=Count(
                'items',
                filter=~Q(items__counted_quantity=F('items__expected_quantity'))
            ),
            total_expected=Sum('items__expected_quantity'),
            total_counted=Sum('items__counted_quantity'),
            total_difference=Sum(
                F('items__counted_quantity') - F('items__expected_quantity')
            ),
            absolute_difference=Sum(
                Func(
                    F('items__counted_quantity') - F('items__expected_quantity'),
                    function='ABS'
                )
            ),
        ).order_by('-count_date')[:limit]
        
        data = [{
            'id': str(sc.id),
            'count_number': sc.count_number,
            'count_date': sc.count_date.isoformat() if sc.count_date else None,
            'warehouse_name': sc.warehouse.name if sc.warehouse else None,
            'status': sc.status,
            'status_display': sc.get_status_display(),
            'item_count': sc.item_count or 0,
            'items_with_discrepancy': sc.items_with_discrepancy or 0,
            'total_expected': float(sc.total_expected or 0),
            'total_counted': float(sc.total_counted or 0),
            'total_difference': float(sc.total_difference or 0),
            'absolute_difference': float(sc.absolute_difference or 0),
            'accuracy_rate': (
                round((1 - (sc.items_with_discrepancy / sc.item_count)) * 100, 2)
                if sc.item_count and sc.item_count > 0 else 100
            ),
        } for sc in stock_counts]
        
        # Statistiques globales
        summary = StockCount.objects.filter(
            organization=organization
        ).aggregate(
            total_counts=Count('id'),
            validated_counts=Count('id', filter=Q(status='validated')),
            pending_counts=Count('id', filter=Q(status__in=['draft', 'planned', 'in_progress', 'completed'])),
        )
        
        return Response({
            'stock_counts': data,
            'summary': summary,
        })

    @action(detail=False, methods=['get'])
    def export_stock_list(self, request, organization_slug=None):
        """Export complete stock list as CSV"""
        import csv
        from django.http import HttpResponse
        
        organization = self.get_organization_from_request()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_list.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'SKU', 'Nom', 'Catégorie', 'Entrepôt', 'Quantité',
            'Prix achat', 'Prix vente', 'Valeur stock', 'Stock min', 'Stock max', 'Unité'
        ])
        
        stocks = Stock.objects.filter(
            product__organization=organization,
            product__is_active=True
        ).select_related('product', 'product__category', 'warehouse').order_by(
            'product__name', 'warehouse__name'
        )
        
        for stock in stocks:
            writer.writerow([
                stock.product.sku,
                stock.product.name,
                stock.product.category.name if stock.product.category else '',
                stock.warehouse.name,
                stock.quantity,
                float(stock.product.purchase_price),
                float(stock.product.selling_price),
                float(stock.quantity * stock.product.purchase_price),
                stock.product.min_stock_level,
                stock.product.max_stock_level,
                stock.product.unit,
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def export_movements(self, request, organization_slug=None):
        """Export movement history as CSV"""
        import csv
        from django.http import HttpResponse
        
        organization = self.get_organization_from_request()
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="movements_{days}days.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Référence', 'Type', 'Produit', 'SKU', 'Entrepôt',
            'Destination', 'Quantité', 'Valeur', 'Notes'
        ])
        
        movements = Movement.objects.filter(
            organization=organization,
            movement_date__gte=start_date
        ).select_related(
            'product', 'warehouse', 'destination_warehouse'
        ).order_by('-movement_date')
        
        for m in movements:
            writer.writerow([
                m.movement_date.isoformat() if m.movement_date else '',
                m.reference or '',
                m.get_movement_type_display(),
                m.product.name,
                m.product.sku,
                m.warehouse.name,
                m.destination_warehouse.name if m.destination_warehouse else '',
                m.quantity,
                float(m.quantity * m.product.purchase_price),
                m.notes or '',
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def export_alerts(self, request, organization_slug=None):
        """Export active alerts as CSV"""
        import csv
        from django.http import HttpResponse
        
        organization = self.get_organization_from_request()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alerts.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Date création', 'Type', 'Sévérité', 'Produit', 'SKU',
            'Entrepôt', 'Message', 'Résolu', 'Date résolution'
        ])
        
        alerts = Alert.objects.filter(
            organization=organization
        ).select_related('product', 'warehouse').order_by('-created_at')
        
        for alert in alerts:
            writer.writerow([
                alert.created_at.isoformat() if alert.created_at else '',
                alert.get_alert_type_display(),
                alert.get_severity_display(),
                alert.product.name if alert.product else '',
                alert.product.sku if alert.product else '',
                alert.warehouse.name if alert.warehouse else '',
                alert.message,
                'Oui' if alert.is_resolved else 'Non',
                alert.resolved_at.isoformat() if alert.resolved_at else '',
            ])
        
        return response

    @action(detail=False, methods=['get'])
    def export_products_pdf(self, request, organization_slug=None):
        """Export product catalog as PDF"""
        from django.http import HttpResponse
        from .pdf_generator import generate_product_catalog_pdf
        
        organization = self.get_organization_from_request()
        
        products = Product.objects.filter(
            organization=organization,
            is_active=True
        ).select_related('category').order_by('name')
        
        pdf_buffer = generate_product_catalog_pdf(products, organization)
        
        filename = f"Catalogue_Produits_{organization.subdomain}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['get'])
    def export_stock_pdf(self, request, organization_slug=None):
        """Export stock report as PDF"""
        from django.http import HttpResponse
        from .pdf_generator import generate_stock_report_pdf
        
        organization = self.get_organization_from_request()
        warehouse_id = request.query_params.get('warehouse')
        
        warehouse = None
        if warehouse_id:
            warehouse = Warehouse.objects.filter(
                id=warehouse_id,
                organization=organization
            ).first()
        
        stocks = Stock.objects.filter(
            product__organization=organization,
            product__is_active=True
        ).select_related('product', 'product__category', 'warehouse')
        
        if warehouse:
            stocks = stocks.filter(warehouse=warehouse)
        
        stocks = stocks.order_by('warehouse__name', 'product__name')
        
        pdf_buffer = generate_stock_report_pdf(list(stocks), organization, warehouse)
        
        warehouse_suffix = f"_{warehouse.code}" if warehouse else ""
        filename = f"Rapport_Stock{warehouse_suffix}_{organization.subdomain}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'])
    def generate_quote_pdf(self, request, organization_slug=None):
        """
        Generate a quote PDF from provided data
        
        Expected body:
        {
            "quote_number": "DEV-001",
            "date": "2024-01-15",
            "valid_until": "2024-02-15",
            "client_name": "Client Name",
            "client_email": "client@email.com",
            "client_phone": "+224 XXX XXX XXX",
            "client_address": "Address",
            "items": [
                {"product_name": "Product 1", "quantity": 10, "unit_price": 50000},
                ...
            ],
            "notes": "Optional notes",
            "discount_percent": 5
        }
        """
        from django.http import HttpResponse
        from .pdf_generator import generate_quote_pdf
        from datetime import datetime
        
        organization = self.get_organization_from_request()
        quote_data = request.data
        
        # Validate required fields
        if not quote_data.get('client_name'):
            return Response({'error': 'client_name est requis'}, status=status.HTTP_400_BAD_REQUEST)
        if not quote_data.get('items'):
            return Response({'error': 'items est requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse dates if strings
        if isinstance(quote_data.get('date'), str):
            quote_data['date'] = datetime.strptime(quote_data['date'], '%Y-%m-%d').date()
        if isinstance(quote_data.get('valid_until'), str):
            quote_data['valid_until'] = datetime.strptime(quote_data['valid_until'], '%Y-%m-%d').date()
        
        pdf_buffer = generate_quote_pdf(quote_data, organization)
        
        quote_number = quote_data.get('quote_number', 'DEVIS')
        filename = f"Devis_{quote_number}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'])
    def generate_invoice_pdf(self, request, organization_slug=None):
        """
        Generate an invoice PDF from provided data
        
        Expected body:
        {
            "invoice_number": "FAC-001",
            "date": "2024-01-15",
            "due_date": "2024-02-15",
            "client_name": "Client Name",
            "client_email": "client@email.com",
            "client_phone": "+224 XXX XXX XXX",
            "client_address": "Address",
            "items": [
                {"product_name": "Product 1", "quantity": 10, "unit_price": 50000},
                ...
            ],
            "notes": "Optional notes",
            "discount_percent": 0,
            "tax_percent": 18,
            "is_paid": false
        }
        """
        from django.http import HttpResponse
        from .pdf_generator import generate_invoice_pdf
        from datetime import datetime
        
        organization = self.get_organization_from_request()
        invoice_data = request.data
        
        # Validate required fields
        if not invoice_data.get('client_name'):
            return Response({'error': 'client_name est requis'}, status=status.HTTP_400_BAD_REQUEST)
        if not invoice_data.get('items'):
            return Response({'error': 'items est requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse dates if strings
        if isinstance(invoice_data.get('date'), str):
            invoice_data['date'] = datetime.strptime(invoice_data['date'], '%Y-%m-%d').date()
        if isinstance(invoice_data.get('due_date'), str):
            invoice_data['due_date'] = datetime.strptime(invoice_data['due_date'], '%Y-%m-%d').date()
        
        pdf_buffer = generate_invoice_pdf(invoice_data, organization)
        
        invoice_number = invoice_data.get('invoice_number', 'FACTURE')
        filename = f"Facture_{invoice_number}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
