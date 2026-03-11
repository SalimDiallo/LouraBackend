"""
Repository classes for the inventory application.

This module implements the Repository pattern to centralize data access logic
and complex queries, eliminating repetitive queryset filtering across views.
"""

from django.db.models import Q, Prefetch, Count, Sum, F, Avg
from django.db.models.functions import Coalesce


class BaseRepository:
    """
    Base repository with common query patterns.

    All model repositories should inherit from this class.
    """

    model = None  # Subclasses must define the model

    @classmethod
    def get_by_id(cls, pk, organization=None):
        """
        Get a single object by ID, optionally filtered by organization.

        Args:
            pk: Primary key of the object
            organization: Organization instance (for multi-tenant filtering)

        Returns:
            Model instance or None
        """
        queryset = cls.model.objects.all()
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset.filter(pk=pk).first()

    @classmethod
    def get_all(cls, organization):
        """
        Get all objects for an organization.

        Args:
            organization: Organization instance

        Returns:
            QuerySet
        """
        return cls.model.objects.filter(organization=organization)

    @classmethod
    def get_active(cls, organization):
        """
        Get only active objects.

        Args:
            organization: Organization instance

        Returns:
            QuerySet
        """
        return cls.get_all(organization).filter(is_active=True)

    @classmethod
    def search(cls, organization, search_term, search_fields=None):
        """
        Search objects by multiple fields.

        Args:
            organization: Organization instance
            search_term: Search string
            search_fields: List of field names to search in

        Returns:
            QuerySet
        """
        if not search_term or not search_fields:
            return cls.get_all(organization)

        # Build Q objects for each search field
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": search_term})

        return cls.get_all(organization).filter(query)


class CategoryRepository(BaseRepository):
    """Repository for Category model."""

    @classmethod
    def _get_model(cls):
        from .models import Category
        return Category

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """
        Get filtered categories.

        Args:
            organization: Organization instance
            filters: Dict of filter parameters

        Returns:
            QuerySet
        """
        from .models import Category

        queryset = Category.objects.filter(organization=organization)

        if not filters:
            return queryset

        # Filter by active status
        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        # Filter by parent category
        if 'parent_id' in filters and filters['parent_id']:
            queryset = queryset.filter(parent_id=filters['parent_id'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(description__icontains=search_term)
            )

        return queryset.select_related('parent', 'organization').order_by('name')

    @classmethod
    def get_root_categories(cls, organization):
        """Get categories without parent (root level)."""
        from .models import Category
        return Category.objects.filter(
            organization=organization,
            parent__isnull=True
        ).order_by('name')


class WarehouseRepository(BaseRepository):
    """Repository for Warehouse model."""

    @classmethod
    def _get_model(cls):
        from .models import Warehouse
        return Warehouse

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered warehouses with stock information."""
        from .models import Warehouse

        queryset = Warehouse.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('organization')

        # Filter by active status
        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        # Filter by city
        if 'city' in filters and filters['city']:
            queryset = queryset.filter(city__iexact=filters['city'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(address__icontains=search_term) |
                Q(city__icontains=search_term) |
                Q(manager_name__icontains=search_term)
            )

        return queryset.select_related('organization').prefetch_related('stocks')


class SupplierRepository(BaseRepository):
    """Repository for Supplier model."""

    @classmethod
    def _get_model(cls):
        from .models import Supplier
        return Supplier

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered suppliers."""
        from .models import Supplier

        queryset = Supplier.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('organization')

        # Filter by active status
        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        # Filter by city
        if 'city' in filters and filters['city']:
            queryset = queryset.filter(city__iexact=filters['city'])

        # Filter by country
        if 'country' in filters and filters['country']:
            queryset = queryset.filter(country__iexact=filters['country'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone__icontains=search_term) |
                Q(contact_person__icontains=search_term)
            )

        return queryset.select_related('organization').order_by('name')


class ProductRepository(BaseRepository):
    """Repository for Product model."""

    @classmethod
    def _get_model(cls):
        from .models import Product
        return Product

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered products with related data."""
        from .models import Product

        queryset = Product.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('category', 'organization').prefetch_related('stocks')

        # Filter by active status
        if 'is_active' in filters and filters['is_active'] is not None:
            queryset = queryset.filter(is_active=filters['is_active'])

        # Filter by category
        if 'category_id' in filters and filters['category_id']:
            queryset = queryset.filter(category_id=filters['category_id'])

        # Filter by product type
        if 'product_type' in filters and filters['product_type']:
            queryset = queryset.filter(product_type=filters['product_type'])

        # Filter by stock availability
        if 'in_stock' in filters and filters['in_stock'] is not None:
            if filters['in_stock']:
                # Products with stock > 0
                queryset = queryset.filter(stocks__quantity__gt=0).distinct()
            else:
                # Products with no stock or stock = 0
                queryset = queryset.filter(
                    Q(stocks__isnull=True) | Q(stocks__quantity=0)
                ).distinct()

        # Filter by price range
        if 'min_price' in filters and filters['min_price'] is not None:
            queryset = queryset.filter(sale_price__gte=filters['min_price'])

        if 'max_price' in filters and filters['max_price'] is not None:
            queryset = queryset.filter(sale_price__lte=filters['max_price'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(sku__icontains=search_term) |
                Q(barcode__icontains=search_term) |
                Q(description__icontains=search_term)
            )

        return queryset.select_related(
            'category',
            'organization'
        ).prefetch_related('stocks__warehouse').distinct()

    @classmethod
    def get_low_stock_products(cls, organization, threshold=None):
        """Get products with stock below minimum threshold."""
        from .models import Product

        queryset = Product.objects.filter(
            organization=organization,
            track_inventory=True
        ).annotate(
            total_stock=Coalesce(Sum('stocks__quantity'), 0)
        )

        if threshold:
            return queryset.filter(total_stock__lte=threshold)
        else:
            # Use the product's own minimum_stock field
            return queryset.filter(total_stock__lte=F('minimum_stock'))

    @classmethod
    def get_products_with_stock_value(cls, organization):
        """Get products annotated with total stock value."""
        from .models import Product

        return Product.objects.filter(
            organization=organization
        ).annotate(
            total_quantity=Coalesce(Sum('stocks__quantity'), 0),
            stock_value=Sum(F('stocks__quantity') * F('purchase_price'))
        ).select_related('category')


class OrderRepository(BaseRepository):
    """Repository for Order model."""

    @classmethod
    def _get_model(cls):
        from .models import Order
        return Order

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered orders."""
        from .models import Order

        queryset = Order.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('supplier', 'warehouse', 'organization')

        # Filter by status
        if 'status' in filters and filters['status']:
            queryset = queryset.filter(status=filters['status'])

        # Filter by supplier
        if 'supplier_id' in filters and filters['supplier_id']:
            queryset = queryset.filter(supplier_id=filters['supplier_id'])

        # Filter by warehouse
        if 'warehouse_id' in filters and filters['warehouse_id']:
            queryset = queryset.filter(warehouse_id=filters['warehouse_id'])

        # Filter by date range
        if 'start_date' in filters and filters['start_date']:
            queryset = queryset.filter(order_date__gte=filters['start_date'])

        if 'end_date' in filters and filters['end_date']:
            queryset = queryset.filter(order_date__lte=filters['end_date'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(order_number__icontains=search_term) |
                Q(reference__icontains=search_term) |
                Q(notes__icontains=search_term)
            )

        return queryset.select_related(
            'supplier',
            'warehouse',
            'organization'
        ).prefetch_related('items__product').order_by('-order_date')


class StockRepository(BaseRepository):
    """Repository for Stock model."""

    @classmethod
    def _get_model(cls):
        from .models import Stock
        return Stock

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered stock records."""
        from .models import Stock

        # Stock model doesn't have direct organization FK, filter through product
        queryset = Stock.objects.filter(product__organization=organization)

        if not filters:
            return queryset.select_related('product', 'product__organization', 'warehouse')

        # Filter by warehouse
        if 'warehouse_id' in filters and filters['warehouse_id']:
            queryset = queryset.filter(warehouse_id=filters['warehouse_id'])

        # Filter by product
        if 'product_id' in filters and filters['product_id']:
            queryset = queryset.filter(product_id=filters['product_id'])

        # Filter by category
        if 'category_id' in filters and filters['category_id']:
            queryset = queryset.filter(product__category_id=filters['category_id'])

        # Filter by low stock
        if 'low_stock' in filters and filters['low_stock']:
            queryset = queryset.filter(
                quantity__lte=F('product__minimum_stock')
            )

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(product__name__icontains=search_term) |
                Q(product__sku__icontains=search_term) |
                Q(warehouse__name__icontains=search_term)
            )

        return queryset.select_related(
            'product',
            'product__category',
            'product__organization',
            'warehouse'
        ).order_by('product__name')

    @classmethod
    def get_stock_summary_by_warehouse(cls, organization):
        """Get stock summary grouped by warehouse."""
        from .models import Stock

        return Stock.objects.filter(
            organization=organization
        ).values(
            'warehouse__id',
            'warehouse__name'
        ).annotate(
            total_products=Count('product', distinct=True),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__purchase_price'))
        )

    @classmethod
    def get_stock_summary_by_product(cls, organization):
        """Get stock summary grouped by product."""
        from .models import Stock

        return Stock.objects.filter(
            organization=organization
        ).values(
            'product__id',
            'product__name',
            'product__sku'
        ).annotate(
            total_warehouses=Count('warehouse', distinct=True),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('product__purchase_price'))
        )


class MovementRepository(BaseRepository):
    """Repository for Movement model."""

    @classmethod
    def _get_model(cls):
        from .models import Movement
        return Movement

    model = property(_get_model)

    @classmethod
    def get_filtered(cls, organization, filters=None):
        """Get filtered stock movements."""
        from .models import Movement

        queryset = Movement.objects.filter(organization=organization)

        if not filters:
            return queryset.select_related('product', 'warehouse', 'organization')

        # Filter by movement type
        if 'movement_type' in filters and filters['movement_type']:
            queryset = queryset.filter(movement_type=filters['movement_type'])

        # Filter by product
        if 'product_id' in filters and filters['product_id']:
            queryset = queryset.filter(product_id=filters['product_id'])

        # Filter by warehouse
        if 'warehouse_id' in filters and filters['warehouse_id']:
            queryset = queryset.filter(warehouse_id=filters['warehouse_id'])

        # Filter by date range
        if 'start_date' in filters and filters['start_date']:
            queryset = queryset.filter(movement_date__gte=filters['start_date'])

        if 'end_date' in filters and filters['end_date']:
            queryset = queryset.filter(movement_date__lte=filters['end_date'])

        # Search
        if 'search' in filters and filters['search']:
            search_term = filters['search']
            queryset = queryset.filter(
                Q(product__name__icontains=search_term) |
                Q(product__sku__icontains=search_term) |
                Q(reference__icontains=search_term) |
                Q(notes__icontains=search_term)
            )

        return queryset.select_related(
            'product',
            'warehouse',
            'organization'
        ).order_by('-movement_date')
