"""
Générateur de PDF pour les documents d'inventaire
Design sobre, professionnel et compact
"""

from io import BytesIO
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, PageBreak
from datetime import datetime


# Couleurs professionnelles
PRIMARY_COLOR = colors.HexColor('#1a1a2e')
SECONDARY_COLOR = colors.HexColor('#4a4e69')
ACCENT_COLOR = colors.HexColor('#22577a')
SUCCESS_COLOR = colors.HexColor('#28a745')
WARNING_COLOR = colors.HexColor('#ffc107')
DANGER_COLOR = colors.HexColor('#dc3545')
LIGHT_BG = colors.HexColor('#f8f9fa')
BORDER_COLOR = colors.HexColor('#dee2e6')


def get_styles():
    """Styles communs pour tous les documents"""
    styles = getSampleStyleSheet()
    
    return {
        'title': ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=PRIMARY_COLOR,
            spaceAfter=4,
            alignment=1,
            fontName='Helvetica-Bold',
        ),
        'subtitle': ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=SECONDARY_COLOR,
            alignment=1,
            spaceAfter=8,
        ),
        'heading': ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=10,
            textColor=PRIMARY_COLOR,
            spaceBefore=8,
            spaceAfter=4,
            fontName='Helvetica-Bold',
        ),
        'normal': ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            leading=12,
        ),
        'small': ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            textColor=SECONDARY_COLOR,
        ),
        'footer': ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#999999'),
            alignment=1,
        ),
    }


def create_header_table(title, org_name, doc_ref=None):
    """Crée un en-tête compact avec logo et infos"""
    header_data = [
        [
            Paragraph(f"<b>{org_name}</b>", get_styles()['normal']),
            Paragraph(f"<b>{title}</b>", get_styles()['title']),
            Paragraph(doc_ref or datetime.now().strftime('%d/%m/%Y'), get_styles()['small']),
        ]
    ]
    
    header_table = Table(header_data, colWidths=[5*cm, 8*cm, 4*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return header_table


def format_currency(amount, currency='GNF'):
    """Formate un montant en devise"""
    if amount is None:
        return '0 ' + currency
    return f"{amount:,.0f} {currency}".replace(',', ' ')


def generate_order_pdf(order):
    """
    Génère un PDF pour un bon de commande (Purchase Order)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()
    org = order.organization

    # Statuts
    status_labels = {
        'draft': 'BROUILLON',
        'pending': 'EN ATTENTE',
        'confirmed': 'CONFIRMÉE',
        'received': 'REÇUE',
        'cancelled': 'ANNULÉE',
    }
    
    status_colors = {
        'draft': colors.HexColor('#6c757d'),
        'pending': WARNING_COLOR,
        'confirmed': ACCENT_COLOR,
        'received': SUCCESS_COLOR,
        'cancelled': DANGER_COLOR,
    }

    # En-tête
    elements.append(create_header_table(
        "BON DE COMMANDE",
        org.name,
        f"N° {order.order_number}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 4*mm))

    # Statut
    status = order.status
    status_data = [[status_labels.get(status, status)]]
    status_table = Table(status_data, colWidths=[17*cm])
    status_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), status_colors.get(status, SECONDARY_COLOR)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 4*mm))

    # Infos fournisseur + commande
    info_data = [
        ["FOURNISSEUR", "", "COMMANDE", ""],
        [
            "Nom:",
            order.supplier.name if order.supplier else "N/A",
            "Date commande:",
            order.order_date.strftime('%d/%m/%Y') if order.order_date else "N/A"
        ],
        [
            "Contact:",
            order.supplier.contact_person if order.supplier else "N/A",
            "Livraison prévue:",
            order.expected_delivery_date.strftime('%d/%m/%Y') if order.expected_delivery_date else "N/A"
        ],
        [
            "Email:",
            order.supplier.email if order.supplier else "N/A",
            "Entrepôt:",
            order.warehouse.name if order.warehouse else "N/A"
        ],
    ]

    info_table = Table(info_data, colWidths=[2.5*cm, 5.5*cm, 3*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('TEXTCOLOR', (2, 1), (2, -1), SECONDARY_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Articles commandés
    items_data = [["#", "PRODUIT", "SKU", "QTÉ", "PRIX UNIT.", "TOTAL"]]
    
    items = order.items.all().select_related('product')
    for idx, item in enumerate(items, 1):
        items_data.append([
            str(idx),
            item.product.name if item.product else "N/A",
            item.product.sku if item.product else "N/A",
            str(item.quantity),
            format_currency(item.unit_price),
            format_currency(item.quantity * item.unit_price if item.unit_price else 0),
        ])
    
    # Total
    items_data.append(["", "", "", "", "TOTAL:", format_currency(order.total_amount)])

    items_table = Table(items_data, colWidths=[1*cm, 6*cm, 2.5*cm, 1.5*cm, 3*cm, 3*cm])
    
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Ligne total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), ACCENT_COLOR),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 6*mm))

    # Notes
    if order.notes:
        elements.append(Paragraph("<b>NOTES</b>", styles['heading']))
        elements.append(Paragraph(order.notes, styles['small']))
        elements.append(Spacer(1, 4*mm))

    # Footer
    footer_data = [
        [f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", "", f"Réf: {str(order.id)[:8].upper()}"]
    ]
    footer_table = Table(footer_data, colWidths=[6*cm, 5*cm, 6*cm])
    footer_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TEXTCOLOR', (0, 0), (-1, -1), SECONDARY_COLOR),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_product_catalog_pdf(products, organization):
    """
    Génère un PDF catalogue de produits
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()

    # En-tête
    elements.append(create_header_table(
        "CATALOGUE PRODUITS",
        organization.name,
        datetime.now().strftime('%d/%m/%Y')
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 6*mm))

    # Statistiques
    total_products = len(products)
    total_value = sum((p.purchase_price or 0) * (p.get_total_stock() or 0) for p in products)
    
    stats_data = [
        [f"Nombre de produits: {total_products}", f"Valeur totale du stock: {format_currency(total_value)}"]
    ]
    stats_table = Table(stats_data, colWidths=[8.5*cm, 8.5*cm])
    stats_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), PRIMARY_COLOR),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 6*mm))

    # Tableau des produits
    products_data = [["SKU", "NOM", "CATÉGORIE", "STOCK", "PRIX ACHAT", "PRIX VENTE"]]
    
    for product in products:
        total_stock = product.get_total_stock() if hasattr(product, 'get_total_stock') else 0
        products_data.append([
            product.sku or "-",
            Paragraph(product.name[:30] + "..." if len(product.name) > 30 else product.name, styles['small']),
            product.category.name if product.category else "-",
            str(total_stock or 0),
            format_currency(product.purchase_price),
            format_currency(product.selling_price),
        ])

    products_table = Table(products_data, colWidths=[2.5*cm, 5*cm, 3*cm, 1.5*cm, 2.5*cm, 2.5*cm])
    products_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(products_table)
    elements.append(Spacer(1, 6*mm))

    # Footer
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_stock_report_pdf(stocks, organization, warehouse=None):
    """
    Génère un PDF rapport de stock
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()

    title = f"RAPPORT DE STOCK - {warehouse.name}" if warehouse else "RAPPORT DE STOCK GLOBAL"

    # En-tête
    elements.append(create_header_table(
        title,
        organization.name,
        datetime.now().strftime('%d/%m/%Y')
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 6*mm))

    # Statistiques
    total_items = len(stocks)
    total_quantity = sum(s.quantity for s in stocks)
    total_value = sum(s.quantity * (s.product.purchase_price or 0) for s in stocks)
    low_stock = sum(1 for s in stocks if s.quantity <= (s.product.min_stock_level or 0))
    out_of_stock = sum(1 for s in stocks if s.quantity == 0)

    stats_data = [
        ["RÉSUMÉ DU STOCK", "", "", ""],
        [
            f"Articles: {total_items}",
            f"Quantité totale: {total_quantity:,.0f}",
            f"Stock bas: {low_stock}",
            f"Rupture: {out_of_stock}"
        ],
        [f"Valeur totale: {format_currency(total_value)}", "", "", ""]
    ]
    stats_table = Table(stats_data, colWidths=[4.25*cm, 4.25*cm, 4.25*cm, 4.25*cm])
    stats_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('SPAN', (0, 2), (-1, 2)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('BACKGROUND', (0, 2), (-1, 2), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 6*mm))

    # Tableau des stocks
    stock_data = [["SKU", "PRODUIT", "ENTREPÔT", "QTÉ", "MIN", "STATUT", "VALEUR"]]
    
    for stock in stocks:
        qty = stock.quantity
        min_level = stock.product.min_stock_level or 0
        
        if qty == 0:
            status = "RUPTURE"
            status_color = "red"
        elif qty <= min_level:
            status = "BAS"
            status_color = "orange"
        else:
            status = "OK"
            status_color = "green"
        
        stock_data.append([
            stock.product.sku or "-",
            Paragraph(stock.product.name[:25] + "..." if len(stock.product.name) > 25 else stock.product.name, styles['small']),
            stock.warehouse.name if stock.warehouse else "-",
            str(int(qty)),
            str(int(min_level)),
            status,
            format_currency(qty * (stock.product.purchase_price or 0)),
        ])

    stock_table = Table(stock_data, colWidths=[2*cm, 4.5*cm, 3*cm, 1.5*cm, 1.5*cm, 2*cm, 2.5*cm])
    
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (5, 0), (5, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Colorier les statuts
    for idx, stock in enumerate(stocks, 1):
        qty = stock.quantity
        min_level = stock.product.min_stock_level or 0
        if qty == 0:
            table_style.append(('TEXTCOLOR', (5, idx), (5, idx), DANGER_COLOR))
            table_style.append(('FONTNAME', (5, idx), (5, idx), 'Helvetica-Bold'))
        elif qty <= min_level:
            table_style.append(('TEXTCOLOR', (5, idx), (5, idx), WARNING_COLOR))
    
    stock_table.setStyle(TableStyle(table_style))
    elements.append(stock_table)
    elements.append(Spacer(1, 6*mm))

    # Footer
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_stock_count_pdf(stock_count):
    """
    Génère un PDF pour un rapport d'inventaire physique
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()
    org = stock_count.organization

    # Statuts
    status_labels = {
        'draft': 'BROUILLON',
        'planned': 'PLANIFIÉ',
        'in_progress': 'EN COURS',
        'completed': 'TERMINÉ',
        'validated': 'VALIDÉ',
        'cancelled': 'ANNULÉ',
    }
    
    status_colors = {
        'draft': colors.HexColor('#6c757d'),
        'planned': ACCENT_COLOR,
        'in_progress': WARNING_COLOR,
        'completed': colors.HexColor('#17a2b8'),
        'validated': SUCCESS_COLOR,
        'cancelled': DANGER_COLOR,
    }

    # En-tête
    elements.append(create_header_table(
        "RAPPORT D'INVENTAIRE",
        org.name,
        f"N° {stock_count.count_number}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 4*mm))

    # Statut
    status = stock_count.status
    status_data = [[status_labels.get(status, status)]]
    status_table = Table(status_data, colWidths=[17*cm])
    status_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), status_colors.get(status, SECONDARY_COLOR)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 4*mm))

    # Infos inventaire
    info_data = [
        ["INFORMATIONS DE L'INVENTAIRE", ""],
        ["Entrepôt:", stock_count.warehouse.name if stock_count.warehouse else "N/A"],
        ["Date de l'inventaire:", stock_count.count_date.strftime('%d/%m/%Y') if stock_count.count_date else "N/A"],
        ["Notes:", stock_count.notes or "-"],
    ]

    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    # Statistiques
    items = list(stock_count.items.all().select_related('product'))
    total_items = len(items)
    total_expected = sum(float(i.expected_quantity) for i in items)
    total_counted = sum(float(i.counted_quantity) for i in items)
    
    items_matched = sum(1 for i in items if i.counted_quantity == i.expected_quantity)
    items_surplus = sum(1 for i in items if i.counted_quantity > i.expected_quantity)
    items_deficit = sum(1 for i in items if i.counted_quantity < i.expected_quantity)
    
    accuracy = (items_matched / total_items * 100) if total_items > 0 else 0

    stats_data = [
        ["STATISTIQUES", "", "", ""],
        [
            f"Articles: {total_items}",
            f"Conformes: {items_matched}",
            f"Excédents: {items_surplus}",
            f"Déficits: {items_deficit}"
        ],
        [
            f"Qté attendue: {total_expected:,.0f}",
            f"Qté comptée: {total_counted:,.0f}",
            f"Différence: {total_counted - total_expected:+,.0f}",
            f"Précision: {accuracy:.1f}%"
        ],
    ]
    stats_table = Table(stats_data, colWidths=[4.25*cm, 4.25*cm, 4.25*cm, 4.25*cm])
    stats_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 6*mm))

    # Détail des articles
    items_data = [["SKU", "PRODUIT", "ATTENDU", "COMPTÉ", "ÉCART", "NOTES"]]
    
    for item in items:
        difference = float(item.counted_quantity) - float(item.expected_quantity)
        diff_str = f"{difference:+.0f}" if difference != 0 else "0"
        
        items_data.append([
            item.product.sku if item.product else "-",
            Paragraph(item.product.name[:20] + "..." if item.product and len(item.product.name) > 20 else (item.product.name if item.product else "N/A"), styles['small']),
            f"{float(item.expected_quantity):.0f}",
            f"{float(item.counted_quantity):.0f}",
            diff_str,
            item.notes[:15] + "..." if item.notes and len(item.notes) > 15 else (item.notes or "-"),
        ])

    items_table = Table(items_data, colWidths=[2*cm, 5*cm, 2*cm, 2*cm, 2*cm, 4*cm])
    
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Colorier les écarts
    for idx, item in enumerate(items, 1):
        difference = float(item.counted_quantity) - float(item.expected_quantity)
        if difference > 0:
            table_style.append(('TEXTCOLOR', (4, idx), (4, idx), SUCCESS_COLOR))
        elif difference < 0:
            table_style.append(('TEXTCOLOR', (4, idx), (4, idx), DANGER_COLOR))
            table_style.append(('FONTNAME', (4, idx), (4, idx), 'Helvetica-Bold'))
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 6*mm))

    # Footer
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_quote_pdf(quote_data, organization):
    """
    Génère un PDF pour un devis
    
    quote_data: dict avec les clés:
    - quote_number: str
    - date: date
    - valid_until: date
    - client_name: str
    - client_email: str
    - client_phone: str
    - client_address: str
    - items: list[dict] avec product_name, quantity, unit_price
    - notes: str (optional)
    - discount_percent: Decimal (optional)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()

    # En-tête
    elements.append(create_header_table(
        "DEVIS",
        organization.name,
        f"N° {quote_data.get('quote_number', 'N/A')}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 6*mm))

    # Infos devis + client
    quote_date = quote_data.get('date', datetime.now().date())
    valid_until = quote_data.get('valid_until')
    
    info_data = [
        ["DEVIS", "", "CLIENT", ""],
        [
            "Date:",
            quote_date.strftime('%d/%m/%Y') if hasattr(quote_date, 'strftime') else str(quote_date),
            "Nom:",
            quote_data.get('client_name', 'N/A')
        ],
        [
            "Validité:",
            valid_until.strftime('%d/%m/%Y') if valid_until and hasattr(valid_until, 'strftime') else "30 jours",
            "Email:",
            quote_data.get('client_email', 'N/A')
        ],
        [
            "",
            "",
            "Tél:",
            quote_data.get('client_phone', 'N/A')
        ],
    ]

    info_table = Table(info_data, colWidths=[2.5*cm, 5*cm, 2.5*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('TEXTCOLOR', (2, 1), (2, -1), SECONDARY_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Articles
    items_data = [["#", "DÉSIGNATION", "QTÉ", "PRIX UNIT.", "TOTAL"]]
    
    subtotal = Decimal('0')
    for idx, item in enumerate(quote_data.get('items', []), 1):
        qty = Decimal(str(item.get('quantity', 0)))
        unit_price = Decimal(str(item.get('unit_price', 0)))
        total = qty * unit_price
        subtotal += total
        
        items_data.append([
            str(idx),
            item.get('product_name', 'N/A'),
            str(qty),
            format_currency(unit_price),
            format_currency(total),
        ])
    
    # Sous-total, remise, total
    discount_percent = Decimal(str(quote_data.get('discount_percent', 0)))
    discount_amount = subtotal * discount_percent / 100
    total = subtotal - discount_amount
    
    items_data.append(["", "", "", "Sous-total:", format_currency(subtotal)])
    if discount_percent > 0:
        items_data.append(["", "", "", f"Remise ({discount_percent}%):", f"-{format_currency(discount_amount)}"])
    items_data.append(["", "", "", "TOTAL:", format_currency(total)])

    items_table = Table(items_data, colWidths=[1*cm, 8*cm, 2*cm, 3*cm, 3*cm])
    
    num_items = len(quote_data.get('items', []))
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, num_items), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Ligne total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (3, -1), (-1, -1), ACCENT_COLOR),
        ('TEXTCOLOR', (3, -1), (-1, -1), colors.white),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))

    # Conditions
    conditions_text = """
    <b>CONDITIONS GÉNÉRALES</b><br/><br/>
    • Ce devis est valable pour la durée indiquée ci-dessus.<br/>
    • Paiement à la commande sauf accord préalable.<br/>
    • Les prix sont exprimés en GNF et sont susceptibles de modification.<br/>
    """
    if quote_data.get('notes'):
        conditions_text += f"<br/><b>Notes:</b> {quote_data['notes']}"
    
    elements.append(Paragraph(conditions_text, styles['small']))
    elements.append(Spacer(1, 8*mm))

    # Signature
    sig_data = [
        ["Accepté et signé par le client:", ""],
        ["", ""],
        ["Date: _______________", "Signature:"],
    ]
    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 30),
    ]))
    elements.append(sig_table)

    # Footer
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_invoice_pdf(invoice_data, organization):
    """
    Génère un PDF pour une facture
    
    invoice_data: dict avec les clés:
    - invoice_number: str
    - date: date
    - due_date: date
    - client_name: str
    - client_email: str
    - client_phone: str
    - client_address: str
    - items: list[dict] avec product_name, quantity, unit_price
    - notes: str (optional)
    - discount_percent: Decimal (optional)
    - tax_percent: Decimal (optional, default 18%)
    - is_paid: bool
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    elements = []
    styles = get_styles()

    # En-tête
    elements.append(create_header_table(
        "FACTURE",
        organization.name,
        f"N° {invoice_data.get('invoice_number', 'N/A')}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 4*mm))

    # Statut paiement
    is_paid = invoice_data.get('is_paid', False)
    status_data = [["PAYÉE" if is_paid else "EN ATTENTE DE PAIEMENT"]]
    status_table = Table(status_data, colWidths=[17*cm])
    status_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), SUCCESS_COLOR if is_paid else WARNING_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white if is_paid else PRIMARY_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 4*mm))

    # Infos facture + client
    invoice_date = invoice_data.get('date', datetime.now().date())
    due_date = invoice_data.get('due_date')
    
    info_data = [
        ["FACTURE", "", "CLIENT", ""],
        [
            "Date:",
            invoice_date.strftime('%d/%m/%Y') if hasattr(invoice_date, 'strftime') else str(invoice_date),
            "Nom:",
            invoice_data.get('client_name', 'N/A')
        ],
        [
            "Échéance:",
            due_date.strftime('%d/%m/%Y') if due_date and hasattr(due_date, 'strftime') else "À réception",
            "Email:",
            invoice_data.get('client_email', 'N/A')
        ],
        [
            "",
            "",
            "Tél:",
            invoice_data.get('client_phone', 'N/A')
        ],
    ]

    info_table = Table(info_data, colWidths=[2.5*cm, 5*cm, 2.5*cm, 6*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('TEXTCOLOR', (2, 1), (2, -1), SECONDARY_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Articles
    items_data = [["#", "DÉSIGNATION", "QTÉ", "PRIX UNIT.", "TOTAL"]]
    
    subtotal = Decimal('0')
    for idx, item in enumerate(invoice_data.get('items', []), 1):
        qty = Decimal(str(item.get('quantity', 0)))
        unit_price = Decimal(str(item.get('unit_price', 0)))
        total = qty * unit_price
        subtotal += total
        
        items_data.append([
            str(idx),
            item.get('product_name', 'N/A'),
            str(qty),
            format_currency(unit_price),
            format_currency(total),
        ])
    
    # Calculs
    discount_percent = Decimal(str(invoice_data.get('discount_percent', 0)))
    discount_amount = subtotal * discount_percent / 100
    after_discount = subtotal - discount_amount
    
    tax_percent = Decimal(str(invoice_data.get('tax_percent', 18)))
    tax_amount = after_discount * tax_percent / 100
    total = after_discount + tax_amount
    
    items_data.append(["", "", "", "Sous-total HT:", format_currency(subtotal)])
    if discount_percent > 0:
        items_data.append(["", "", "", f"Remise ({discount_percent}%):", f"-{format_currency(discount_amount)}"])
    items_data.append(["", "", "", f"TVA ({tax_percent}%):", format_currency(tax_amount)])
    items_data.append(["", "", "", "TOTAL TTC:", format_currency(total)])

    items_table = Table(items_data, colWidths=[1*cm, 8*cm, 2*cm, 3*cm, 3*cm])
    
    num_items = len(invoice_data.get('items', []))
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, num_items), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Ligne total
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (3, -1), (-1, -1), ACCENT_COLOR),
        ('TEXTCOLOR', (3, -1), (-1, -1), colors.white),
    ]
    
    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)
    elements.append(Spacer(1, 8*mm))

    # Infos bancaires / Paiement
    payment_info = f"""
    <b>INFORMATIONS DE PAIEMENT</b><br/><br/>
    Merci de régler cette facture à l'ordre de <b>{organization.name}</b>.<br/>
    """
    if invoice_data.get('notes'):
        payment_info += f"<br/><b>Notes:</b> {invoice_data['notes']}"
    
    elements.append(Paragraph(payment_info, styles['small']))

    # Footer
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
