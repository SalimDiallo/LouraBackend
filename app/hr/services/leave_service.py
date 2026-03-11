"""
Leave Service - Service Layer pour la gestion des congés

Ce service encapsule toute la logique métier liée aux congés.
Il est indépendant des vues (Single Responsibility Principle).
"""
import logging
from typing import Optional, Dict, Any
from datetime import date
from django.db.models import QuerySet
from django.utils import timezone

logger = logging.getLogger(__name__)


class LeaveService:
    """
    Service pour les opérations métier sur les congés.
    
    Responsabilités:
    - Création de demandes de congé
    - Approbation/Rejet
    - Calculs statistiques
    """
    
    @staticmethod
    def get_leave_requests_for_organization(organization, status: str = None) -> QuerySet:
        """Retourne les demandes de congé d'une organisation."""
        from hr.models import LeaveRequest
        
        queryset = LeaveRequest.objects.filter(employee__organization=organization)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_leave_requests_for_employee(employee, status: str = None) -> QuerySet:
        """Retourne les demandes de congé d'un employé."""
        from hr.models import LeaveRequest
        
        queryset = LeaveRequest.objects.filter(employee=employee)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_pending_requests_for_manager(manager) -> QuerySet:
        """
        Retourne les demandes en attente pour les subordonnés d'un manager.
        """
        from hr.models import LeaveRequest, Employee
        
        # Récupérer les IDs des subordonnés
        subordinate_ids = Employee.objects.filter(
            manager=manager,
            is_active=True
        ).values_list('id', flat=True)
        
        return LeaveRequest.objects.filter(
            employee_id__in=subordinate_ids,
            status='pending'
        ).order_by('-created_at')
    
    @staticmethod
    def create_leave_request(
        employee,
        leave_type,
        start_date: date,
        end_date: date,
        reason: str = '',
        **kwargs
    ):
        """
        Crée une nouvelle demande de congé.
        
        Returns:
            LeaveRequest créée
        """
        from hr.models import LeaveRequest
        
        leave_request = LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status='pending',
            **kwargs
        )
        
        logger.info(f"Leave request created for {employee.email}: {leave_request.total_days} days")
        return leave_request
    
    @staticmethod
    def approve_leave_request(leave_request, approver, notes: str = '') -> bool:
        """
        Approuve une demande de congé.
        
        Args:
            leave_request: La demande à approuver
            approver: L'utilisateur qui approuve (Employee ou AdminUser)
            notes: Notes d'approbation
            
        Returns:
            bool: True si succès
        """
        if leave_request.status != 'pending':
            logger.warning(f"Cannot approve leave request {leave_request.id}: status is {leave_request.status}")
            return False
        
        leave_request.status = 'approved'
        leave_request.approval_date = timezone.now()
        leave_request.approval_notes = notes
        
        # Assigner l'approbateur
        if getattr(approver, 'user_type', None) == 'employee':
            leave_request.approver = approver
        elif getattr(approver, 'user_type', None) == 'admin':
            leave_request.approved_by_admin = approver
        
        leave_request.save()
        
        logger.info(f"Leave request {leave_request.id} approved by {approver}")
        return True
    
    @staticmethod
    def reject_leave_request(leave_request, rejector, notes: str = '') -> bool:
        """
        Rejette une demande de congé.
        """
        if leave_request.status != 'pending':
            logger.warning(f"Cannot reject leave request {leave_request.id}: status is {leave_request.status}")
            return False
        
        leave_request.status = 'rejected'
        leave_request.approval_date = timezone.now()
        leave_request.approval_notes = notes
        
        if getattr(rejector, 'user_type', None) == 'employee':
            leave_request.approver = rejector
        elif getattr(rejector, 'user_type', None) == 'admin':
            leave_request.approved_by_admin = rejector
        
        leave_request.save()
        
        logger.info(f"Leave request {leave_request.id} rejected by {rejector}")
        return True
    
    @staticmethod
    def cancel_leave_request(leave_request) -> bool:
        """Annule une demande de congé en attente."""
        if leave_request.status != 'pending':
            return False
        
        leave_request.delete()
        logger.info(f"Leave request {leave_request.id} cancelled")
        return True
    
    @staticmethod
    def get_organization_leave_stats(organization, year: int = None) -> Dict[str, Any]:
        """Retourne les statistiques de congés d'une organisation."""
        from hr.models import LeaveRequest
        from django.db.models import Count, Sum
        
        year = year or date.today().year
        
        requests = LeaveRequest.objects.filter(
            employee__organization=organization,
            start_date__year=year
        )
        
        by_status = requests.values('status').annotate(count=Count('id'))
        by_type = requests.values('leave_type__name').annotate(
            count=Count('id'),
            total_days=Sum('total_days')
        )
        
        return {
            'year': year,
            'total_requests': requests.count(),
            'by_status': {item['status']: item['count'] for item in by_status},
            'by_type': {
                item['leave_type__name']: {
                    'count': item['count'],
                    'days': item['total_days'] or 0
                }
                for item in by_type
            }
        }
