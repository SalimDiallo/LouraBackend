"""
PDF Base Module - Unified PDF Generation System
================================================

This module provides a unified, reusable system for PDF generation across all apps.
It supports both download and inline preview modes.

Features:
- Automatic Content-Disposition handling (inline vs attachment)
- Query parameter support (?mode=preview or ?mode=download)
- Consistent error handling
- Type hints for better IDE support
- Reusable mixin for all ViewSets

Usage Example:
--------------
from inventory.pdf_base import PDFGeneratorMixin

class MyViewSet(PDFGeneratorMixin, viewsets.ModelViewSet):

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, organization_slug=None, pk=None):
        obj = self.get_object()
        from .pdf_generator import generate_my_pdf

        pdf_buffer = generate_my_pdf(obj)
        filename = f"Document_{obj.number}.pdf"

        return self.pdf_response(
            pdf_buffer=pdf_buffer,
            filename=filename,
            request=request
        )
"""

from io import BytesIO
from typing import Optional, Union
from django.http import HttpResponse, HttpRequest


class PDFGeneratorMixin:
    """
    Mixin to add unified PDF generation capabilities to ViewSets.

    This mixin provides a standard way to return PDF responses with support
    for both download and inline preview modes.
    """

    def pdf_response(
        self,
        pdf_buffer: BytesIO,
        filename: str,
        request: Optional[HttpRequest] = None,
        default_mode: str = 'download'
    ) -> HttpResponse:
        """
        Generate a standardized PDF HTTP response with preview support.

        Args:
            pdf_buffer: BytesIO buffer containing the generated PDF
            filename: Name of the PDF file (e.g., "invoice_001.pdf")
            request: Optional Django request object to check query parameters
            default_mode: Default mode if not specified ('download' or 'preview')

        Returns:
            HttpResponse with appropriate Content-Disposition header

        Query Parameters:
            ?mode=preview - Opens PDF inline in browser (for preview modal)
            ?mode=download - Downloads PDF as attachment (default)

        Examples:
            # Download mode (default)
            GET /api/inventory/sales/123/export-pdf/

            # Preview mode
            GET /api/inventory/sales/123/export-pdf/?mode=preview
        """
        # Determine the mode from query parameters
        mode = default_mode
        if request:
            mode = request.query_params.get('mode', default_mode)

        # Validate mode
        if mode not in ['preview', 'download']:
            mode = default_mode

        # Create HTTP response with PDF content
        response = HttpResponse(
            pdf_buffer.getvalue(),
            content_type='application/pdf'
        )

        # Set Content-Disposition based on mode
        if mode == 'preview':
            # Inline: Opens in browser for preview
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        else:
            # Attachment: Forces download
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Add additional PDF-specific headers
        response['X-PDF-Filename'] = filename
        response['X-PDF-Mode'] = mode

        # Cache control for PDFs
        response['Cache-Control'] = 'private, max-age=300'  # 5 minutes cache

        return response

    def generate_and_respond(
        self,
        generator_func: callable,
        generator_args: tuple = (),
        generator_kwargs: dict = None,
        filename: str = "document.pdf",
        request: Optional[HttpRequest] = None,
        default_mode: str = 'download'
    ) -> HttpResponse:
        """
        Convenience method to generate PDF and return response in one call.

        Args:
            generator_func: PDF generator function (e.g., generate_invoice_pdf)
            generator_args: Positional arguments for generator function
            generator_kwargs: Keyword arguments for generator function
            filename: Name of the PDF file
            request: Django request object
            default_mode: Default mode if not specified

        Returns:
            HttpResponse with PDF content

        Example:
            return self.generate_and_respond(
                generator_func=generate_invoice_pdf,
                generator_args=(sale,),
                filename=f"Invoice_{sale.sale_number}.pdf",
                request=request
            )
        """
        if generator_kwargs is None:
            generator_kwargs = {}

        # Call the generator function
        pdf_buffer = generator_func(*generator_args, **generator_kwargs)

        # Return standardized response
        return self.pdf_response(
            pdf_buffer=pdf_buffer,
            filename=filename,
            request=request,
            default_mode=default_mode
        )


class PDFResponseHelper:
    """
    Static helper class for PDF responses outside of ViewSets.

    Use this when you need PDF response functionality but aren't using
    the PDFGeneratorMixin (e.g., in function-based views).
    """

    @staticmethod
    def create_response(
        pdf_buffer: BytesIO,
        filename: str,
        mode: str = 'download'
    ) -> HttpResponse:
        """
        Create a PDF HTTP response.
        Args:
            pdf_buffer: BytesIO buffer containing PDF
            filename: Name of the PDF file
            mode: 'preview' or 'download'

        Returns:
            HttpResponse with PDF content
        """
        response = HttpResponse(
            pdf_buffer.getvalue(),
            content_type='application/pdf'
        )

        if mode == 'preview':
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        else:
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

        response['X-PDF-Filename'] = filename
        response['X-PDF-Mode'] = mode
        response['Cache-Control'] = 'private, max-age=300'

        return response


# ==========================================
# USAGE EXAMPLES
# ==========================================

"""
Example 1: Using the Mixin in a ViewSet
----------------------------------------

from rest_framework import viewsets
from rest_framework.decorators import action
from inventory.pdf_base import PDFGeneratorMixin

class SaleViewSet(PDFGeneratorMixin, viewsets.ModelViewSet):
    # ... other ViewSet code ...

    @action(detail=True, methods=['get'], url_path='receipt')
    def generate_receipt(self, request, organization_slug=None, pk=None):
        '''Generate receipt PDF for a sale'''
        sale = self.get_object()
        from .pdf_sales import generate_sale_receipt_pdf

        pdf_buffer = generate_sale_receipt_pdf(sale)
        filename = f"Recu_{sale.sale_number}.pdf"

        # Unified response with preview support
        return self.pdf_response(
            pdf_buffer=pdf_buffer,
            filename=filename,
            request=request
        )


Example 2: Using the generate_and_respond shortcut
--------------------------------------------------

    @action(detail=True, methods=['get'], url_path='invoice')
    def generate_invoice(self, request, organization_slug=None, pk=None):
        '''Generate invoice PDF for a sale'''
        sale = self.get_object()
        from .pdf_sales import generate_invoice_pdf

        # One-liner with automatic PDF generation and response
        return self.generate_and_respond(
            generator_func=generate_invoice_pdf,
            generator_args=(sale,),
            filename=f"Facture_{sale.sale_number}.pdf",
            request=request
        )


Example 3: Using PDFResponseHelper in function-based views
----------------------------------------------------------

from django.http import HttpRequest
from inventory.pdf_base import PDFResponseHelper

def my_view(request: HttpRequest, pk: int):
    # ... generate PDF ...
    pdf_buffer = generate_some_pdf()

    mode = request.GET.get('mode', 'download')
    return PDFResponseHelper.create_response(
        pdf_buffer=pdf_buffer,
        filename="document.pdf",
        mode=mode
    )


Example 4: Frontend API Calls
------------------------------

// Download mode (default behavior)
fetch('/api/inventory/sales/123/receipt/')
  → Downloads PDF file

// Preview mode (for modal display)
fetch('/api/inventory/sales/123/receipt/?mode=preview')
  → Returns PDF with inline disposition for browser preview


Example 5: Using with React usePDF hook
---------------------------------------

import { usePDF } from '@/lib/hooks';

const MyComponent = () => {
  const { preview, download } = usePDF();

  // Preview in modal
  const handlePreview = () => {
    preview(
      '/api/inventory/sales/123/receipt/',  // URL
      'Reçu de Vente',                       // Title
      'recu_VTE-001.pdf'                     // Filename
    );
  };

  // Direct download
  const handleDownload = () => {
    download(
      '/api/inventory/sales/123/receipt/',  // URL
      'recu_VTE-001.pdf'                     // Filename
    );
  };

  return (
    <>
      <button onClick={handlePreview}>Prévisualiser</button>
      <button onClick={handleDownload}>Télécharger</button>
    </>
  );
};

Note: The frontend PDFService automatically adds ?mode=preview when using
the preview() method, so the backend will return the correct response.
"""
