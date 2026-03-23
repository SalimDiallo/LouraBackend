"""
Professional PDF Generation for Sales Documents
==============================================

This module generates professional, print-ready PDFs for:
- Invoices (Factures)
- Proforma Invoices (Devis)
- Sale Receipts
- Payment Receipts

Design Principles:
- Clean, minimalist layout
- Professional typography
- Subtle use of color
- Clear hierarchy
- Print-friendly
"""

from io import BytesIO
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from decimal import Decimal
from django.utils import timezone
from django.conf import settings


def get_professional_styles():
    """
    Create a professional style sheet for PDF documents.
    Uses a modern, clean design with subtle colors.
    """
    styles = getSampleStyleSheet()

    # Main title - Large, bold, professional
    styles.add(ParagraphStyle(
        name='ProDocumentTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=3*mm,
        spaceBefore=0,
        leading=32
    ))

    # Section headers - Clean and organized
    styles.add(ParagraphStyle(
        name='ProSectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=4*mm,
        spaceBefore=6*mm,
        leading=14,
    ))

    # Body text - Readable and clean
    styles.add(ParagraphStyle(
        name='ProBodyText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica',
        alignment=TA_LEFT,
        leading=12,
        spaceAfter=2*mm,
    ))

    # Small text for metadata
    styles.add(ParagraphStyle(
        name='ProSmallText',
        parent=styles['Normal'],
        fontSize=7.5,
        textColor=colors.HexColor('#7f8c8d'),
        fontName='Helvetica',
        alignment=TA_CENTER,
        leading=10,
    ))

    # Right-aligned text
    styles.add(ParagraphStyle(
        name='ProRightAlign',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica',
        alignment=TA_RIGHT,
        leading=12,
    ))

    # Bold body text
    styles.add(ParagraphStyle(
        name='ProBodyTextBold',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#34495e'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        leading=12,
    ))

    return styles


def format_currency(amount, currency='GNF'):
    """Format currency with proper separators."""
    if amount is None:
        amount = 0
    try:
        amount = float(amount)
        # Format with space thousands separator
        formatted = f"{amount:,.0f}".replace(',', ' ')
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"0 {currency}"


def format_date(date_obj, with_time=False):
    """Format date in French format."""
    if not date_obj:
        return "N/A"
    try:
        if with_time:
            return date_obj.strftime("%d/%m/%Y %H:%M")
        return date_obj.strftime("%d/%m/%Y")
    except:
        return str(date_obj)


def create_company_header(org, doc_type="FACTURE"):
    """Create a professional company header section with optional logo."""
    styles = get_professional_styles()
    elements = []

    # Check if organization has a logo
    logo_img = None
    has_logo = False

    if org and hasattr(org, 'logo') and org.logo:
        # Try to use the uploaded logo file
        try:
            logo_path = org.logo.path if hasattr(org.logo, 'path') else None
            if logo_path and os.path.exists(logo_path):
                logo_img = Image(logo_path)
                has_logo = True
        except:
            pass

    # If no uploaded logo, try logo_url
    if not has_logo and org and hasattr(org, 'logo_url') and org.logo_url:
        try:
            logo_img = Image(org.logo_url)
            has_logo = True
        except:
            pass

    # If logo exists, create header with logo + title side by side
    if has_logo and logo_img:
        # Resize logo to reasonable size (max 3cm height, keep aspect ratio)
        max_height = 3*cm
        max_width = 4*cm

        # Get original dimensions
        img_width, img_height = logo_img.imageWidth, logo_img.imageHeight
        aspect = img_width / float(img_height)

        # Calculate new dimensions keeping aspect ratio
        if img_height > max_height:
            new_height = max_height
            new_width = new_height * aspect
        else:
            new_height = img_height
            new_width = img_width

        # Ensure width doesn't exceed max
        if new_width > max_width:
            new_width = max_width
            new_height = new_width / aspect

        logo_img.drawHeight = new_height
        logo_img.drawWidth = new_width

        # Create title paragraph
        title = Paragraph(doc_type, styles['ProDocumentTitle'])

        # Create table with logo and title
        header_table = Table([[logo_img, title]], colWidths=[new_width + 1*cm, None])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 2*mm))
    else:
        # No logo: standard layout with just the title
        title = Paragraph(doc_type, styles['ProDocumentTitle'])
        elements.append(title)
        elements.append(Spacer(1, 2*mm))

    # Thin separator line
    elements.append(HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor('#e0e0e0'),
        spaceBefore=0,
        spaceAfter=8*mm
    ))

    return elements


def create_info_section(org, document_info):
    """Create document and company information section."""
    styles = get_professional_styles()

    # Two-column layout: Company info | Document info
    company_text = f"""<b>{org.name if org else 'Votre Entreprise'}</b><br/>
{getattr(org, 'address', 'Adresse') or ''}<br/>
Tél: {getattr(org, 'phone', 'Téléphone') or ''}<br/>
Email: {getattr(org, 'email', 'Email') or ''}"""

    if hasattr(org, 'tax_id') and org.tax_id:
        company_text += f"<br/>NIF: {org.tax_id}"
    if hasattr(org, 'registry_number') and getattr(org, 'registry_number', None):
        company_text += f"<br/>RCCM: {org.registry_number}"

    company_para = Paragraph(company_text, styles['ProBodyText'])
    doc_para = Paragraph(document_info, styles['ProRightAlign'])

    info_table = Table([[company_para, doc_para]], colWidths=[9*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    return info_table


def create_client_section(client_data):
    """Create client information section."""
    styles = get_professional_styles()
    elements = []

    # Section header
    elements.append(Paragraph("FACTURER À", styles['ProSectionHeader']))

    # Client details in a clean box
    client_para = Paragraph(client_data, styles['ProBodyText'])

    client_table = Table([[client_para]], colWidths=[17*cm])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(client_table)
    elements.append(Spacer(1, 8*mm))

    return elements


def create_items_table(items_data, currency='GNF'):
    """Create a professional items table."""
    # Table data with headers
    table_data = [['DÉSIGNATION', 'QTÉ', 'PRIX UNITAIRE', 'REMISE', 'TOTAL']]

    for item in items_data:
        table_data.append([
            item['description'],
            str(item['quantity']),
            format_currency(item['unit_price'], currency),
            item['discount'] if item['discount'] != '-' else '-',
            format_currency(item['total'], currency)
        ])

    items_table = Table(table_data, colWidths=[7.5*cm, 2*cm, 3*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Body rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#34495e')),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),

        # Grid and padding
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    return items_table


def create_totals_section(totals_data, currency='GNF'):
    """Create totals section with professional styling."""
    totals_rows = []

    # Subtotal
    if 'subtotal' in totals_data:
        totals_rows.append(['Sous-total HT:', format_currency(totals_data['subtotal'], currency)])

    # Discount
    if 'discount' in totals_data and totals_data['discount'] > 0:
        totals_rows.append(['Remise:', f"- {format_currency(totals_data['discount'], currency)}"])

    # Tax
    if 'tax_rate' in totals_data and totals_data['tax'] > 0:
        totals_rows.append([f"TVA ({totals_data['tax_rate']}%):", format_currency(totals_data['tax'], currency)])

    # Total (prominent)
    totals_rows.append(['', ''])  # Spacer
    totals_rows.append(['TOTAL TTC:', format_currency(totals_data['total'], currency)])

    totals_table = Table(totals_rows, colWidths=[11*cm, 6*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -2), 9),
        ('TEXTCOLOR', (0, 0), (-1, -2), colors.HexColor('#34495e')),

        # Total row - prominent
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2c3e50')),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        ('LEFTPADDING', (0, -1), (-1, -1), 8),
        ('RIGHTPADDING', (0, -1), (-1, -1), 8),

        # Line above total
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#2c3e50')),
    ]))

    return totals_table


def create_footer(generation_date):
    """Create document footer."""
    styles = get_professional_styles()

    elements = []

    # Separator line
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor('#e0e0e0'),
        spaceBefore=0,
        spaceAfter=5*mm
    ))

    # Footer text
    footer_text = f"Document généré le {generation_date} | Valide sans signature"
    elements.append(Paragraph(footer_text, styles['ProSmallText']))

    return elements


def generate_invoice_pdf(sale):
    """Generate professional invoice PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = get_professional_styles()
    elements = []
    org = sale.organization
    currency = getattr(org, 'currency', 'GNF')

    # === HEADER ===
    elements.extend(create_company_header(org, "FACTURE"))

    # === DOCUMENT INFO ===
    status_color = '#27ae60' if sale.payment_status == 'paid' else '#e74c3c' if sale.payment_status == 'pending' else '#f39c12'

    doc_info = f"""<b>N° Facture:</b> {sale.sale_number}<br/>
<b>Date d'émission:</b> {format_date(sale.sale_date)}<br/>
<b>Statut:</b> <font color="{status_color}">{sale.get_payment_status_display()}</font>"""

    elements.append(create_info_section(org, doc_info))
    elements.append(Spacer(1, 8*mm))

    # === CLIENT INFO ===
    if sale.customer:
        client_data = f"""<b>{sale.customer.name}</b><br/>
{sale.customer.address or ''}<br/>
Tél: {sale.customer.phone or '-'} | Email: {sale.customer.email or '-'}"""
        if hasattr(sale.customer, 'tax_id') and sale.customer.tax_id:
            client_data += f"<br/>NIF: {sale.customer.tax_id}"
    else:
        client_data = "<b>Client anonyme</b>"

    elements.extend(create_client_section(client_data))

    # === ITEMS TABLE ===
    items_data = []
    for item in sale.items.all():
        discount_text = '-'
        if item.discount_value > 0:
            if item.discount_type == 'percentage':
                discount_text = f"-{item.discount_value}%"
            else:
                discount_text = f"-{format_currency(item.discount_value, currency)}"

        items_data.append({
            'description': item.product.name,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount': discount_text,
            'total': float(item.total)
        })

    elements.append(create_items_table(items_data, currency))
    elements.append(Spacer(1, 6*mm))

    # === TOTALS ===
    totals_data = {
        'subtotal': float(sale.subtotal),
        'discount': float(sale.discount_amount) if sale.discount_amount > 0 else 0,
        'tax_rate': float(sale.tax_rate) if sale.tax_rate > 0 else 0,
        'tax': float(sale.tax_amount) if sale.tax_amount > 0 else 0,
        'total': float(sale.total_amount)
    }

    elements.append(create_totals_section(totals_data, currency))
    elements.append(Spacer(1, 8*mm))

    # === PAYMENT INFO ===
    if sale.payments.exists() or sale.payment_status != 'paid':
        elements.append(Paragraph("INFORMATIONS DE PAIEMENT", styles['ProSectionHeader']))

        payment_info = [
            ['Montant payé:', format_currency(sale.paid_amount, currency)],
            ['Reste à payer:', format_currency(sale.get_remaining_amount(), currency)],
            ['Mode de paiement:', sale.get_payment_method_display()],
        ]

        payment_table = Table(payment_info, colWidths=[5*cm, 12*cm])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495e')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))

        elements.append(payment_table)
        elements.append(Spacer(1, 8*mm))

    # === NOTES ===
    if sale.notes:
        elements.append(Paragraph("NOTES", styles['ProSectionHeader']))
        notes_para = Paragraph(sale.notes.replace('\n', '<br/>'), styles['ProBodyText'])
        elements.append(notes_para)

    # === FOOTER ===
    elements.extend(create_footer(format_date(timezone.now(), with_time=True)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_proforma_pdf(proforma):
    """Generate professional proforma invoice PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = get_professional_styles()
    elements = []
    org = proforma.organization
    currency = getattr(org, 'currency', 'GNF')

    # === HEADER ===
    elements.extend(create_company_header(org, "DEVIS / PRO FORMA"))

    # === DOCUMENT INFO ===
    is_expired = proforma.validity_date and proforma.validity_date < timezone.now().date()
    status_color = '#e74c3c' if is_expired else '#27ae60' if proforma.status == 'accepted' else '#f39c12'

    doc_info = f"""<b>N° Devis:</b> {proforma.proforma_number}<br/>
<b>Date d'émission:</b> {format_date(proforma.issue_date)}<br/>
<b>Valable jusqu'au:</b> {format_date(proforma.validity_date)}<br/>
<b>Statut:</b> <font color="{status_color}">{proforma.get_status_display()}</font>"""

    elements.append(create_info_section(org, doc_info))
    elements.append(Spacer(1, 8*mm))

    # === CLIENT INFO ===
    if proforma.customer:
        client_data = f"""<b>{proforma.customer.name}</b><br/>
{proforma.customer.address or ''}<br/>
Tél: {proforma.customer.phone or '-'} | Email: {proforma.customer.email or '-'}"""
        if hasattr(proforma.customer, 'tax_id') and proforma.customer.tax_id:
            client_data += f"<br/>NIF: {proforma.customer.tax_id}"
    else:
        client_data = f"""<b>{proforma.client_name or 'Client'}</b><br/>
{proforma.client_address or ''}<br/>
Tél: {proforma.client_phone or '-'} | Email: {proforma.client_email or '-'}"""

    elements.extend(create_client_section(client_data))

    # === ITEMS TABLE ===
    items_data = []
    for item in proforma.items.all():
        items_data.append({
            'description': f"{item.product.name}\n{item.description or ''}",
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount': '-',
            'total': float(item.total)
        })

    elements.append(create_items_table(items_data, currency))
    elements.append(Spacer(1, 6*mm))

    # === TOTALS ===
    totals_data = {
        'subtotal': float(proforma.subtotal),
        'discount': float(proforma.discount_amount) if proforma.discount_amount > 0 else 0,
        'tax_rate': 0,
        'tax': float(proforma.tax_amount) if proforma.tax_amount > 0 else 0,
        'total': float(proforma.total_amount)
    }

    elements.append(create_totals_section(totals_data, currency))
    elements.append(Spacer(1, 10*mm))

    # === CONDITIONS ===
    elements.append(Paragraph("CONDITIONS GÉNÉRALES", styles['ProSectionHeader']))

    if proforma.conditions:
        conditions_para = Paragraph(proforma.conditions.replace('\n', '<br/>'), styles['ProBodyText'])
    else:
        default_conditions = f"""• Les prix sont exprimés en {currency} et valables jusqu'à la date indiquée.<br/>
• Un acompte de 30% pourra être demandé à la commande.<br/>
• Le solde est payable à la livraison ou selon accord préalable.<br/>
• Les délais de livraison sont donnés à titre indicatif.<br/>
• Toute commande implique l'acceptation de nos conditions générales de vente."""
        conditions_para = Paragraph(default_conditions, styles['ProBodyText'])

    conditions_table = Table([[conditions_para]], colWidths=[17*cm])
    conditions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(conditions_table)
    elements.append(Spacer(1, 10*mm))

    # === SIGNATURE SECTION ===
    signature_data = [
        ['Signature du client', 'Signature du fournisseur'],
        ['Date: ___/___/______', 'Date: ___/___/______'],
        ['', ''],
        ['', ''],
    ]

    signature_table = Table(signature_data, colWidths=[8.5*cm, 8.5*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495e')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#34495e')),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))

    elements.append(signature_table)

    # === FOOTER ===
    elements.extend(create_footer(format_date(timezone.now(), with_time=True)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_sale_receipt_pdf(sale):
    """Generate a simple sale receipt (lighter than invoice)."""
    # For receipts, use the same invoice template
    # but could be customized for a simpler layout
    return generate_invoice_pdf(sale)


def generate_payment_receipt_pdf(payment):
    """Generate payment receipt PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    styles = get_professional_styles()
    elements = []
    org = payment.organization
    currency = getattr(org, 'currency', 'GNF')

    # === HEADER ===
    elements.extend(create_company_header(org, "REÇU DE PAIEMENT"))

    # === DOCUMENT INFO ===
    doc_info = f"""<b>N° Reçu:</b> {payment.receipt_number}<br/>
<b>Date:</b> {format_date(payment.payment_date)}<br/>
<b>Méthode:</b> {payment.get_payment_method_display()}"""

    elements.append(create_info_section(org, doc_info))
    elements.append(Spacer(1, 10*mm))

    # === PAYMENT DETAILS ===
    elements.append(Paragraph("DÉTAILS DU PAIEMENT", styles['ProSectionHeader']))

    payment_details = [
        ['Montant payé:', format_currency(payment.amount, currency)],
        ['Client:', payment.customer_name or (payment.sale.customer.name if payment.sale and payment.sale.customer else 'N/A')],
        ['Téléphone:', payment.customer_phone or (payment.sale.customer.phone if payment.sale and payment.sale.customer else 'N/A')],
    ]

    if payment.sale:
        payment_details.append(['Vente N°:', payment.sale.sale_number])

    if payment.reference:
        payment_details.append(['Référence:', payment.reference])

    payment_table = Table(payment_details, colWidths=[5*cm, 12*cm])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#34495e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))

    elements.append(payment_table)

    # === NOTES ===
    if payment.notes:
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("NOTES", styles['ProSectionHeader']))
        notes_para = Paragraph(payment.notes.replace('\n', '<br/>'), styles['ProBodyText'])
        elements.append(notes_para)

    # === FOOTER ===
    elements.extend(create_footer(format_date(timezone.now(), with_time=True)))

    doc.build(elements)
    buffer.seek(0)
    return buffer
