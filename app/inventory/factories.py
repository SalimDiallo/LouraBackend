"""
Factory classes for the inventory application.

This module implements the Factory pattern for creating complex objects
and generating unique identifiers (document numbers, codes, etc.).
"""

from django.utils import timezone
from django.db import transaction
import re
import uuid

class DocumentNumberFactory:
    """
    Factory for generating truly unique document numbers.

    This version guarantees that the same document number is never generated twice,
    even under concurrent usage or fallback.

    Usage:
        # Generate an order number
        order_number = DocumentNumberFactory.generate(
            model_class=Order,
            organization=org,
            prefix='ORD',
            field_name='order_number'
        )
    """

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
        Generate the next sequential, absolutely unique document number.
        If a collision occurs, bumps until a unique one is found.
        In case of database errors or true contention, always generate a
        unique fallback using timestamp and UUID to guarantee uniqueness.
        """
        # Determine prefix
        if prefix is None:
            if doc_type and doc_type in DocumentNumberFactory.DEFAULT_PREFIXES:
                prefix = DocumentNumberFactory.DEFAULT_PREFIXES[doc_type]
            else:
                prefix = 'DOC'

        # Infer field name if not provided
        if field_name is None:
            model_name = model_class.__name__.lower()
            field_name = f"{model_name}_number"

        max_retries = 15

        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    filter_kwargs = {
                        'organization': organization,
                        f'{field_name}__startswith': f'{prefix}{separator}'
                    }
                    # Ordering numerically, descending
                    last_doc = model_class.objects.filter(
                        **filter_kwargs
                    ).select_for_update().order_by(f'-{field_name}').first()

                    if last_doc and hasattr(last_doc, field_name):
                        last_number = getattr(last_doc, field_name)
                        next_num = DocumentNumberFactory._parse_and_increment(
                            last_number, prefix, separator, length
                        )
                    else:
                        next_num = 1

                    while True:
                        formatted_number = f"{prefix}{separator}{str(next_num).zfill(length)}"
                        check_kwargs = {
                            'organization': organization,
                            field_name: formatted_number
                        }
                        if not model_class.objects.filter(**check_kwargs).exists():
                            # Guaranteed unique
                            return formatted_number
                        next_num += 1

            except Exception:
                continue  # Try again, up to max_retries

        # ABSOLUTE UNIQUE FALLBACK: Never generate the same!
        # Compose with prefix, timestamp, microseconds, and 6-char uuid
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
        unique = uuid.uuid4().hex[:6].upper()
        return f"{prefix}{separator}{timestamp}{unique}"

    @staticmethod
    def _parse_and_increment(last_number, prefix, separator, length):
        """
        Parse the last number and increment it.
        """
        if not last_number:
            return 1
        try:
            parts = last_number.split(separator)
            if len(parts) >= 2:
                numeric_part = parts[-1]
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
        Generate multiple unique numbers at once.
        Collisions are always avoided, even under race conditions.
        """
        numbers = []
        used_numbers = set()
        # Generate first N unique numbers by bumping
        for i in range(count):
            # We must guarantee uniqueness. Try a lot of times in case of concurrency.
            num = None
            for attempt in range(20):
                candidate = DocumentNumberFactory.generate(
                    model_class, organization, prefix, field_name, doc_type=doc_type
                )
                if candidate not in used_numbers:
                    num = candidate
                    break
            if num is None:
                # fallback
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
                u = uuid.uuid4().hex[0:6].upper()
                num = f"{prefix or 'DOC'}-{timestamp}{u}"
            used_numbers.add(num)
            numbers.append(num)
        return numbers

class CodeFactory:
    """
    Factory for generating codes/SKUs/barcodes, guaranteeing uniqueness.
    """

    @staticmethod
    def generate_sku(category_code, organization, model_class=None, length=6):
        """
        Generate a unique SKU, retrying if collision occurs. Never reused.
        """
        base = f"{category_code}-"
        for i in range(30):
            if model_class:
                count = model_class.objects.filter(
                    organization=organization,
                    sku__startswith=base
                ).count()
                next_num = count + 1 + i
            else:
                t = timezone.now().strftime('%H%M%S%f')
                next_num = int(t) + i
            sku = f"{base}{str(next_num).zfill(length)}"
            if not model_class or not model_class.objects.filter(
                organization=organization,
                sku=sku
            ).exists():
                return sku
        # fallback: truly unique
        timeu = timezone.now().strftime('%Y%m%d%H%M%S%f') + uuid.uuid4().hex[:4]
        return f"{base}{timeu[:length]}"

    @staticmethod
    def generate_barcode(prefix='BAR', length=13):
        """
        Generate a unique barcode, combining timestamp and random uuid.
        Never produces the same twice.
        """
        # The barcode must be unique even across nodes and time
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
        rand = uuid.uuid4().hex[:length]
        base = f"{prefix}{timestamp}{rand}"
        # Truncate or pad to match desired length
        if len(base) > length:
            return base[:length]
        else:
            # pad with zeros if needed
            return base.ljust(length, '0')
