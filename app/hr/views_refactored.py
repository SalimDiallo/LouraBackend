"""
Views Refactored - Exemples de ViewSets utilisant les nouveaux patterns

Ce fichier montre comment refactorer les ViewSets existants en utilisant:
- Service Layer Pattern
- Mixin Pattern
- Single Responsibility Principle

IMPORTANT: Ce fichier est une démonstration. Pour migrer progressivement,
les ViewSets existants dans views.py peuvent être remplacés un par un
en important depuis ce fichier.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from hr.mixins import HRViewSetMixin, EmployeeRelatedMixin, ApprovableMixin, PDFExportMixin
from hr.services import EmployeeService, LeaveService, PayrollService
from hr.permissions import (
    IsAdminUserOrEmployee,
    RequiresEmployeePermission,
    RequiresLeavePermission,
    RequiresPayrollPermission,
    IsManagerOrHRAdmin,
)
from hr.models import Employee, LeaveRequest, LeaveBalance, Payslip, PayrollPeriod
from hr.serializers import (
    EmployeeSerializer,
    EmployeeCreateSerializer,
    EmployeeListSerializer,
    EmployeeUpdateSerializer,
    LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    PayslipSerializer,
    PayslipCreateSerializer,
)


class EmployeeViewSetRefactored(HRViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des employés - VERSION REFACTORÉE.
    
    Utilise:
    - HRViewSetMixin pour le filtrage par organisation
    - EmployeeService pour la logique métier
    
    Avant: ~150 lignes
    Après: ~50 lignes (70% de réduction)
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresEmployeePermission]
    
    # Configuration du mixin
    organization_field = 'organization'
    view_permission = 'can_view_employee'
    create_permission = 'can_create_employee'
    activation_permission = 'can_activate_employee'
    
    def get_serializer_class(self):
        """Choisit le serializer selon l'action."""
        serializer_map = {
            'create': EmployeeCreateSerializer,
            'update': EmployeeUpdateSerializer,
            'partial_update': EmployeeUpdateSerializer,
            'list': EmployeeListSerializer,
        }
        return serializer_map.get(self.action, EmployeeSerializer)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des employés."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({
                'error': 'Organisation requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        stats = EmployeeService.get_employee_stats(organization)
        return Response(stats)


class LeaveRequestViewSetRefactored(
    EmployeeRelatedMixin,
    ApprovableMixin,
    PDFExportMixin,
    HRViewSetMixin,
    viewsets.ModelViewSet
):
    """
    ViewSet pour la gestion des demandes de congé - VERSION REFACTORÉE.
    
    Utilise:
    - EmployeeRelatedMixin pour le filtrage par employee__organization
    - ApprovableMixin pour les actions approve/reject
    - PDFExportMixin pour l'export PDF
    - LeaveService pour la logique métier
    
    Avant: ~200 lignes
    Après: ~80 lignes (60% de réduction)
    """
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresLeavePermission]
    
    # Configuration des mixins
    view_permission = 'can_view_leave'
    create_permission = 'can_create_leave'
    approval_permission = 'can_approve_leave'
    
    # Configuration PDF
    pdf_filename_template = 'Conge_{employee}_{date}.pdf'
    
    @property
    def pdf_generator_func(self):
        """Importer le générateur PDF à la demande."""
        from hr.pdf_generator import generate_leave_request_pdf
        return generate_leave_request_pdf
    
    def _get_pdf_filename(self, obj):
        """Génère le nom du fichier PDF pour une demande de congé."""
        employee_name = obj.employee.get_full_name().replace(' ', '_')
        date_str = obj.start_date.strftime('%Y%m%d')
        return f'Conge_{employee_name}_{date_str}.pdf'
    
    def perform_create(self, serializer):
        """Crée une demande de congé via le service."""
        from hr.models import Employee
        from core.models import AdminUser
        
        user = self.request.user
        
        if isinstance(user, Employee):
            if not user.has_permission('can_create_leave'):
                from rest_framework import serializers as drf_serializers
                raise drf_serializers.ValidationError({'permission': 'Permission refusée'})
            
            # Créer via le service
            leave_request = LeaveService.create_leave_request(
                employee=user,
                leave_type=serializer.validated_data['leave_type'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                reason=serializer.validated_data.get('reason', ''),
                start_half_day=serializer.validated_data.get('start_half_day', False),
                end_half_day=serializer.validated_data.get('end_half_day', False),
            )
            serializer.instance = leave_request
            
        elif isinstance(user, AdminUser):
            employee_id = self.request.data.get('employee')
            if not employee_id:
                from rest_framework import serializers as drf_serializers
                raise drf_serializers.ValidationError({
                    'employee': 'L\'employé est requis'
                })
            
            employee = Employee.objects.filter(
                id=employee_id,
                organization__admin=user
            ).first()
            
            if not employee:
                from rest_framework import serializers as drf_serializers
                raise drf_serializers.ValidationError({
                    'employee': 'Employé non trouvé'
                })
            
            leave_request = LeaveService.create_leave_request(
                employee=employee,
                leave_type=serializer.validated_data['leave_type'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                reason=serializer.validated_data.get('reason', ''),
            )
            serializer.instance = leave_request
    
    def _do_approve(self, obj, request):
        """Approuve une demande de congé via le service."""
        notes = request.data.get('approval_notes', '')
        success = LeaveService.approve_leave_request(obj, request.user, notes)
        
        if success:
            return Response({'message': 'Demande approuvée'})
        return Response({
            'message': 'Impossible d\'approuver cette demande'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def _do_reject(self, obj, request):
        """Rejette une demande de congé via le service."""
        notes = request.data.get('approval_notes', '')
        success = LeaveService.reject_leave_request(obj, request.user, notes)
        
        if success:
            return Response({'message': 'Demande rejetée'})
        return Response({
            'message': 'Impossible de rejeter cette demande'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des congés."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({
                'error': 'Organisation requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        year = request.query_params.get('year')
        stats = LeaveService.get_organization_leave_stats(
            organization,
            year=int(year) if year else None
        )
        return Response(stats)


class PayrollPeriodViewSetRefactored(HRViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des périodes de paie - VERSION REFACTORÉE.
    
    Utilise:
    - HRViewSetMixin pour le filtrage par organisation
    - PayrollService pour la logique métier
    """
    queryset = PayrollPeriod.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresPayrollPermission]
    
    # Configuration du mixin
    view_permission = 'can_view_payroll'
    create_permission = 'can_create_payroll'
    
    @action(detail=True, methods=['post'])
    def generate_payslips(self, request, pk=None):
        """Génère les fiches de paie pour la période."""
        from hr.models import Employee
        
        period = self.get_object()
        
        # Optionnel: filtrer les employés
        employee_ids = request.data.get('employee_ids', [])
        if employee_ids:
            employees = Employee.objects.filter(
                id__in=employee_ids,
                organization=period.organization,
                is_active=True
            )
        else:
            employees = None
        
        count = PayrollService.generate_payslips_for_period(period, employees)
        return Response({
            'message': f'{count} fiches de paie générées'
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Traite la période de paie."""
        period = self.get_object()
        success = PayrollService.process_payroll_period(period)
        
        if success:
            return Response({'message': 'Période traitée'})
        return Response({
            'message': 'Impossible de traiter cette période'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Clôture la période de paie."""
        period = self.get_object()
        success = PayrollService.close_payroll_period(period)
        
        if success:
            return Response({'message': 'Période clôturée'})
        return Response({
            'message': 'Impossible de clôturer cette période'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques de paie."""
        organization = self.get_organization_from_request(raise_exception=False)
        if not organization:
            return Response({
                'error': 'Organisation requise'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        year = request.query_params.get('year')
        stats = PayrollService.get_organization_payroll_stats(
            organization,
            year=int(year) if year else None
        )
        return Response(stats)
