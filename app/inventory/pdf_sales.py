"""
PDF Generation for Sales & Commercial Documents

Ce module contient les fonctions de génération PDF pour :
- Reçus de vente
- Reçus de paiement
- Factures pro forma
- Bons de commande
- Bons de livraison
- Export des dépenses
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from decimal import Decimal


def get_styles():
    """Get standard styles for PDF documents"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#37474f'),
        spaceBefore=15,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='BodyTextRight',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='BodyTextCenter',
        parent=styles['Normal'],
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    ))
    
    return styles


def format_currency(amount, currency="GNF"):
    """Format amount as currency"""
    if amount is None:
        amount = Decimal('0.00')
    return f"{amount:,.0f} {currency}"


def format_date(date_obj, with_time=False):
    """Format date for display"""
    if date_obj is None:
        return "-"
    if with_time:
        return date_obj.strftime("%d/%m/%Y %H:%M")
    return date_obj.strftime("%d/%m/%Y")


def get_organization_header(organization):
    """Generate organization header data"""
    return [
        organization.name if organization else "LouraTech",
        f"Tél: {getattr(organization, 'phone', 'N/A')}",
        f"Email: {getattr(organization, 'email', 'N/A')}",
        f"Adresse: {getattr(organization, 'address', 'N/A')}"
    ]


def generate_sale_receipt_pdf(sale):
    """Generate PDF receipt for a sale"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("REÇU DE VENTE", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Sale info
    info_data = [
        ["N° de vente:", sale.sale_number],
        ["Date:", format_date(sale.sale_date, with_time=True)],
        ["Mode de paiement:", sale.get_payment_method_display()],
        ["Statut:", sale.get_payment_status_display()],
    ]
    
    if sale.customer:
        info_data.extend([
            ["Client:", sale.customer.name],
            ["Téléphone:", sale.customer.phone or "-"],
        ])
    
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))
    
    # Items table
    elements.append(Paragraph("Détails des produits", styles['SectionHeader']))
    
    items_data = [["Produit", "Qté", "Prix unit.", "Remise", "Total"]]
    
    for item in sale.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.discount_amount) if item.discount_amount > 0 else "-",
            format_currency(item.total)
        ])
    
    items_table = Table(items_data, colWidths=[6*cm, 2*cm, 3*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sous-total:", format_currency(sale.subtotal)],
    ]
    
    if sale.discount_amount > 0:
        totals_data.append(["Remise:", f"-{format_currency(sale.discount_amount)}"])
    
    if sale.tax_amount > 0:
        totals_data.append([f"TVA ({sale.tax_rate}%):", format_currency(sale.tax_amount)])
    
    totals_data.append(["TOTAL:", format_currency(sale.total_amount)])
    totals_data.append(["Payé:", format_currency(sale.paid_amount)])
    
    remaining = sale.get_remaining_amount()
    if remaining > 0:
        totals_data.append(["Reste à payer:", format_currency(remaining)])
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, -3), (0, -3), colors.HexColor('#1a237e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(totals_table)
    
    # Footer
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("Merci pour votre achat!", styles['BodyTextCenter']))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(
        f"Document généré le {format_date(sale.created_at, with_time=True)}",
        styles['SmallText']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_payment_receipt_pdf(payment):
    """Generate PDF for payment receipt"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("REÇU DE PAIEMENT", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Receipt info
    info_data = [
        ["N° de reçu:", payment.receipt_number],
        ["Date:", format_date(payment.payment_date, with_time=True)],
        ["Mode de paiement:", payment.get_payment_method_display()],
    ]
    
    if payment.sale:
        info_data.append(["N° de vente:", payment.sale.sale_number])
    
    if payment.customer_name:
        info_data.append(["Client:", payment.customer_name])
    
    if payment.customer_phone:
        info_data.append(["Téléphone:", payment.customer_phone])
    
    if payment.reference:
        info_data.append(["Référence:", payment.reference])
    
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15*mm))
    
    # Amount
    amount_data = [
        ["Montant reçu:", format_currency(payment.amount)]
    ]
    
    amount_table = Table(amount_data, colWidths=[8*cm, 8*cm])
    amount_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2e7d32')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(amount_table)
    
    # Notes
    if payment.notes:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("Notes:", styles['SectionHeader']))
        elements.append(Paragraph(payment.notes, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("Signature: ____________________", styles['BodyTextRight']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_proforma_pdf(proforma):
    """Generate PDF for proforma invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("FACTURE PRO FORMA", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Proforma info
    info = [
        ["N° Pro forma:", proforma.proforma_number],
        ["Date d'émission:", format_date(proforma.issue_date)],
        ["Valide jusqu'au:", format_date(proforma.validity_date)],
        ["Statut:", proforma.get_status_display()],
    ]
    
    info_table = Table(info, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # Client info
    elements.append(Paragraph("Client", styles['SectionHeader']))
    
    if proforma.customer:
        client_info = f"""
        <b>{proforma.customer.name}</b><br/>
        {proforma.customer.address or ''}<br/>
        Tél: {proforma.customer.phone or '-'}<br/>
        Email: {proforma.customer.email or '-'}
        """
    else:
        client_info = f"""
        <b>{proforma.client_name or 'N/A'}</b><br/>
        {proforma.client_address or ''}<br/>
        Tél: {proforma.client_phone or '-'}<br/>
        Email: {proforma.client_email or '-'}
        """
    
    elements.append(Paragraph(client_info, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Items
    elements.append(Paragraph("Détails", styles['SectionHeader']))
    
    items_data = [["Produit", "Description", "Qté", "Prix unit.", "Total"]]
    
    for item in proforma.items.all():
        items_data.append([
            item.product.name,
            item.description or "-",
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.total)
        ])
    
    items_table = Table(items_data, colWidths=[4*cm, 4*cm, 2*cm, 3*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sous-total:", format_currency(proforma.subtotal)],
    ]
    
    if proforma.discount_amount > 0:
        totals_data.append(["Remise:", f"-{format_currency(proforma.discount_amount)}"])
    
    if proforma.tax_amount > 0:
        totals_data.append(["TVA:", format_currency(proforma.tax_amount)])
    
    totals_data.append(["TOTAL:", format_currency(proforma.total_amount)])
    
    totals_table = Table(totals_data, colWidths=[12.5*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(totals_table)
    
    # Conditions
    if proforma.conditions:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("Conditions de vente", styles['SectionHeader']))
        elements.append(Paragraph(proforma.conditions, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(
        "Ce document n'a pas valeur de facture définitive.",
        styles['SmallText']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_purchase_order_pdf(order):
    """Generate PDF for purchase order"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("BON DE COMMANDE", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Order info
    info = [
        ["N° de commande:", order.order_number],
        ["Date:", format_date(order.order_date)],
        ["Livraison prévue:", format_date(order.expected_delivery_date) or "-"],
        ["Statut:", order.get_status_display()],
    ]
    
    info_table = Table(info, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # Supplier info
    elements.append(Paragraph("Fournisseur", styles['SectionHeader']))
    supplier_info = f"""
    <b>{order.supplier.name}</b><br/>
    {order.supplier.address or ''}<br/>
    Tél: {order.supplier.phone or '-'}<br/>
    Email: {order.supplier.email or '-'}
    """
    elements.append(Paragraph(supplier_info, styles['Normal']))
    elements.append(Spacer(1, 8*mm))
    
    # Warehouse
    elements.append(Paragraph("Livraison à", styles['SectionHeader']))
    warehouse_info = f"""
    <b>{order.warehouse.name}</b> ({order.warehouse.code})<br/>
    {order.warehouse.address or ''}
    """
    elements.append(Paragraph(warehouse_info, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Items
    elements.append(Paragraph("Articles commandés", styles['SectionHeader']))
    
    items_data = [["Produit", "Qté", "Prix unitaire", "Total"]]
    
    for item in order.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.total)
        ])
    
    items_table = Table(items_data, colWidths=[6*cm, 2.5*cm, 4*cm, 4*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sous-total:", format_currency(order.subtotal)],
    ]
    
    if order.shipping_cost > 0:
        totals_data.append(["Frais de livraison:", format_currency(order.shipping_cost)])
    
    if order.tax_amount > 0:
        totals_data.append(["Taxes:", format_currency(order.tax_amount)])
    
    totals_data.append(["TOTAL:", format_currency(order.total_amount)])
    
    totals_table = Table(totals_data, colWidths=[12.5*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(totals_table)
    
    # Payment terms
    if order.payment_terms:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("Conditions de paiement", styles['SectionHeader']))
        elements.append(Paragraph(order.payment_terms, styles['Normal']))
    
    # Signatures
    elements.append(Spacer(1, 20*mm))
    sig_data = [["Signature Acheteur:", "", "Signature Fournisseur:"],
                ["____________________", "", "____________________"]]
    sig_table = Table(sig_data, colWidths=[6*cm, 4*cm, 6*cm])
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_delivery_note_pdf(note):
    """Generate PDF for delivery note"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("BON DE LIVRAISON", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Delivery info
    info = [
        ["N° de livraison:", note.delivery_number],
        ["N° de vente:", note.sale.sale_number],
        ["Date de livraison:", format_date(note.delivery_date)],
        ["Statut:", note.get_status_display()],
    ]
    
    info_table = Table(info, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # Recipient info
    elements.append(Paragraph("Destinataire", styles['SectionHeader']))
    recipient_info = f"""
    <b>{note.recipient_name}</b><br/>
    {note.delivery_address}<br/>
    Tél: {note.recipient_phone or '-'}
    """
    elements.append(Paragraph(recipient_info, styles['Normal']))
    elements.append(Spacer(1, 8*mm))
    
    # Transport info
    if note.carrier_name or note.driver_name:
        elements.append(Paragraph("Transport", styles['SectionHeader']))
        transport_info = []
        if note.carrier_name:
            transport_info.append(f"Transporteur: {note.carrier_name}")
        if note.driver_name:
            transport_info.append(f"Chauffeur: {note.driver_name}")
        if note.vehicle_info:
            transport_info.append(f"Véhicule: {note.vehicle_info}")
        elements.append(Paragraph("<br/>".join(transport_info), styles['Normal']))
        elements.append(Spacer(1, 8*mm))
    
    # Items
    elements.append(Paragraph("Articles à livrer", styles['SectionHeader']))
    
    items_data = [["Produit", "Qté commandée", "Qté livrée", "Observation"]]
    
    for item in note.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            str(item.delivered_quantity),
            item.notes or "-"
        ])
    
    items_table = Table(items_data, colWidths=[5*cm, 3*cm, 3*cm, 5*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    
    # Notes
    if note.notes:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("Observations", styles['SectionHeader']))
        elements.append(Paragraph(note.notes, styles['Normal']))
    
    # Signatures
    elements.append(Spacer(1, 20*mm))
    sig_data = [
        ["Signature Expéditeur:", "", "Signature Destinataire:"],
        ["Date: ___/___/______", "", "Date: ___/___/______"],
        ["", "", ""],
        ["____________________", "", "____________________"]
    ]
    sig_table = Table(sig_data, colWidths=[6*cm, 4*cm, 6*cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_credit_sale_statement_pdf(credit_sale):
    """Generate PDF statement for a credit sale with payment history"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("RELEVÉ DE CRÉANCE", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Credit sale info
    info_data = [
        ["N° de vente:", credit_sale.sale.sale_number],
        ["Date de vente:", format_date(credit_sale.sale.sale_date, with_time=True)],
        ["Statut:", credit_sale.get_status_display()],
    ]
    
    if credit_sale.due_date:
        info_data.append(["Échéance:", format_date(credit_sale.due_date)])
    else:
        info_data.append(["Échéance:", "Sans échéance"])
    
    info_table = Table(info_data, colWidths=[4*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))
    
    # Customer info
    elements.append(Paragraph("Client", styles['SectionHeader']))
    customer = credit_sale.customer
    if customer:
        customer_info = f"""
        <b>{customer.name}</b><br/>
        {customer.address or ''}<br/>
        Tél: {customer.phone or '-'}<br/>
        Email: {customer.email or '-'}
        """
    else:
        customer_info = "Client non renseigné"
    
    elements.append(Paragraph(customer_info, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Items from sale
    elements.append(Paragraph("Détails de la vente", styles['SectionHeader']))
    
    items_data = [["Produit", "Qté", "Prix unit.", "Remise", "Total"]]
    
    for item in credit_sale.sale.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.discount_amount) if item.discount_amount > 0 else "-",
            format_currency(item.total)
        ])
    
    items_table = Table(items_data, colWidths=[6*cm, 2*cm, 3*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Montant total:", format_currency(credit_sale.total_amount)],
    ]
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a237e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 10*mm))
    
    # Payment history
    elements.append(Paragraph("Historique des paiements", styles['SectionHeader']))
    
    payments = credit_sale.sale.payments.all().order_by('payment_date')
    if payments.exists():
        payments_data = [["Date", "Référence", "Mode", "Montant"]]
        
        for payment in payments:
            payments_data.append([
                format_date(payment.payment_date, with_time=True),
                payment.receipt_number or "-",
                payment.get_payment_method_display(),
                format_currency(payment.amount)
            ])
        
        payments_table = Table(payments_data, colWidths=[4*cm, 4*cm, 4*cm, 4.5*cm])
        payments_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(payments_table)
    else:
        elements.append(Paragraph("Aucun paiement enregistré.", styles['Normal']))
    
    elements.append(Spacer(1, 10*mm))
    
    # Summary
    elements.append(Paragraph("Récapitulatif", styles['SectionHeader']))
    
    summary_data = [
        ["Total de la créance:", format_currency(credit_sale.total_amount)],
        ["Montant payé:", format_currency(credit_sale.paid_amount)],
        ["Reste à payer:", format_currency(credit_sale.remaining_amount)],
    ]
    
    summary_table = Table(summary_data, colWidths=[12*cm, 4.5*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#d32f2f') if credit_sale.remaining_amount > 0 else colors.HexColor('#2e7d32')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(summary_table)
    
    # Status indicator
    elements.append(Spacer(1, 10*mm))
    if credit_sale.remaining_amount <= 0:
        status_text = "✓ CRÉANCE SOLDÉE"
        status_color = colors.HexColor('#2e7d32')
        bg_color = colors.HexColor('#e8f5e9')
    elif credit_sale.status == 'overdue':
        status_text = "⚠ CRÉANCE EN RETARD"
        status_color = colors.HexColor('#d32f2f')
        bg_color = colors.HexColor('#ffebee')
    else:
        status_text = "◷ CRÉANCE EN COURS"
        status_color = colors.HexColor('#f57c00')
        bg_color = colors.HexColor('#fff3e0')
    
    status_data = [[status_text]]
    status_table = Table(status_data, colWidths=[16.5*cm])
    status_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (-1, -1), status_color),
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(status_table)
    
    # Footer
    elements.append(Spacer(1, 15*mm))
    from django.utils import timezone
    elements.append(Paragraph(
        f"Document généré le {format_date(timezone.now(), with_time=True)}",
        styles['SmallText']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(sale):
    """Generate PDF invoice for a sale (more formal version of receipt)"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = get_styles()
    elements = []
    
    # Header
    elements.append(Paragraph("FACTURE", styles['CustomTitle']))
    elements.append(Spacer(1, 5*mm))
    
    # Invoice info (2 columns: company info + invoice details)
    org = sale.organization
    org_info = f"""
    <b>{org.name if org else 'LouraTech'}</b><br/>
    {getattr(org, 'address', 'N/A')}<br/>
    Tél: {getattr(org, 'phone', 'N/A')}<br/>
    Email: {getattr(org, 'email', 'N/A')}
    """
    
    invoice_info = f"""
    <b>Facture N°:</b> {sale.sale_number}<br/>
    <b>Date:</b> {format_date(sale.sale_date, with_time=False)}<br/>
    <b>Statut:</b> {sale.get_payment_status_display()}
    """
    
    header_data = [[Paragraph(org_info, styles['Normal']), Paragraph(invoice_info, styles['BodyTextRight'])]]
    header_table = Table(header_data, colWidths=[8.5*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10*mm))
    
    # Customer info
    elements.append(Paragraph("Facturé à:", styles['SectionHeader']))
    if sale.customer:
        customer_info = f"""
        <b>{sale.customer.name}</b><br/>
        {sale.customer.address or ''}<br/>
        Tél: {sale.customer.phone or '-'}<br/>
        Email: {sale.customer.email or '-'}
        """
    else:
        customer_info = "<b>Client anonyme</b>"
    
    elements.append(Paragraph(customer_info, styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Items table
    elements.append(Paragraph("Détails", styles['SectionHeader']))
    
    items_data = [["Description", "Qté", "Prix unitaire", "Remise", "Total HT"]]
    
    for item in sale.items.all():
        items_data.append([
            item.product.name,
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.discount_amount) if item.discount_amount > 0 else "-",
            format_currency(item.total)
        ])
    
    items_table = Table(items_data, colWidths=[6*cm, 2*cm, 3*cm, 2.5*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))
    
    # Totals
    totals_data = [
        ["Sous-total HT:", format_currency(sale.subtotal)],
    ]
    
    if sale.discount_amount > 0:
        totals_data.append(["Remise:", f"-{format_currency(sale.discount_amount)}"])
    
    if sale.tax_amount > 0:
        totals_data.append([f"TVA ({sale.tax_rate}%):", format_currency(sale.tax_amount)])
    
    totals_data.append(["TOTAL TTC:", format_currency(sale.total_amount)])
    
    totals_table = Table(totals_data, colWidths=[12*cm, 4.5*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a237e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a237e')),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 8*mm))
    
    # Payment info
    elements.append(Paragraph("Informations de paiement", styles['SectionHeader']))
    
    payment_info_data = [
        ["Montant payé:", format_currency(sale.paid_amount)],
        ["Reste à payer:", format_currency(sale.get_remaining_amount())],
        ["Mode de paiement:", sale.get_payment_method_display()],
    ]
    
    payment_info_table = Table(payment_info_data, colWidths=[4*cm, 8*cm])
    payment_info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(payment_info_table)
    
    # Notes
    if sale.notes:
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("Notes:", styles['SectionHeader']))
        elements.append(Paragraph(sale.notes, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(
        "Merci pour votre confiance!",
        styles['BodyTextCenter']
    ))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(
        f"Document généré le {format_date(sale.created_at, with_time=True)}",
        styles['SmallText']
    ))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def export_expenses_pdf(queryset, organization, filters=None):
    """Export expenses list to PDF with filters info"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = get_styles()
    elements = []

    # Header
    elements.append(Paragraph("RAPPORT DES DÉPENSES", styles['CustomTitle']))
    elements.append(Paragraph(f"Organisation: {organization.name}", styles['Normal']))

    # Date de génération
    from django.utils import timezone
    elements.append(Paragraph(
        f"Date de génération: {timezone.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Small']
    ))

    # Filtres appliqués
    if filters:
        filter_text = "Filtres: "
        filter_parts = []
        if filters.get('start_date'):
            filter_parts.append(f"Du {filters['start_date']}")
        if filters.get('end_date'):
            filter_parts.append(f"Au {filters['end_date']}")
        if filters.get('category_name'):
            filter_parts.append(f"Catégorie: {filters['category_name']}")

        if filter_parts:
            filter_text += ", ".join(filter_parts)
            elements.append(Paragraph(filter_text, styles['Small']))

    elements.append(Spacer(1, 10*mm))

    # Summary
    from django.db.models import Sum, Count
    total = queryset.aggregate(total=Sum('amount'))['total'] or 0

    summary_data = [
        ["Nombre de dépenses:", str(queryset.count())],
        ["Total:", format_currency(total)],
    ]

    summary_table = Table(summary_data, colWidths=[4*cm, 8*cm])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10*mm))

    # Répartition par catégorie
    by_category = queryset.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    if by_category:
        elements.append(Paragraph("Répartition par catégorie:", styles['Heading2']))
        category_data = [["Catégorie", "Nombre", "Total"]]
        for cat in by_category:
            category_data.append([
                cat['category__name'] or "Sans catégorie",
                str(cat['count']),
                format_currency(cat['total'])
            ])

        cat_table = Table(category_data, colWidths=[6*cm, 3*cm, 4*cm])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 10*mm))

    # Expenses table
    elements.append(Paragraph("Liste détaillée des dépenses:", styles['Heading2']))
    data = [["Date", "Description", "Catégorie", "Bénéficiaire", "Montant"]]

    for expense in queryset:
        data.append([
            format_date(expense.expense_date),
            expense.description[:30] + "..." if len(expense.description) > 30 else expense.description,
            expense.category.name if expense.category else "-",
            expense.beneficiary[:20] if expense.beneficiary else "-",
            format_currency(expense.amount)
        ])

    table = Table(data, colWidths=[2.5*cm, 5*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer
