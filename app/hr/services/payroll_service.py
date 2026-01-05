"""
Payroll Service - Service Layer pour la gestion de la paie

Ce service encapsule toute la logique métier liée à la paie.
Il est indépendant des vues (Single Responsibility Principle).
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import date
from decimal import Decimal
from django.db.models import QuerySet, Sum

logger = logging.getLogger(__name__)


class PayrollService:
    """
    Service pour les opérations métier sur la paie.
    
    Responsabilités:
    - Gestion des périodes de paie
    - Génération des fiches de paie
    - Gestion des avances
    - Calculs et statistiques
    """
    
    @staticmethod
    def get_payroll_periods_for_organization(organization, status: str = None) -> QuerySet:
        """Retourne les périodes de paie d'une organisation."""
        from hr.models import PayrollPeriod
        
        queryset = PayrollPeriod.objects.filter(organization=organization)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-start_date')
    
    @staticmethod
    def create_payroll_period(
        organization,
        name: str,
        start_date: date,
        end_date: date,
        payment_date: date = None,
        **kwargs
    ):
        """Crée une nouvelle période de paie."""
        from hr.models import PayrollPeriod
        
        period = PayrollPeriod.objects.create(
            organization=organization,
            name=name,
            start_date=start_date,
            end_date=end_date,
            payment_date=payment_date or end_date,
            status='draft',
            **kwargs
        )
        
        logger.info(f"Payroll period '{name}' created for organization '{organization.name}'")
        return period
    
    @staticmethod
    def generate_payslips_for_period(payroll_period, employees: QuerySet = None) -> int:
        """
        Génère les fiches de paie pour une période.
        
        Args:
            payroll_period: La période de paie
            employees: QuerySet d'employés (si None, tous les actifs)
            
        Returns:
            Nombre de fiches créées
        """
        from hr.models import Payslip, Employee, Contract
        
        if employees is None:
            employees = Employee.objects.filter(
                organization=payroll_period.organization,
                is_active=True
            )
        
        created = 0
        for employee in employees:
            # Vérifier si une fiche existe déjà
            if Payslip.objects.filter(
                employee=employee,
                payroll_period=payroll_period
            ).exists():
                continue
            
            # Récupérer le contrat actif
            contract = Contract.objects.filter(
                employee=employee,
                is_active=True
            ).first()
            
            if not contract:
                logger.warning(f"No active contract for employee {employee.email}")
                continue
            
            # Créer la fiche de paie
            payslip = Payslip.objects.create(
                employee=employee,
                payroll_period=payroll_period,
                base_salary=contract.base_salary,
                currency=contract.currency,
                status='draft'
            )
            payslip.calculate_totals()
            created += 1
        
        logger.info(f"Generated {created} payslips for period '{payroll_period.name}'")
        return created
    
    @staticmethod
    def process_payroll_period(payroll_period) -> bool:
        """
        Traite une période de paie (passe au statut processed).
        """
        from hr.models import PayrollPeriod
        
        if payroll_period.status not in ['draft', 'pending']:
            logger.warning(f"Cannot process period {payroll_period.id}: status is {payroll_period.status}")
            return False
        
        # Mettre à jour les fiches de paie
        payroll_period.payslips.filter(status='draft').update(status='processed')
        payroll_period.status = 'processed'
        payroll_period.save(update_fields=['status'])
        
        logger.info(f"Payroll period '{payroll_period.name}' processed")
        return True
    
    @staticmethod
    def close_payroll_period(payroll_period) -> bool:
        """Clôture une période de paie."""
        if payroll_period.status != 'processed':
            return False
        
        payroll_period.payslips.filter(status='processed').update(status='paid')
        payroll_period.status = 'closed'
        payroll_period.save(update_fields=['status'])
        
        logger.info(f"Payroll period '{payroll_period.name}' closed")
        return True
    
    @staticmethod
    def get_payslips_for_employee(employee, year: int = None) -> QuerySet:
        """Retourne les fiches de paie d'un employé."""
        from hr.models import Payslip
        
        queryset = Payslip.objects.filter(employee=employee)
        if year:
            queryset = queryset.filter(payroll_period__start_date__year=year)
        return queryset.order_by('-payroll_period__start_date')
    
    @staticmethod
    def create_advance(
        employee,
        amount: Decimal,
        reason: str = '',
        requested_date: date = None,
        **kwargs
    ):
        """Crée une demande d'avance sur salaire."""
        from hr.models import PayrollAdvance
        
        advance = PayrollAdvance.objects.create(
            employee=employee,
            amount=amount,
            reason=reason,
            requested_date=requested_date or date.today(),
            status='pending',
            **kwargs
        )
        
        logger.info(f"Advance request created for {employee.email}: {amount}")
        return advance
    
    @staticmethod
    def approve_advance(advance, approver, notes: str = '') -> bool:
        """Approuve une demande d'avance."""
        from hr.models import Employee
        from core.models import AdminUser
        from django.utils import timezone
        
        if advance.status != 'pending':
            return False
        
        advance.status = 'approved'
        advance.approval_date = timezone.now()
        advance.approval_notes = notes
        
        if getattr(approver, 'user_type', None) == 'employee':
            advance.approved_by = approver
        elif getattr(approver, 'user_type', None) == 'admin':
            advance.approved_by_admin = approver
        
        advance.save()
        logger.info(f"Advance {advance.id} approved by {approver}")
        return True
    
    @staticmethod
    def pay_advance(advance) -> bool:
        """Marque une avance comme payée."""
        if advance.status != 'approved':
            return False
        
        advance.status = 'paid'
        advance.payment_date = date.today()
        advance.save(update_fields=['status', 'payment_date'])
        
        logger.info(f"Advance {advance.id} marked as paid")
        return True
    
    @staticmethod
    def deduct_advance_from_payslip(advance, payslip) -> bool:
        """Déduit une avance d'une fiche de paie."""
        from hr.models import PayslipItem
        
        if advance.status != 'paid':
            return False
        
        # Créer un item de déduction
        PayslipItem.objects.create(
            payslip=payslip,
            name=f"Remboursement avance du {advance.requested_date}",
            amount=advance.amount,
            is_deduction=True
        )
        
        advance.payslip = payslip
        advance.status = 'deducted'
        advance.save(update_fields=['payslip', 'status'])
        
        # Recalculer les totaux
        payslip.calculate_totals()
        
        logger.info(f"Advance {advance.id} deducted from payslip {payslip.id}")
        return True
    
    @staticmethod
    def get_organization_payroll_stats(organization, year: int = None) -> Dict[str, Any]:
        """Retourne les statistiques de paie d'une organisation."""
        from hr.models import Payslip, PayrollPeriod
        
        year = year or date.today().year
        
        periods = PayrollPeriod.objects.filter(
            organization=organization,
            start_date__year=year
        )
        
        payslips = Payslip.objects.filter(
            payroll_period__in=periods
        )
        
        totals = payslips.aggregate(
            total_net=Sum('net_salary'),
            total_gross=Sum('gross_salary'),
            total_deductions=Sum('total_deductions')
        )
        
        return {
            'year': year,
            'periods_count': periods.count(),
            'payslips_count': payslips.count(),
            'total_net_salary': float(totals['total_net'] or 0),
            'total_gross_salary': float(totals['total_gross'] or 0),
            'total_deductions': float(totals['total_deductions'] or 0),
            'by_status': {
                status: payslips.filter(status=status).count()
                for status in ['draft', 'processed', 'paid']
            }
        }
