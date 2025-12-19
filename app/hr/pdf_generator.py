"""
Générateur de PDF pour les documents RH
Design sobre, professionnel et compact (1 page)
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime


# Couleurs professionnelles
PRIMARY_COLOR = colors.HexColor('#1a1a2e')
SECONDARY_COLOR = colors.HexColor('#4a4e69')
ACCENT_COLOR = colors.HexColor('#22577a')
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


def generate_payslip_pdf(payslip):
    """
    Génère un PDF compact pour une fiche de paie (1 page)
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
    org = payslip.employee.organization

    # En-tête
    elements.append(create_header_table(
        "BULLETIN DE PAIE",
        org.name,
        f"Réf: {str(payslip.id)[:8].upper()}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 4*mm))

    # Infos employé + Période (côte à côte)
    info_data = [
        ["EMPLOYÉ", "", "PÉRIODE", ""],
        [
            "Nom:",
            payslip.employee.get_full_name(),
            "Période:",
            payslip.payroll_period.name if payslip.payroll_period else "N/A"
        ],
        [
            "Matricule:",
            payslip.employee.employee_id or "N/A",
            "Du:",
            payslip.payroll_period.start_date.strftime('%d/%m/%Y') if payslip.payroll_period else "N/A"
        ],
        [
            "Poste:",
            payslip.employee.position.title if payslip.employee.position else "N/A",
            "Au:",
            payslip.payroll_period.end_date.strftime('%d/%m/%Y') if payslip.payroll_period else "N/A"
        ],
    ]

    info_table = Table(info_data, colWidths=[2.5*cm, 5.5*cm, 2.5*cm, 5.5*cm])
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
    elements.append(Spacer(1, 4*mm))

    # Tableau principal des revenus
    salary_data = [["LIBELLÉ", "MONTANT"]]
    
    # Salaire de base
    salary_data.append(["Salaire de base", f"{payslip.base_salary:,.0f} {payslip.currency}"])
    
    # Primes
    allowances = payslip.items.filter(is_deduction=False).order_by('name')
    for item in allowances:
        salary_data.append([f"  + {item.name}", f"{item.amount:,.0f} {payslip.currency}"])
    
    # Brut
    salary_data.append(["SALAIRE BRUT", f"{payslip.gross_salary:,.0f} {payslip.currency}"])
    
    # Déductions
    deductions = payslip.items.filter(is_deduction=True).order_by('name')
    if deductions.exists():
        for item in deductions:
            salary_data.append([f"  - {item.name}", f"{item.amount:,.0f} {payslip.currency}"])
        salary_data.append(["TOTAL DÉDUCTIONS", f"-{payslip.total_deductions:,.0f} {payslip.currency}"])
    
    # Net
    salary_data.append(["NET À PAYER", f"{payslip.net_salary:,.0f} {payslip.currency}"])

    salary_table = Table(salary_data, colWidths=[12*cm, 5*cm])
    
    table_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    
    # Ligne brut en gras
    brut_idx = 2 + allowances.count()
    table_style.extend([
        ('FONTNAME', (0, brut_idx), (-1, brut_idx), 'Helvetica-Bold'),
        ('BACKGROUND', (0, brut_idx), (-1, brut_idx), colors.HexColor('#e8f5e9')),
    ])
    
    # Ligne net en surbrillance
    table_style.extend([
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), ACCENT_COLOR),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
    ])
    
    salary_table.setStyle(TableStyle(table_style))
    elements.append(salary_table)
    elements.append(Spacer(1, 6*mm))

    # Pied de page compact
    footer_data = [
        [f"Statut: {payslip.get_status_display()}", f"Méthode: {payslip.payment_method or 'Non définie'}", f"Généré le {datetime.now().strftime('%d/%m/%Y')}"]
    ]
    footer_table = Table(footer_data, colWidths=[6*cm, 6*cm, 5*cm])
    footer_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('TEXTCOLOR', (0, 0), (-1, -1), SECONDARY_COLOR),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(footer_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_contract_pdf(contract):
    """
    Génère un PDF compact pour un contrat (1 page)
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
    employee = contract.employee
    org = employee.organization

    # Types de contrat
    contract_types = {
        'permanent': 'CONTRAT À DURÉE INDÉTERMINÉE (CDI)',
        'temporary': 'CONTRAT À DURÉE DÉTERMINÉE (CDD)',
        'contract': 'CONTRAT DE TRAVAIL',
        'internship': 'CONVENTION DE STAGE',
        'freelance': 'CONTRAT FREELANCE',
    }

    salary_periods = {
        'hourly': 'horaire',
        'daily': 'journalier',
        'monthly': 'mensuel',
        'annual': 'annuel',
    }

    # En-tête
    elements.append(create_header_table(
        contract_types.get(contract.contract_type, 'CONTRAT DE TRAVAIL'),
        org.name,
        contract.start_date.strftime('%d/%m/%Y')
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 6*mm))

    # Parties
    parties_text = f"""
    <b>Entre</b> {org.name}, représenté par son représentant légal, ci-après dénommé "l'Employeur",<br/><br/>
    <b>Et</b> {employee.get_full_name()}, ci-après dénommé "l'Employé".
    """
    elements.append(Paragraph(parties_text, styles['normal']))
    elements.append(Spacer(1, 4*mm))

    # Tableau des conditions
    conditions_data = [
        ["CONDITIONS DU CONTRAT", ""],
        ["Type de contrat", contract_types.get(contract.contract_type, contract.contract_type)],
        ["Date d'effet", contract.start_date.strftime('%d/%m/%Y')],
        ["Date de fin", contract.end_date.strftime('%d/%m/%Y') if contract.end_date else "Indéterminée"],
        ["Poste occupé", employee.position.title if employee.position else "À définir"],
        ["Département", employee.department.name if employee.department else "N/A"],
        ["Durée hebdomadaire", f"{contract.hours_per_week} heures"],
    ]

    cond_table = Table(conditions_data, colWidths=[6*cm, 11*cm])
    cond_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(cond_table)
    elements.append(Spacer(1, 4*mm))

    # Rémunération
    salary_period = salary_periods.get(contract.salary_period, contract.salary_period)
    remun_data = [
        ["RÉMUNÉRATION", ""],
        ["Salaire brut", f"{contract.base_salary:,.0f} {contract.currency} ({salary_period})"],
    ]

    remun_table = Table(remun_data, colWidths=[6*cm, 11*cm])
    remun_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(remun_table)
    elements.append(Spacer(1, 6*mm))

    # Clauses si présentes
    if contract.description:
        elements.append(Paragraph("<b>CLAUSES PARTICULIÈRES</b>", styles['heading']))
        elements.append(Paragraph(contract.description, styles['small']))
        elements.append(Spacer(1, 4*mm))

    # Signatures
    elements.append(Spacer(1, 8*mm))
    sig_data = [
        ["L'EMPLOYEUR", "L'EMPLOYÉ"],
        ["", ""],
        ["Date: _______________", "Date: _______________"],
        ["Signature:", "Lu et approuvé, signature:"],
    ]

    sig_table = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 25),
    ]))
    elements.append(sig_table)

    # Footer
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_leave_request_pdf(leave_request):
    """
    Génère un PDF compact pour une demande de congé (1 page)
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
    employee = leave_request.employee
    org = employee.organization

    status_labels = {
        'pending': 'EN ATTENTE',
        'approved': 'APPROUVÉE',
        'rejected': 'REJETÉE',
        'cancelled': 'ANNULÉE',
    }

    # En-tête
    elements.append(create_header_table(
        "DEMANDE DE CONGÉ",
        org.name,
        f"Réf: {str(leave_request.id)[:8].upper()}"
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    elements.append(Spacer(1, 6*mm))

    # Statut
    status = leave_request.status
    status_color = colors.HexColor('#ffc107') if status == 'pending' else (
        colors.HexColor('#28a745') if status == 'approved' else colors.HexColor('#dc3545')
    )
    status_data = [[status_labels.get(status, status)]]
    status_table = Table(status_data, colWidths=[17*cm])
    status_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BACKGROUND', (0, 0), (-1, -1), status_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white if status != 'pending' else PRIMARY_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 6*mm))

    # Infos demandeur
    info_data = [
        ["DEMANDEUR", ""],
        ["Nom complet", employee.get_full_name()],
        ["Matricule", employee.employee_id or "N/A"],
        ["Département", employee.department.name if employee.department else "N/A"],
        ["Poste", employee.position.title if employee.position else "N/A"],
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

    # Détails du congé
    leave_data = [
        ["DÉTAILS DU CONGÉ", ""],
        ["Type de congé", leave_request.leave_type.name if leave_request.leave_type else "N/A"],
        ["Date de début", leave_request.start_date.strftime('%d/%m/%Y')],
        ["Date de fin", leave_request.end_date.strftime('%d/%m/%Y')],
        ["Durée totale", f"{leave_request.total_days} jour(s)"],
        ["Motif", leave_request.reason or "Non spécifié"],
    ]

    leave_table = Table(leave_data, colWidths=[5*cm, 12*cm])
    leave_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(leave_table)
    elements.append(Spacer(1, 6*mm))

    # Approbation si applicable
    if leave_request.status in ['approved', 'rejected'] and hasattr(leave_request, 'approver'):
        approval_data = [
            ["DÉCISION", ""],
            ["Décision", "APPROUVÉE" if leave_request.status == 'approved' else "REJETÉE"],
            ["Par", leave_request.approver.get_full_name() if leave_request.approver else "N/A"],
            ["Date", leave_request.approval_date.strftime('%d/%m/%Y') if leave_request.approval_date else "N/A"],
            ["Commentaire", leave_request.approval_notes or "-"],
        ]

        approval_table = Table(approval_data, colWidths=[5*cm, 12*cm])
        approval_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745') if leave_request.status == 'approved' else colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 1), (0, -1), SECONDARY_COLOR),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(approval_table)

    # Footer
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
