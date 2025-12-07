"""
Générateur de PDF pour les fiches de paie
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime


def generate_payslip_pdf(payslip):
    """
    Génère un PDF pour une fiche de paie

    Args:
        payslip: Instance du modèle Payslip

    Returns:
        BytesIO: Buffer contenant le PDF généré
    """
    buffer = BytesIO()

    # Créer le document PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Conteneur pour les éléments du PDF
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1F2937'),
        spaceAfter=12,
        alignment=1  # Centré
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
    )

    normal_style = styles['Normal']

    # En-tête du document
    elements.append(Paragraph("FICHE DE PAIE", title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Informations de l'organisation
    org = payslip.employee.organization
    org_data = [
        ["Organisation:", org.name],
        ["", org.address if hasattr(org, 'address') else ""],
    ]

    org_table = Table(org_data, colWidths=[4*cm, 12*cm])
    org_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(org_table)
    elements.append(Spacer(1, 0.5*cm))

    # Informations de l'employé
    elements.append(Paragraph("INFORMATIONS EMPLOYÉ", heading_style))

    employee_data = [
        ["Nom complet:", payslip.employee.get_full_name()],
        ["Matricule:", payslip.employee.employee_id or "N/A"],
        ["Email:", payslip.employee.email],
        ["Département:", payslip.employee.department.name if payslip.employee.department else "N/A"],
        ["Poste:", payslip.employee.position.title if payslip.employee.position else "N/A"],
    ]

    employee_table = Table(employee_data, colWidths=[4*cm, 12*cm])
    employee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 0.5*cm))

    # Période de paie
    elements.append(Paragraph("PÉRIODE DE PAIE", heading_style))

    period_data = [
        ["Période:", payslip.payroll_period.name],
        ["Du:", payslip.payroll_period.start_date.strftime('%d/%m/%Y')],
        ["Au:", payslip.payroll_period.end_date.strftime('%d/%m/%Y')],
        ["Date de paiement:", payslip.payroll_period.payment_date.strftime('%d/%m/%Y') if payslip.payroll_period.payment_date else "Non définie"],
    ]

    period_table = Table(period_data, colWidths=[4*cm, 12*cm])
    period_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 0.8*cm))

    # Détails de la paie
    elements.append(Paragraph("DÉTAILS DE LA PAIE", heading_style))

    # Salaire de base
    salary_data = [
        ["DESCRIPTION", "MONTANT"],
        ["Salaire de base", f"{payslip.base_salary:,.2f} {payslip.currency}"],
    ]

    # Primes (allowances)
    allowances = payslip.items.filter(is_deduction=False).order_by('name')
    if allowances.exists():
        salary_data.append(["", ""])  # Ligne vide
        salary_data.append(["PRIMES ET INDEMNITÉS", ""])
        for item in allowances:
            salary_data.append([f"  • {item.name}", f"{item.amount:,.2f} {payslip.currency}"])

    # Total brut
    salary_data.append(["", ""])
    salary_data.append(["SALAIRE BRUT", f"{payslip.gross_salary:,.2f} {payslip.currency}"])

    # Déductions
    deductions = payslip.items.filter(is_deduction=True).order_by('name')
    if deductions.exists():
        salary_data.append(["", ""])
        salary_data.append(["DÉDUCTIONS", ""])
        for item in deductions:
            salary_data.append([f"  • {item.name}", f"{item.amount:,.2f} {payslip.currency}"])

    # Total déductions
    salary_data.append(["", ""])
    salary_data.append(["TOTAL DÉDUCTIONS", f"{payslip.total_deductions:,.2f} {payslip.currency}"])

    # Salaire net
    salary_data.append(["", ""])
    salary_data.append(["SALAIRE NET À PAYER", f"{payslip.net_salary:,.2f} {payslip.currency}"])

    # Créer le tableau
    salary_table = Table(salary_data, colWidths=[10*cm, 6*cm])

    # Style du tableau
    table_style = [
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),

        # Corps du tableau
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

        # Lignes de séparation
        ('GRID', (0, 0), (-1, 0), 1, colors.HexColor('#1F2937')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#E5E7EB')),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]

    # Mettre en évidence les sections
    row_idx = 1  # Après l'en-tête

    # Salaire de base
    table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#F3F4F6')))
    row_idx += 1

    # Primes
    if allowances.exists():
        row_idx += 1  # Ligne vide
        table_style.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))
        table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#DBEAFE')))
        row_idx += 1
        row_idx += allowances.count()

    # Total brut
    row_idx += 1  # Ligne vide
    table_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
    table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#DCFCE7')))
    table_style.append(('FONTSIZE', (0, row_idx), (-1, row_idx), 11))
    row_idx += 1

    # Déductions
    if deductions.exists():
        row_idx += 1  # Ligne vide
        table_style.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))
        table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FEE2E2')))
        row_idx += 1
        row_idx += deductions.count()

    # Total déductions
    row_idx += 1  # Ligne vide
    table_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
    table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#FEE2E2')))
    table_style.append(('FONTSIZE', (0, row_idx), (-1, row_idx), 11))
    row_idx += 1

    # Salaire net (dernière ligne)
    row_idx += 1  # Ligne vide
    table_style.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
    table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#10B981')))
    table_style.append(('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.white))
    table_style.append(('FONTSIZE', (0, row_idx), (-1, row_idx), 12))

    salary_table.setStyle(TableStyle(table_style))
    elements.append(salary_table)

    # Informations complémentaires
    if payslip.notes:
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("NOTES", heading_style))
        elements.append(Paragraph(payslip.notes, normal_style))

    # Pied de page
    elements.append(Spacer(1, 1*cm))
    footer_data = [
        ["Statut:", payslip.get_status_display()],
        ["Méthode de paiement:", payslip.payment_method or "Non définie"],
        ["Généré le:", datetime.now().strftime('%d/%m/%Y à %H:%M')],
    ]

    footer_table = Table(footer_data, colWidths=[4*cm, 12*cm])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#6B7280')),
    ]))
    elements.append(footer_table)

    # Générer le PDF
    doc.build(elements)

    # Retourner le buffer
    buffer.seek(0)
    return buffer
