"""
Base serializers and mixins for the inventory application.

This module provides reusable serializer components to reduce code duplication
and ensure consistent behavior across all inventory serializers.
"""

from rest_framework import serializers


class UUIDSerializerMixin:
    """
    Mixin to automatically convert UUID fields to string representation.

    This eliminates the need to manually define get_id(), get_organization(), etc.
    methods in every serializer.

    Usage:
        class ProductSerializer(UUIDSerializerMixin, serializers.ModelSerializer):
            id = serializers.SerializerMethodField()
            organization = serializers.SerializerMethodField()

            class Meta:
                model = Product
                fields = ['id', 'organization', 'name', ...]
    """

    def get_id(self, obj):
        """Convert UUID id to string."""
        return str(obj.id) if obj.id else None

    def get_organization(self, obj):
        """Convert organization UUID to string."""
        try:
            return str(obj.organization.id) if obj.organization else None
        except AttributeError:
            return None

    def get_product(self, obj):
        """Convert product UUID to string."""
        try:
            return str(obj.product.id) if obj.product else None
        except AttributeError:
            return None

    def get_warehouse(self, obj):
        """Convert warehouse UUID to string."""
        try:
            return str(obj.warehouse.id) if obj.warehouse else None
        except AttributeError:
            return None

    def get_category(self, obj):
        """Convert category UUID to string."""
        try:
            return str(obj.category.id) if obj.category else None
        except AttributeError:
            return None

    def get_supplier(self, obj):
        """Convert supplier UUID to string."""
        try:
            return str(obj.supplier.id) if obj.supplier else None
        except AttributeError:
            return None

    def get_customer(self, obj):
        """Convert customer UUID to string."""
        try:
            return str(obj.customer.id) if obj.customer else None
        except AttributeError:
            return None

    def get_order(self, obj):
        """Convert order UUID to string."""
        try:
            return str(obj.order.id) if obj.order else None
        except AttributeError:
            return None

    def get_sale(self, obj):
        """Convert sale UUID to string."""
        try:
            return str(obj.sale.id) if obj.sale else None
        except AttributeError:
            return None

    def get_movement(self, obj):
        """Convert movement UUID to string."""
        try:
            return str(obj.movement.id) if obj.movement else None
        except AttributeError:
            return None

    def get_parent(self, obj):
        """Convert parent UUID to string."""
        try:
            return str(obj.parent.id) if obj.parent else None
        except AttributeError:
            return None

    def get_user(self, obj):
        """Convert user UUID to string."""
        try:
            return str(obj.user.id) if obj.user else None
        except AttributeError:
            return None

    def get_created_by(self, obj):
        """Convert created_by user UUID to string."""
        try:
            return str(obj.created_by.id) if obj.created_by else None
        except AttributeError:
            return None

    def get_updated_by(self, obj):
        """Convert updated_by user UUID to string."""
        try:
            return str(obj.updated_by.id) if obj.updated_by else None
        except AttributeError:
            return None


class RelatedNameSerializerMixin:
    """
    Mixin to get name/title from related objects.

    Useful for displaying human-readable names in list views.
    """

    def get_organization_name(self, obj):
        """Get organization name."""
        try:
            return obj.organization.name if obj.organization else None
        except AttributeError:
            return None

    def get_product_name(self, obj):
        """Get product name."""
        try:
            return obj.product.name if obj.product else None
        except AttributeError:
            return None

    def get_warehouse_name(self, obj):
        """Get warehouse name."""
        try:
            return obj.warehouse.name if obj.warehouse else None
        except AttributeError:
            return None

    def get_category_name(self, obj):
        """Get category name."""
        try:
            return obj.category.name if obj.category else None
        except AttributeError:
            return None

    def get_supplier_name(self, obj):
        """Get supplier name."""
        try:
            return obj.supplier.name if obj.supplier else None
        except AttributeError:
            return None

    def get_customer_name(self, obj):
        """Get customer name."""
        try:
            return obj.customer.name if obj.customer else None
        except AttributeError:
            return None

    def get_parent_name(self, obj):
        """Get parent name."""
        try:
            return obj.parent.name if obj.parent else None
        except AttributeError:
            return None


class InventoryBaseSerializer(UUIDSerializerMixin, serializers.ModelSerializer):
    """
    Base serializer for all inventory models.

    Provides automatic UUID-to-string conversion for common fields.
    All inventory serializers should inherit from this class.

    Features:
    - Automatic UUID conversion for id, organization, and common foreign keys
    - Consistent error handling
    - Common validation patterns

    Example:
        class ProductSerializer(InventoryBaseSerializer):
            class Meta:
                model = Product
                fields = ['id', 'organization', 'name', 'sku', 'price']
                # id and organization are automatically converted to strings
    """

    class Meta:
        abstract = True


class InventoryListSerializer(UUIDSerializerMixin, RelatedNameSerializerMixin, serializers.ModelSerializer):
    """
    Base serializer for list views in inventory.

    Includes both UUID conversion and related object names for better UX.

    Example:
        class ProductListSerializer(InventoryListSerializer):
            category_name = serializers.SerializerMethodField()

            class Meta:
                model = Product
                fields = ['id', 'name', 'sku', 'category', 'category_name']
    """

    class Meta:
        abstract = True
