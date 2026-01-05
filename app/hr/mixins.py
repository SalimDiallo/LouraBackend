"""
HR Mixins - Patterns réutilisables spécifiques à l'app HR

Ces mixins étendent les mixins de base de core avec des fonctionnalités spécifiques HR.
"""
import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from core.mixins import BaseOrganizationViewSetMixin

logger = logging.getLogger(__name__)


class HRViewSetMixin(BaseOrganizationViewSetMixin):
    """
    Mixin de base pour les ViewSets HR.
    
    Ajoute:
    - Actions activate/deactivate avec décorateurs @action
    - Gestion des exports PDF
    """
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Active l'objet."""
        return super().activate(request, pk)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactive l'objet."""
        return super().deactivate(request, pk)


class EmployeeRelatedMixin:
    """
    Mixin pour les modèles liés à Employee (LeaveRequest, Payslip, etc.)
    
    Implémente le filtrage par employee__organization au lieu de organization.
    """
    organization_field = 'employee__organization'
    
    def _filter_for_employee(self, user, queryset):
        """
        Pour les employés, filtre aussi selon les droits HR.
        - HR Admin voit tout dans l'organisation
        - Manager voit ses subordonnés
        - Employé normal voit seulement ses propres données
        """
        if self.view_permission and user.has_permission(self.view_permission):
            # HR Admin ou gestionnaire avec permission - voit tout dans l'org
            if user.is_hr_admin() or (user.assigned_role and user.assigned_role.code == 'manager'):
                return queryset.filter(employee__organization=user.organization)
        
        # Manager voit ses subordonnés
        if hasattr(user, 'subordinates') and user.subordinates.exists():
            from django.db.models import Q
            subordinate_ids = user.subordinates.values_list('id', flat=True)
            return queryset.filter(
                Q(employee=user) | Q(employee_id__in=subordinate_ids)
            )
        
        # Employé normal voit seulement ses données
        return queryset.filter(employee=user)


class ApprovableMixin:
    """
    Mixin pour les modèles avec workflow d'approbation.
    
    Ajoute les actions approve/reject avec gestion des permissions.
    """
    
    approval_permission = None
    
    def _can_approve(self, user, obj):
        """Vérifie si l'utilisateur peut approuver l'objet."""
        from core.models import AdminUser
        from hr.models import Employee
        
        # Admin peut toujours approuver
        if getattr(user, 'user_type', None) == 'admin':
            return True
        
        if getattr(user, 'user_type', None) == 'employee':
            # Vérifier la permission
            if self.approval_permission and user.has_permission(self.approval_permission):
                return True
            
            # Manager peut approuver ses subordonnés
            if hasattr(obj, 'employee'):
                if obj.employee.manager == user:
                    return True
                if user.subordinates.filter(id=obj.employee.id).exists():
                    return True
        
        return False
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuve l'objet."""
        obj = self.get_object()
        
        if not self._can_approve(request.user, obj):
            return Response({
                'message': 'Vous n\'avez pas la permission d\'approuver'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # La logique d'approbation est déléguée au service
        return self._do_approve(obj, request)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejette l'objet."""
        obj = self.get_object()
        
        if not self._can_approve(request.user, obj):
            return Response({
                'message': 'Vous n\'avez pas la permission de rejeter'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return self._do_reject(obj, request)
    
    def _do_approve(self, obj, request):
        """Point d'extension pour l'approbation. À implémenter par les sous-classes."""
        raise NotImplementedError("Subclasses must implement _do_approve")
    
    def _do_reject(self, obj, request):
        """Point d'extension pour le rejet. À implémenter par les sous-classes."""
        raise NotImplementedError("Subclasses must implement _do_reject")


class PDFExportMixin:
    """
    Mixin pour les ViewSets avec export PDF.
    """
    
    pdf_generator_func = None
    pdf_filename_template = '{model}_{id}.pdf'
    
    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Exporte l'objet en PDF."""
        from django.http import HttpResponse
        
        if not self.pdf_generator_func:
            return Response({
                'message': 'Export PDF non configuré'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        
        obj = self.get_object()
        pdf_buffer = self.pdf_generator_func(obj)
        
        filename = self._get_pdf_filename(obj)
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def _get_pdf_filename(self, obj):
        """Génère le nom du fichier PDF."""
        model_name = obj.__class__.__name__
        obj_id = str(obj.id)[:8]
        return self.pdf_filename_template.format(model=model_name, id=obj_id)
