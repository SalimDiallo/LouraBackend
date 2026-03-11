"""
Filter utilities for the inventory application.

This module provides utilities to extract and parse query parameters
from API requests, eliminating repetitive filter extraction logic.
"""

from datetime import datetime
from django.utils.dateparse import parse_date, parse_datetime


class QueryFilterExtractor:
    """
    Extract and parse filter parameters from Django request query params.

    This eliminates the need to manually extract and convert query parameters
    in every ViewSet's get_queryset() method.

    Usage:
        def get_queryset(self):
            organization = self.get_organization_from_request()
            extractor = QueryFilterExtractor(self.request.query_params)
            filters = extractor.extract_common_filters()
            return ProductRepository.get_filtered(organization, filters)
    """

    def __init__(self, query_params):
        """
        Initialize with request query parameters.

        Args:
            query_params: request.query_params from DRF request
        """
        self.params = query_params

    def get_string(self, key, default=None):
        """Get string parameter."""
        return self.params.get(key, default)

    def get_int(self, key, default=None):
        """Get integer parameter."""
        value = self.params.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key, default=None):
        """Get float parameter."""
        value = self.params.get(key)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key, default=None):
        """
        Get boolean parameter.

        Accepts: 'true', 'True', '1', 'yes' as True
                 'false', 'False', '0', 'no' as False
        """
        value = self.params.get(key)
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')

        return default

    def get_date(self, key, default=None):
        """Get date parameter (parses ISO format)."""
        value = self.params.get(key)
        if value is None:
            return default
        try:
            return parse_date(value)
        except (ValueError, TypeError):
            return default

    def get_datetime(self, key, default=None):
        """Get datetime parameter (parses ISO format)."""
        value = self.params.get(key)
        if value is None:
            return default
        try:
            return parse_datetime(value)
        except (ValueError, TypeError):
            return default

    def get_uuid(self, key, default=None):
        """Get UUID parameter."""
        value = self.params.get(key)
        if value is None:
            return default
        # UUID validation happens at the database level
        return value

    def get_list(self, key, separator=',', default=None):
        """
        Get list parameter (comma-separated by default).

        Args:
            key: Parameter name
            separator: List separator (default: comma)
            default: Default value if not found

        Returns:
            list or default

        Example:
            ?categories=1,2,3 -> ['1', '2', '3']
        """
        value = self.params.get(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]

    def extract_common_filters(self):
        """
        Extract common filter parameters used across most models.

        Returns:
            dict: Dictionary of filter parameters
        """
        return {
            'is_active': self.get_bool('is_active'),
            'search': self.get_string('search'),
            'ordering': self.get_string('ordering'),
        }

    def extract_category_filters(self):
        """Extract filters specific to Category model."""
        filters = self.extract_common_filters()
        filters.update({
            'parent_id': self.get_uuid('parent'),
        })
        return filters

    def extract_warehouse_filters(self):
        """Extract filters specific to Warehouse model."""
        filters = self.extract_common_filters()
        filters.update({
            'city': self.get_string('city'),
            'country': self.get_string('country'),
        })
        return filters

    def extract_supplier_filters(self):
        """Extract filters specific to Supplier model."""
        filters = self.extract_common_filters()
        filters.update({
            'city': self.get_string('city'),
            'country': self.get_string('country'),
        })
        return filters

    def extract_product_filters(self):
        """Extract filters specific to Product model."""
        filters = self.extract_common_filters()
        filters.update({
            'category_id': self.get_uuid('category'),
            'product_type': self.get_string('product_type'),
            'in_stock': self.get_bool('in_stock'),
            'min_price': self.get_float('min_price'),
            'max_price': self.get_float('max_price'),
        })
        return filters

    def extract_order_filters(self):
        """Extract filters specific to Order model."""
        filters = self.extract_common_filters()
        filters.update({
            'status': self.get_string('status'),
            'supplier_id': self.get_uuid('supplier'),
            'warehouse_id': self.get_uuid('warehouse'),
            'start_date': self.get_date('start_date'),
            'end_date': self.get_date('end_date'),
        })
        return filters

    def extract_stock_filters(self):
        """Extract filters specific to Stock model."""
        filters = self.extract_common_filters()
        filters.update({
            'warehouse_id': self.get_uuid('warehouse'),
            'product_id': self.get_uuid('product'),
            'category_id': self.get_uuid('category'),
            'low_stock': self.get_bool('low_stock'),
        })
        return filters

    def extract_movement_filters(self):
        """Extract filters specific to Movement model."""
        filters = self.extract_common_filters()
        filters.update({
            'movement_type': self.get_string('movement_type'),
            'product_id': self.get_uuid('product'),
            'warehouse_id': self.get_uuid('warehouse'),
            'start_date': self.get_date('start_date'),
            'end_date': self.get_date('end_date'),
        })
        return filters

    def extract_sale_filters(self):
        """Extract filters specific to Sale model."""
        filters = self.extract_common_filters()
        filters.update({
            'status': self.get_string('status'),
            'customer_id': self.get_uuid('customer'),
            'payment_status': self.get_string('payment_status'),
            'start_date': self.get_date('start_date'),
            'end_date': self.get_date('end_date'),
        })
        return filters

    def extract_customer_filters(self):
        """Extract filters specific to Customer model."""
        filters = self.extract_common_filters()
        filters.update({
            'city': self.get_string('city'),
            'country': self.get_string('country'),
            'customer_type': self.get_string('customer_type'),
        })
        return filters

    def extract_pagination(self):
        """
        Extract pagination parameters.

        Returns:
            dict: Dictionary with page and page_size
        """
        return {
            'page': self.get_int('page', 1),
            'page_size': self.get_int('page_size', 20),
        }

    def has_param(self, key):
        """Check if a parameter exists in the query string."""
        return key in self.params

    def get_all_params(self):
        """Get all query parameters as a dictionary."""
        return dict(self.params)


class FilterHelper:
    """
    Static helper methods for common filtering operations.
    """

    @staticmethod
    def apply_ordering(queryset, ordering_param):
        """
        Apply ordering to queryset.

        Args:
            queryset: Django QuerySet
            ordering_param: Ordering string (e.g., 'name', '-created_at')

        Returns:
            Ordered QuerySet
        """
        if not ordering_param:
            return queryset

        # Validate ordering field (prevent SQL injection)
        allowed_fields = [
            'name', 'created_at', 'updated_at', 'code', 'price',
            'quantity', 'status', 'date', 'total', 'order_date',
            'sale_date', 'movement_date'
        ]

        # Remove '-' prefix for validation
        field = ordering_param.lstrip('-')

        if field in allowed_fields:
            return queryset.order_by(ordering_param)
        else:
            # Default ordering if invalid field
            return queryset

    @staticmethod
    def build_search_query(search_term, fields):
        """
        Build a Q object for searching across multiple fields.

        Args:
            search_term: Search string
            fields: List of field names to search

        Returns:
            Q object
        """
        from django.db.models import Q

        if not search_term or not fields:
            return Q()

        query = Q()
        for field in fields:
            query |= Q(**{f"{field}__icontains": search_term})

        return query

    @staticmethod
    def parse_date_range(start_date_str, end_date_str):
        """
        Parse and validate date range strings.

        Args:
            start_date_str: Start date string (ISO format)
            end_date_str: End date string (ISO format)

        Returns:
            tuple: (start_date, end_date) or (None, None)
        """
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        # Validate range
        if start_date and end_date and start_date > end_date:
            return None, None

        return start_date, end_date
