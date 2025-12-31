"""
Factory classes for the inventory application.

This module implements the Factory pattern for creating complex objects
and generating unique identifiers (document numbers, codes, etc.).
"""

from django.utils import timezone
from django.db import transaction
import re


class DocumentNumberFactory:
    """
    Factory for generating sequential document numbers.

    This eliminates the need for duplicate number generation logic across
    orders, sales, payments, proformas, etc.

    Usage:
        # Generate an order number
        order_number = DocumentNumberFactory.generate(
            model_class=Order,
            organization=org,
            prefix='ORD',
            field_name='order_number'
        )

    Features:
    - Thread-safe number generation
    - Automatic sequential numbering
    - Customizable prefixes
    - Fallback to timestamp-based numbers
    """

    # Default prefixes for common document types
    DEFAULT_PREFIXES = {
        'order': 'CMN',
        'sale': 'VTE',
        'payment': 'REC',
        'proforma': 'PF',
        'invoice': 'INV',
        'purchase_order': 'BC',
        'delivery': 'BL',
        'expense': 'DEP',
        'quote': 'DEV',
        'receipt': 'REC',
        'credit_note': 'CN',
        'debit_note': 'DN',
    }

    @staticmethod
    def generate(model_class, organization, prefix=None, field_name=None,
                 length=6, separator='-', doc_type=None):
        """
        Generate the next sequential document number.

        Args:
            model_class: The Django model class (e.g., Order, Sale)
            organization: The organization instance
            prefix: Custom prefix (e.g., 'ORD'). If None, uses doc_type to lookup default
            field_name: Name of the field containing the number (e.g., 'order_number')
            length: Number of digits in the sequential part (default: 6)
            separator: Separator between prefix and number (default: '-')
            doc_type: Document type key for default prefix lookup (e.g., 'order', 'sale')

        Returns:
            str: The generated document number (e.g., 'ORD-000042')

        Examples:
            >>> DocumentNumberFactory.generate(Order, org, prefix='ORD', field_name='order_number')
            'ORD-000001'

            >>> DocumentNumberFactory.generate(Sale, org, doc_type='sale', field_name='sale_number')
            'VTE-000015'
        """
        # Determine prefix
        if prefix is None:
            if doc_type and doc_type in DocumentNumberFactory.DEFAULT_PREFIXES:
                prefix = DocumentNumberFactory.DEFAULT_PREFIXES[doc_type]
            else:
                prefix = 'DOC'

        # Infer field name if not provided
        if field_name is None:
            # Try common patterns: order_number, sale_number, etc.
            model_name = model_class.__name__.lower()
            field_name = f"{model_name}_number"

        max_retries = 10
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Get the last document for this organization by field value
                    filter_kwargs = {
                        'organization': organization,
                        f'{field_name}__startswith': f'{prefix}{separator}'
                    }
                    
                    last_doc = model_class.objects.filter(
                        **filter_kwargs
                    ).select_for_update().order_by(f'-{field_name}').first()

                    if last_doc and hasattr(last_doc, field_name):
                        last_number = getattr(last_doc, field_name)

                        # Try to parse the existing number
                        next_num = DocumentNumberFactory._parse_and_increment(
                            last_number, prefix, separator, length
                        )
                    else:
                        # First document
                        next_num = 1

                    # Format the number
                    formatted_number = f"{prefix}{separator}{str(next_num).zfill(length)}"
                    
                    # Verify uniqueness before returning
                    check_kwargs = {
                        'organization': organization,
                        field_name: formatted_number
                    }
                    if model_class.objects.filter(**check_kwargs).exists():
                        # Number already exists, increment and try again
                        next_num += 1
                        formatted_number = f"{prefix}{separator}{str(next_num).zfill(length)}"
                        # Check again
                        check_kwargs[field_name] = formatted_number
                        while model_class.objects.filter(**check_kwargs).exists():
                            next_num += 1
                            formatted_number = f"{prefix}{separator}{str(next_num).zfill(length)}"
                            check_kwargs[field_name] = formatted_number
                    
                    return formatted_number

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt, fallback to timestamp-based number
                    import uuid
                    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                    unique_suffix = str(uuid.uuid4())[:4].upper()
                    return f"{prefix}{separator}{timestamp}{unique_suffix}"
                continue
        
        # Absolute fallback
        import uuid
        return f"{prefix}{separator}{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _parse_and_increment(last_number, prefix, separator, length):
        """
        Parse the last number and increment it.

        Args:
            last_number: The last generated number (e.g., 'ORD-000042')
            prefix: Expected prefix
            separator: Expected separator
            length: Expected length

        Returns:
            int: The next sequential number
        """
        if not last_number:
            return 1

        try:
            # Remove prefix and separator
            parts = last_number.split(separator)
            if len(parts) >= 2:
                numeric_part = parts[-1]
                # Extract digits
                number = int(re.sub(r'\D', '', numeric_part))
                return number + 1
            else:
                return 1
        except (ValueError, AttributeError, IndexError):
            return 1

    @staticmethod
    def generate_batch(model_class, organization, count, prefix=None,
                      field_name=None, doc_type=None):
        """
        Generate multiple sequential numbers at once.

        Useful for bulk operations.

        Args:
            model_class: The Django model class
            organization: The organization instance
            count: Number of sequential numbers to generate
            prefix: Custom prefix
            field_name: Field name containing the number
            doc_type: Document type for default prefix

        Returns:
            list: List of generated numbers

        Example:
            >>> numbers = DocumentNumberFactory.generate_batch(Order, org, 5, doc_type='order')
            ['ORD-000001', 'ORD-000002', 'ORD-000003', 'ORD-000004', 'ORD-000005']
        """
        numbers = []

        # Generate first number
        first_number = DocumentNumberFactory.generate(
            model_class, organization, prefix, field_name, doc_type=doc_type
        )
        numbers.append(first_number)

        # Determine prefix and separator
        if prefix is None:
            if doc_type and doc_type in DocumentNumberFactory.DEFAULT_PREFIXES:
                prefix = DocumentNumberFactory.DEFAULT_PREFIXES[doc_type]
            else:
                prefix = 'DOC'

        separator = '-'
        length = 6

        # Parse the first number to get the starting point
        try:
            parts = first_number.split(separator)
            if len(parts) >= 2:
                current_num = int(re.sub(r'\D', '', parts[-1]))
            else:
                current_num = 1
        except:
            current_num = 1

        # Generate remaining numbers
        for i in range(1, count):
            next_num = current_num + i
            formatted_number = f"{prefix}{separator}{str(next_num).zfill(length)}"
            numbers.append(formatted_number)

        return numbers


class CodeFactory:
    """
    Factory for generating unique codes (SKU, internal codes, etc.).

    Usage:
        # Generate a product SKU
        sku = CodeFactory.generate_sku(
            category_code='ELC',
            organization=org,
            model_class=Product
        )
    """

    @staticmethod
    def generate_sku(category_code, organization, model_class=None, length=6):
        """
        Generate a unique SKU (Stock Keeping Unit).

        Args:
            category_code: Category code (e.g., 'ELC' for electronics)
            organization: Organization instance
            model_class: Product model class (for uniqueness check)
            length: Length of the numeric part

        Returns:
            str: Generated SKU (e.g., 'ELC-000142')
        """
        if model_class:
            # Count existing products in this category
            count = model_class.objects.filter(
                organization=organization,
                sku__startswith=f"{category_code}-"
            ).count()
            next_num = count + 1
        else:
            # Use timestamp
            next_num = int(timezone.now().strftime('%H%M%S'))

        return f"{category_code}-{str(next_num).zfill(length)}"

    @staticmethod
    def generate_barcode(prefix='BAR', length=13):
        """
        Generate a unique barcode.

        Args:
            prefix: Barcode prefix
            length: Total length of barcode

        Returns:
            str: Generated barcode
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        # Take last N digits to fit the length
        numeric_part = timestamp[-(length - len(prefix)):]
        return f"{prefix}{numeric_part}"
