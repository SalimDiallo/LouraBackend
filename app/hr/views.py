"""
HR Views - ViewSets pour la gestion des ressources humaines

Ce module contient les ViewSets pour :
- Employés (CRUD, activation, permissions)
- Départements et Postes
- Contrats
- Congés (types, soldes, demandes)
- Paie (périodes, fiches, avances)
- Pointages (présence, QR)
- Rôles et Permissions
"""
import logging
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Models
from core.models import Organization, AdminUser
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip, PayrollAdvance, Permission, Role, Attendance
)

# Serializers
from .serializers import (
    EmployeeSerializer, EmployeeCreateSerializer, EmployeeListSerializer,
    EmployeeUpdateSerializer, EmployeeChangePasswordSerializer,
    DepartmentSerializer, PositionSerializer, ContractSerializer,
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    PayrollPeriodSerializer, PayslipSerializer, PayslipCreateSerializer,
    PayrollAdvanceSerializer, PayrollAdvanceCreateSerializer, PayrollAdvanceListSerializer,
    PayrollAdvanceApprovalSerializer,
    PermissionSerializer, RoleSerializer, RoleListSerializer, RoleCreateSerializer,
    AttendanceSerializer, AttendanceCreateSerializer, AttendanceCheckInSerializer,
    AttendanceCheckOutSerializer, AttendanceApprovalSerializer, AttendanceStatsSerializer
)

# Permissions
from .permissions import (
    IsHRAdminOrReadOnly, IsHRAdmin,
    IsManagerOrHRAdmin, IsAdminUserOrEmployee,
    RequiresPermission, RequiresCRUDPermission, CanAccessOwnOrManage,
    IsDepartmentHeadOrHR, IsManagerOfEmployee,
    RequiresEmployeePermission, RequiresDepartmentPermission,
    RequiresPositionPermission, RequiresContractPermission,
    RequiresLeavePermission, RequiresPayrollPermission,
    RequiresAttendancePermission, RequiresRolePermission
)

# Mixins - Design Patterns pour réduire la duplication
from core.mixins import (
    OrganizationResolverMixin,
    OrganizationQuerySetMixin,
    OrganizationCreateMixin,
    BaseOrganizationViewSetMixin,
)

# Services - Logique métier séparée (Service Layer Pattern)
from .services import EmployeeService, LeaveService, PayrollService

# Utils centralisés
from authentication.utils import convert_uuids_to_strings

# Constants - Permissions et Rôles prédéfinis sont définis dans constants.py
# Usage: from hr.constants import PERMISSIONS, PREDEFINED_ROLES

# Module logger
logger = logging.getLogger(__name__)


# -------------------------------
# EMPLOYEE AUTHENTICATION VIEWS
# -------------------------------
# EmployeeLoginView, EmployeeRefreshTokenView, EmployeeLogoutView, and EmployeeMeView
# have been moved to authentication app


class EmployeeChangePasswordView(APIView):
    """Change employee password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not isinstance(request.user, Employee):
            return Response({
                'error': 'Utilisateur non autorise'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = EmployeeChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({
                'message': 'Mot de passe modifie avec succes'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# EMPLOYEE MANAGEMENT VIEWS
# -------------------------------

class EmployeeViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des employés.
    
    Utilise BaseOrganizationViewSetMixin pour:
    - Filtrage automatique par organisation
    - Création avec organisation automatique
    - Actions activate/deactivate
    """
    queryset = Employee.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresEmployeePermission]
    
    # Configuration du mixin
    organization_field = 'organization'
    view_permission = 'can_view_employee'
    create_permission = 'can_create_employee'
    activation_permission = 'can_activate_employee'

    def get_serializer_class(self):
        """Choisit le serializer approprié selon l'action."""
        serializer_map = {
            'create': EmployeeCreateSerializer,
            'update': EmployeeUpdateSerializer,
            'partial_update': EmployeeUpdateSerializer,
            'list': EmployeeListSerializer,
        }
        return serializer_map.get(self.action, EmployeeSerializer)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Active un employé."""
        return super().activate(request, pk)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactive un employé."""
        return super().deactivate(request, pk)

# -------------------------------
# HR CONFIGURATION VIEWS
# -------------------------------

class DepartmentViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des départements.
    
    Utilise BaseOrganizationViewSetMixin pour le filtrage et création automatiques.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresDepartmentPermission]
    
    # Configuration du mixin
    organization_field = 'organization'
    view_permission = 'can_view_department'
    create_permission = 'can_create_department'


class PositionViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des postes.
    
    Utilise BaseOrganizationViewSetMixin pour le filtrage et création automatiques.
    """
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAdminUserOrEmployee]
    
    # Configuration du mixin
    organization_field = 'organization'
    view_permission = 'can_view_position'
    create_permission = 'can_create_position'


class ContractViewSet(BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des contrats.
    
    Utilise BaseOrganizationViewSetMixin pour le filtrage et création automatiques.
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresContractPermission]
    
    # Configuration du mixin - les contrats sont liés à employee.organization
    organization_field = 'employee__organization'
    view_permission = 'can_view_contract'
    create_permission = 'can_create_contract'

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Contract.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_view_contract"):
                if user.is_hr_admin():
                    return Contract.objects.filter(employee__organization=user.organization)
                return Contract.objects.filter(employee=user)
        return Contract.objects.none()

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export a contract as PDF"""
        from .pdf_generator import generate_contract_pdf
        
        contract = self.get_object()
        pdf_buffer = generate_contract_pdf(contract)
        
        employee_name = contract.employee.get_full_name().replace(' ', '_')
        contract_type = contract.contract_type.upper()
        filename = f"Contrat_{contract_type}_{employee_name}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# -------------------------------
# LEAVE MANAGEMENT VIEWS
# -------------------------------

class LeaveTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave types"""
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresLeavePermission]

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveType.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_view_leave"):
                return LeaveType.objects.filter(organization=user.organization)
        return LeaveType.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_subdomain = self.request.query_params.get('organization_subdomain')

            if org_subdomain:
                try:
                    organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                except Organization.DoesNotExist:
                    raise serializers.ValidationError({
                        'organization': f'Organisation "{org_subdomain}" non trouvée'
                    })
            else:
                org_id = self.request.data.get('organization')
                if not org_id:
                    raise serializers.ValidationError({
                        'organization': 'Organisation requise'
                    })
                organization = Organization.objects.filter(id=org_id, admin=user).first()
                if not organization:
                    raise serializers.ValidationError({
                        'organization': 'Organisation non trouvée ou accès refusé'
                    })
        elif isinstance(user, Employee):
            if not user.has_permission("can_manage_leave_types"):
                raise serializers.ValidationError({'permission': 'Permission refusée'})
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorisé'})

        serializer.save(organization=organization)


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave balances"""
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAdminUserOrEmployee, CanAccessOwnOrManage.for_resource('leave', 'can_manage_leave_balances')]

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveBalance.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_manage_leave_balances") or user.is_hr_admin():
                return LeaveBalance.objects.filter(employee__organization=user.organization)
            return LeaveBalance.objects.filter(employee=user)
        return LeaveBalance.objects.none()


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave requests"""
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresLeavePermission]

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveRequest.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_view_leave"):
                # HR admin or manager can see all requests in organization
                if user.is_hr_admin():
                    return LeaveRequest.objects.filter(employee__organization=user.organization)
                # Check if user is a manager (has subordinates or manager role)
                if user.assigned_role and user.assigned_role.code == 'manager':
                    return LeaveRequest.objects.filter(employee__organization=user.organization)
                if user.subordinates.exists():
                    return LeaveRequest.objects.filter(employee__organization=user.organization)
                # Regular employees only see their own requests
                return LeaveRequest.objects.filter(employee=user)
        return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        if isinstance(self.request.user, Employee):
            if not self.request.user.has_permission('can_create_leave'):
                raise serializers.ValidationError({'permission': 'Permission refusée'})
            leave_request = serializer.save(employee=self.request.user)
        elif isinstance(self.request.user, AdminUser):
            # AdminUser creating a leave request for an employee
            employee_id = self.request.data.get('employee')
            if not employee_id:
                raise serializers.ValidationError({
                    'employee': 'L\'employé est requis pour créer une demande de congé'
                })
            try:
                employee = Employee.objects.get(id=employee_id)
                if not self.request.user.organizations.filter(id=employee.organization_id).exists():
                    raise serializers.ValidationError({
                        'employee': 'Vous n\'avez pas accès à cet employé'
                    })
                leave_request = serializer.save(employee=employee)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    'employee': 'Employé introuvable'
                })
        else:
            raise serializers.ValidationError({
                'user': 'Seuls les employés et administrateurs peuvent créer des demandes'
            })

        # Mettre à jour le solde de congé (pending_days)
        year = leave_request.start_date.year
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=year
        )
        balance.pending_days += leave_request.total_days
        balance.save()

    def perform_destroy(self, instance):
        if instance.status == 'pending':
            year = instance.start_date.year
            balance = LeaveBalance.objects.filter(
                employee=instance.employee,
                leave_type=instance.leave_type,
                year=year
            ).first()
            if balance:
                balance.pending_days -= instance.total_days
                balance.save()
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrHRAdmin])
    def approve(self, request, pk=None):
        # requires can_approve_leave
        leave_request = self.get_object()
        serializer = LeaveRequestApprovalSerializer(data=request.data)

        if serializer.is_valid():
            leave_request.status = 'approved'
            leave_request.approver = request.user
            leave_request.approval_date = timezone.now()
            leave_request.approval_notes = serializer.validated_data.get('approval_notes', '')
            leave_request.save()

            year = leave_request.start_date.year
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=year
            )
            balance.used_days += leave_request.total_days
            balance.pending_days -= leave_request.total_days
            balance.save()

            return Response({'message': 'Demande approuvee'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrHRAdmin])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        serializer = LeaveRequestApprovalSerializer(data=request.data)

        if serializer.is_valid():
            leave_request.status = 'rejected'
            leave_request.approver = request.user
            leave_request.approval_date = timezone.now()
            leave_request.approval_notes = serializer.validated_data.get('approval_notes', '')
            leave_request.save()

            year = leave_request.start_date.year
            balance = LeaveBalance.objects.filter(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type,
                year=year
            ).first()
            if balance:
                balance.pending_days -= leave_request.total_days
                balance.save()

            return Response({'message': 'Demande rejetee'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export a leave request as PDF"""
        from .pdf_generator import generate_leave_request_pdf
        
        leave_request = self.get_object()
        pdf_buffer = generate_leave_request_pdf(leave_request)
        
        employee_name = leave_request.employee.get_full_name().replace(' ', '_')
        filename = f"Conge_{employee_name}_{leave_request.start_date.strftime('%Y%m%d')}.pdf"
        
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

# -------------------------------
# PAYROLL VIEWS
# -------------------------------

class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payroll periods"""
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresPayrollPermission]

    def get_queryset(self):
        user = self.request.user

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return PayrollPeriod.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_view_payroll"):
                return PayrollPeriod.objects.filter(organization=user.organization)
        return PayrollPeriod.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if isinstance(user, AdminUser):
            # Essayer d'abord avec organization_subdomain (depuis query params)
            org_subdomain = self.request.query_params.get('organization_subdomain')

            if org_subdomain:
                logger.info(f"Looking for organization with subdomain: {org_subdomain}")
                try:
                    organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                    logger.info(f"Organization found: {organization.name}")
                except Organization.DoesNotExist:
                    logger.error(f"Organization with subdomain {org_subdomain} not found for user {user.email}")
                    raise serializers.ValidationError({
                        'organization': f'Organisation avec le subdomain "{org_subdomain}" non trouvée'
                    })
            else:
                # Fallback: essayer avec organization ID depuis request.data
                org_id = self.request.data.get('organization')
                logger.info(f"Looking for organization with ID: {org_id}")

                if not org_id:
                    logger.error("No organization_subdomain or organization ID provided")
                    raise serializers.ValidationError({
                        'organization': 'L\'identifiant de l\'organisation est requis (organization_subdomain ou organization)'
                    })

                organization = Organization.objects.filter(id=org_id, admin=user).first()
                if not organization:
                    logger.error(f"Organization with ID {org_id} not found for user {user.email}")
                    raise serializers.ValidationError({
                        'organization': 'Organisation non trouvée ou accès refusé'
                    })

        elif isinstance(user, Employee):
            if not user.has_permission("can_create_payroll"):
                logger.warning(f"Employee {user.email} lacks permission to create payroll")
                raise serializers.ValidationError({'permission': 'Permission refusée'})
            organization = user.organization
            logger.info(f"Using employee's organization: {organization.name}")
        else:
            logger.error(f"Unauthorized user type: {type(user)}")
            raise serializers.ValidationError({'user': 'Type d\'utilisateur non autorisé'})

        logger.info(f"Creating payroll period for organization: {organization.name}")
        serializer.save(organization=organization)


class PayslipViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payslips"""
    permission_classes = [IsAdminUserOrEmployee, CanAccessOwnOrManage.for_resource('payroll', 'can_view_payroll')]

    def get_serializer_class(self):
        if self.action == 'create':
            return PayslipCreateSerializer
        return PayslipSerializer

    def get_queryset(self):
        user = self.request.user

        # Base queryset selon le type d'utilisateur
        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = Payslip.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.has_permission("can_view_payroll") or user.is_hr_admin():
                queryset = Payslip.objects.filter(employee__organization=user.organization)
            else:
                queryset = Payslip.objects.filter(employee=user)
        else:
            queryset = Payslip.objects.none()

        # Filtrage supplémentaire par paramètres de requête
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsHRAdmin])
    def mark_as_paid(self, request, pk=None):
        payslip = self.get_object()
        payslip.status = 'paid'
        payslip.payment_date = timezone.now().date()
        payslip.payment_reference = request.data.get('payment_reference', '')
        payslip.save()

        return Response({'message': 'Marque comme paye'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminUserOrEmployee])
    def export_pdf(self, request, pk=None):
        from .pdf_generator import generate_payslip_pdf
        payslip = self.get_object()
        pdf_buffer = generate_payslip_pdf(payslip)
        filename = f"Fiche_Paie_{payslip.employee.get_full_name().replace(' ', '_')}_{payslip.payroll_period.name.replace(' ', '_')}.pdf"
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'], permission_classes=[IsHRAdmin])
    def generate_for_period(self, request):
        """Génération intelligente de fiches de paie avec déduction automatique des avances"""

        payroll_period_id = request.data.get('payroll_period')
        employee_filters = request.data.get('employee_filters', {})
        auto_deduct_advances = request.data.get('auto_deduct_advances', True)  # ✨ Nouveau paramètre

        if not payroll_period_id:
            return Response(
                {'error': 'payroll_period est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payroll_period = PayrollPeriod.objects.get(id=payroll_period_id)
        except PayrollPeriod.DoesNotExist:
            return Response(
                {'error': 'Période de paie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        employees = Employee.objects.filter(
            organization=payroll_period.organization,
            employment_status='active'
        )

        if employee_filters.get('department'):
            employees = employees.filter(department_id=employee_filters['department'])
        if employee_filters.get('position'):
            employees = employees.filter(position_id=employee_filters['position'])

        created_count = 0
        skipped_count = 0
        advances_deducted = 0
        errors = []

        for employee in employees:
            # Vérifier si fiche existe déjà
            if Payslip.objects.filter(employee=employee, payroll_period=payroll_period).exists():
                skipped_count += 1
                logger.info(f"Payslip already exists for {employee.get_full_name()}")
                continue

            try:
                # Récupérer le contrat actif
                contract = employee.contracts.filter(is_active=True).first()
                if not contract:
                    errors.append(f"{employee.get_full_name()}: Pas de contrat actif")
                    continue

                base_salary = contract.base_salary
                currency = contract.currency

                # ✨ NOUVEAU : Récupérer les avances payées non déduites
                paid_advances = []
                advance_deduction_items = []
                total_advance_amount = Decimal('0')

                if auto_deduct_advances:
                    paid_advances = PayrollAdvance.objects.filter(
                        employee=employee,
                        status=PayrollAdvance.AdvanceStatus.PAID,
                        payslip__isnull=True  # Pas encore liée à une fiche
                    )

                    for advance in paid_advances:
                        advance_deduction_items.append({
                            'name': f'Remboursement avance - {advance.reason[:30]}',
                            'amount': advance.amount,
                            'is_deduction': True,
                        })
                        total_advance_amount += advance.amount
                        logger.info(f"Auto-deducting advance {advance.id} ({advance.amount}) for {employee.get_full_name()}")

                # ✨ NOUVEAU : Ajouter déductions standards (CNPS, Impôts)
                standard_deductions = []

                # CNPS - 3.6% du salaire brut
                cnps_amount = (base_salary * Decimal('0.036')).quantize(Decimal('0.01'))
                standard_deductions.append({
                    'name': 'Cotisation CNPS (3.6%)',
                    'amount': cnps_amount,
                    'is_deduction': True,
                })

                # Impôt sur le revenu - 10% (simplifié)
                tax_amount = (base_salary * Decimal('0.10')).quantize(Decimal('0.01'))
                standard_deductions.append({
                    'name': 'Impôt sur le revenu (10%)',
                    'amount': tax_amount,
                    'is_deduction': True,
                })

                # Calculer totaux
                gross_salary = base_salary
                total_deductions = cnps_amount + tax_amount + total_advance_amount
                net_salary = gross_salary - total_deductions

                # Créer la fiche de paie
                payslip = Payslip.objects.create(
                    employee=employee,
                    payroll_period=payroll_period,
                    base_salary=base_salary,
                    currency=currency,
                    gross_salary=gross_salary,
                    total_deductions=total_deductions,
                    net_salary=net_salary,
                    status='draft'
                )

                # Créer les items de déduction
                all_deductions = standard_deductions + advance_deduction_items
                for deduction in all_deductions:
                    PayslipItem.objects.create(
                        payslip=payslip,
                        **deduction
                    )

                # ✨ NOUVEAU : Lier les avances à la fiche et marquer comme déduites
                if auto_deduct_advances and paid_advances:
                    for advance in paid_advances:
                        advance.status = PayrollAdvance.AdvanceStatus.DEDUCTED
                        advance.payslip = payslip
                        advance.deduction_month = payroll_period.end_date
                        advance.save()
                        advances_deducted += 1

                created_count += 1
                logger.info(f"Created payslip for {employee.get_full_name()} with {len(paid_advances)} advances deducted")

            except Exception as e:
                logger.exception(f"Error creating payslip for {employee.get_full_name()}")
                errors.append(f"{employee.get_full_name()}: {str(e)}")

        return Response({
            'message': f'{created_count} fiches de paie créées avec {advances_deducted} avance(s) déduite(s) automatiquement',
            'created': created_count,
            'skipped': skipped_count,
            'total_employees': employees.count(),
            'advances_deducted': advances_deducted,
            'errors': errors
        }, status=status.HTTP_201_CREATED)

# -------------------------------
# PAYROLL STATS VIEW
# -------------------------------

class PayrollStatsView(APIView):
    """
    Get payroll statistics for an organization

    Query params:
    - organization_subdomain (required): Organization slug
    - year (optional): Filter by year
    - month (optional): Filter by month (1-12)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):

        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization or not user.has_permission("can_view_payroll"):
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = Payslip.objects.filter(employee__organization=organization)
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        if year:
            queryset = queryset.filter(payroll_period__start_date__year=year)
        if month:
            queryset = queryset.filter(payroll_period__start_date__month=month)

        total_payrolls = queryset.count()
        aggregates = queryset.aggregate(
            total_gross_salary=models.Sum('gross_salary'),
            total_net_salary=models.Sum('net_salary'),
            total_deductions=models.Sum('total_deductions'),
            avg_salary=models.Avg('net_salary')
        )
        paid_count = queryset.filter(status='paid').count()
        pending_count = queryset.filter(status='pending').count()
        draft_count = queryset.filter(status='draft').count()
        stats = {
            'total_payrolls': total_payrolls,
            'total_gross_salary': float(aggregates['total_gross_salary'] or 0),
            'total_net_salary': float(aggregates['total_net_salary'] or 0),
            'total_deductions': float(aggregates['total_deductions'] or 0),
            'average_salary': float(aggregates['avg_salary'] or 0),
            'paid_count': paid_count,
            'pending_count': pending_count,
            'draft_count': draft_count,
        }
        return Response(stats, status=status.HTTP_200_OK)


class HROverviewStatsView(APIView):
    """
    Get general HR statistics for an organization
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import datetime, timedelta

        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization or not user.has_permission("can_view_employee"):
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        employees = Employee.objects.filter(organization=organization)
        total_employees = employees.count()
        active_employees = employees.filter(employment_status='active').count()
        inactive_employees = employees.filter(employment_status='inactive').count()
        on_leave_employees = employees.filter(employment_status='on_leave').count()

        departments_count = Department.objects.filter(organization=organization, is_active=True).count()
        roles_count = Role.objects.filter(
            models.Q(organization=organization) | models.Q(organization__isnull=True)
        ).count()
        pending_leave_requests = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='pending'
        ).count()
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        approved_leave_requests_this_month = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='approved',
            approval_date__gte=start_of_month
        ).count()
        current_month_payrolls = Payslip.objects.filter(
            employee__organization=organization,
            payroll_period__start_date__year=now.year,
            payroll_period__start_date__month=now.month
        )
        payroll_aggregates = current_month_payrolls.aggregate(
            total=models.Sum('net_salary'),
            avg=models.Avg('net_salary')
        )
        total_payroll_this_month = float(payroll_aggregates['total'] or 0)
        average_salary = float(payroll_aggregates['avg'] or 0)
        recent_hires = Employee.objects.filter(
            organization=organization,
            hire_date__isnull=False
        ).order_by('-hire_date')[:5]
        recent_hires_data = EmployeeListSerializer(recent_hires, many=True).data
        upcoming_leaves = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='approved',
            start_date__gte=now
        ).order_by('start_date')[:10]
        upcoming_leaves_data = LeaveRequestSerializer(upcoming_leaves, many=True).data

        stats = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': inactive_employees,
            'on_leave_employees': on_leave_employees,
            'departments_count': departments_count,
            'roles_count': roles_count,
            'pending_leave_requests': pending_leave_requests,
            'approved_leave_requests_this_month': approved_leave_requests_this_month,
            'total_payroll_this_month': total_payroll_this_month,
            'average_salary': average_salary,
            'recent_hires': recent_hires_data,
            'upcoming_leaves': upcoming_leaves_data,
        }
        return Response(stats, status=status.HTTP_200_OK)


class DepartmentStatsView(APIView):
    """
    Get statistics grouped by department
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):

        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization or not user.has_permission("can_view_department"):
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        departments = Department.objects.filter(organization=organization, is_active=True)
        stats = []
        for dept in departments:
            dept_employees = Employee.objects.filter(department=dept)
            employee_count = dept_employees.count()
            active_count = dept_employees.filter(employment_status='active').count()

            avg_salary = Contract.objects.filter(
                employee__department=dept,
                is_active=True
            ).aggregate(avg=models.Avg('base_salary'))['avg'] or 0

            leave_requests_pending = LeaveRequest.objects.filter(
                employee__department=dept,
                status='pending'
            ).count()

            stats.append({
                'department': DepartmentSerializer(dept).data,
                'employee_count': employee_count,
                'active_count': active_count,
                'average_salary': float(avg_salary),
                'leave_requests_pending': leave_requests_pending,
            })

        return Response(stats, status=status.HTTP_200_OK)

class PayrollAdvanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payroll advance requests"""
    permission_classes = [IsAdminUserOrEmployee]

    def get_serializer_class(self):
        if self.action == 'list':
            return PayrollAdvanceListSerializer
        elif self.action == 'create':
            return PayrollAdvanceCreateSerializer
        return PayrollAdvanceSerializer

    def get_queryset(self):
        user = self.request.user

        # Récupérer l'organisation depuis les paramètres de requête
        org_subdomain = self.request.query_params.get('organization_subdomain')
        status_filter = self.request.query_params.get('status')
        employee_filter = self.request.query_params.get('employee')

        queryset = PayrollAdvance.objects.all()

        if isinstance(user, AdminUser):
            if org_subdomain:
                try:
                    organization = Organization.objects.get(
                        subdomain=org_subdomain,
                        admin=user
                    )
                    queryset = queryset.filter(employee__organization=organization)
                except Organization.DoesNotExist:
                    queryset = PayrollAdvance.objects.none()
            else:
                org_ids = user.organizations.values_list('id', flat=True)
                queryset = queryset.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            # Les employés ne voient que leurs propres demandes ou celles qu'ils peuvent gérer
            if user.has_permission("can_view_payroll") or user.is_hr_admin():
                queryset = queryset.filter(employee__organization=user.organization)
            else:
                queryset = queryset.filter(employee=user)
        else:
            queryset = PayrollAdvance.objects.none()

        # Filtrer par employé si spécifié
        if employee_filter:
            queryset = queryset.filter(employee_id=employee_filter)

        # Filtrer par statut si spécifié
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.select_related('employee', 'approved_by', 'payslip')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def approve(self, request, pk=None):
        """Approuver une demande d'avance"""
        advance = self.get_object()
        user = request.user

        # Vérifier que l'utilisateur a la permission d'approuver
        if isinstance(user, Employee):
            if not (user.has_permission("can_manage_payroll") or user.is_hr_admin()):
                return Response(
                    {'error': 'Vous n\'avez pas la permission d\'approuver des demandes d\'avance'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if advance.status != 'pending':
            return Response(
                {'error': 'Seules les demandes en attente peuvent être approuvées'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PayrollAdvanceApprovalSerializer(data={'action': 'approve', **request.data})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        advance.status = 'approved'
        advance.approved_by = user if isinstance(user, Employee) else None
        advance.approved_date = timezone.now()
        advance.payment_date = data.get('payment_date')
        advance.deduction_month = data.get('deduction_month')
        if data.get('notes'):
            advance.notes = data['notes']
        advance.save()

        return Response(
            PayrollAdvanceSerializer(advance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def reject(self, request, pk=None):
        """Rejeter une demande d'avance"""
        advance = self.get_object()
        user = request.user

        # Vérifier que l'utilisateur a la permission de rejeter
        if isinstance(user, Employee):
            if not (user.has_permission("can_manage_payroll") or user.is_hr_admin()):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de rejeter des demandes d\'avance'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if advance.status != 'pending':
            return Response(
                {'error': 'Seules les demandes en attente peuvent être rejetées'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PayrollAdvanceApprovalSerializer(data={'action': 'reject', **request.data})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        advance.status = 'rejected'
        advance.approved_by = user if isinstance(user, Employee) else None
        advance.approved_date = timezone.now()
        advance.rejection_reason = data.get('rejection_reason', '')
        advance.save()

        return Response(
            PayrollAdvanceSerializer(advance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def mark_as_paid(self, request, pk=None):
        """Marquer une avance comme payée"""
        advance = self.get_object()
        user = request.user

        # Vérifier que l'utilisateur a la permission
        if isinstance(user, Employee):
            if not (user.has_permission("can_manage_payroll") or user.is_hr_admin()):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de marquer les avances comme payées'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if advance.status != 'approved':
            return Response(
                {'error': 'Seules les avances approuvées peuvent être marquées comme payées'},
                status=status.HTTP_400_BAD_REQUEST
            )

        advance.status = 'paid'
        advance.payment_date = request.data.get('payment_date', timezone.now().date())
        advance.save()

        return Response(
            PayrollAdvanceSerializer(advance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def deduct_from_payslip(self, request, pk=None):
        """Déduire l'avance d'une fiche de paie (fermer l'avance)"""

        advance = self.get_object()
        user = request.user

        # Log de débogage
        logger.info(f"Deduct from payslip called for advance {advance.id}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Advance status: {advance.status}")

        # Vérifier que l'utilisateur a la permission
        if isinstance(user, Employee):
            if not (user.has_permission("can_manage_payroll") or user.is_hr_admin()):
                logger.warning(f"User {user.email} lacks permission to deduct advances")
                return Response(
                    {'error': 'Vous n\'avez pas la permission de déduire des avances'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if advance.status != 'paid':
            logger.warning(f"Advance {advance.id} has status {advance.status}, expected 'paid'")
            return Response(
                {'error': f'Seules les avances payées peuvent être déduites. Statut actuel: {advance.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payslip_id = request.data.get('payslip_id')
        logger.info(f"Payslip ID received: {payslip_id}")

        if not payslip_id:
            logger.error("No payslip_id provided in request")
            return Response(
                {'error': 'L\'ID de la fiche de paie est requis (payslip_id)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger.info(f"Looking for payslip with ID: {payslip_id}")
            payslip = Payslip.objects.get(id=payslip_id)
            logger.info(f"Payslip found: {payslip.id} for employee {payslip.employee.get_full_name()}")

            # Vérifier que la fiche de paie appartient au même employé
            if payslip.employee != advance.employee:
                logger.error(f"Employee mismatch: payslip employee {payslip.employee.id} != advance employee {advance.employee.id}")
                return Response(
                    {'error': 'La fiche de paie doit appartenir au même employé que l\'avance'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Marquer l'avance comme déduite
            logger.info(f"Marking advance {advance.id} as deducted")
            advance.status = 'deducted'
            advance.payslip = payslip
            advance.deduction_month = payslip.payroll_period.end_date
            advance.save()
            logger.info(f"Advance {advance.id} successfully marked as deducted")

            return Response(
                PayrollAdvanceSerializer(advance).data,
                status=status.HTTP_200_OK
            )

        except Payslip.DoesNotExist:
            logger.error(f"Payslip with ID {payslip_id} not found")
            return Response(
                {'error': f'Fiche de paie non trouvée (ID: {payslip_id})'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Unexpected error while deducting advance: {str(e)}")
            return Response(
                {'error': f'Erreur inattendue: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# -------------------------------
# PERMISSION & ROLE VIEWSETS
# -------------------------------

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing permissions (read-only)"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Permission.objects.all().order_by('category', 'name')
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles"""
    queryset = Role.objects.all()
    permission_classes = [IsAdminUserOrEmployee, RequiresRolePermission]

    def get_queryset(self):
        user = self.request.user

        queryset = Role.objects.all()

        # Récupérer l'organisation depuis les paramètres de requête
        org_subdomain = self.request.query_params.get('organization_subdomain')
        org_id = self.request.query_params.get('organization')

        if isinstance(user, AdminUser):
            # Si un subdomain ou ID d'organisation est fourni, filtrer par cette organisation
            if org_subdomain:
                try:
                    organization = Organization.objects.get(
                        subdomain=org_subdomain,
                        admin=user
                    )
                    queryset = queryset.filter(
                        models.Q(organization__isnull=True) |
                        models.Q(organization=organization)
                    )
                except Organization.DoesNotExist:
                    # Organisation non trouvée ou l'admin n'y a pas accès
                    queryset = Role.objects.none()
            elif org_id:
                try:
                    organization = Organization.objects.get(
                        id=org_id,
                        admin=user
                    )
                    queryset = queryset.filter(
                        models.Q(organization__isnull=True) |
                        models.Q(organization=organization)
                    )
                except Organization.DoesNotExist:
                    queryset = Role.objects.none()
            else:
                # Pas d'organisation spécifiée, retourner les rôles de toutes les organisations de l'admin
                org_ids = user.organizations.values_list('id', flat=True)
                queryset = queryset.filter(
                    models.Q(organization__isnull=True) |
                    models.Q(organization_id__in=org_ids)
                )
        elif isinstance(user, Employee):
            # Pour les employés, toujours filtrer par leur organisation
            queryset = queryset.filter(
                models.Q(organization__isnull=True) |
                models.Q(organization=user.organization)
            )
        else:
            queryset = Role.objects.none()

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        is_system_role = self.request.query_params.get('is_system_role', None)
        if is_system_role is not None:
            queryset = queryset.filter(is_system_role=is_system_role.lower() == 'true')

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(code__icontains=search)
            )
        return queryset.order_by('-is_system_role', 'name')

    def get_serializer_class(self):
        if self.action == 'list':
            return RoleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RoleCreateSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        user = self.request.user

        if not serializer.validated_data.get('is_system_role', False):
            if isinstance(user, AdminUser):
                # Essayer d'abord avec organization_subdomain
                org_subdomain = self.request.query_params.get('organization_subdomain')

                if org_subdomain:
                    try:
                        org = Organization.objects.get(subdomain=org_subdomain, admin=user)
                        logger.info(f"Creating role for organization: {org.name}")
                        serializer.save(organization=org)
                    except Organization.DoesNotExist:
                        logger.error(f"Organization with subdomain {org_subdomain} not found for user {user.email}")
                        raise serializers.ValidationError({
                            'organization': f'Organisation avec le subdomain "{org_subdomain}" non trouvée'
                        })
                else:
                    # Fallback: utiliser la première organisation de l'admin
                    org = user.organizations.first()
                    if org:
                        logger.info(f"Creating role for admin's first organization: {org.name}")
                        serializer.save(organization=org)
                    else:
                        logger.error(f"Admin user {user.email} has no organization")
                        raise serializers.ValidationError({
                            'organization': "L'administrateur n'a aucune organisation"
                        })
            elif isinstance(user, Employee):
                logger.info(f"Creating role for employee's organization: {user.organization.name}")
                serializer.save(organization=user.organization)
            else:
                logger.error(f"Cannot determine organization for user type: {type(user)}")
                raise serializers.ValidationError({
                    'organization': "Impossible de déterminer l'organisation"
                })
        else:
            logger.info("Creating system role (no organization)")
            serializer.save()

# -------------------------------
# ATTENDANCE VIEWS
# -------------------------------

class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance records"""
    permission_classes = [IsAdminUserOrEmployee, RequiresAttendancePermission]
    serializer_class = AttendanceSerializer
    filterset_fields = ['employee', 'date', 'status', 'is_approved']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    ordering_fields = ['date', 'check_in', 'check_out', 'total_hours']
    ordering = ['-date']

    def get_queryset(self):
        user = self.request.user

        organization_slug = self.request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Attendance.objects.none()

        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Attendance.objects.none()

        queryset = Attendance.objects.filter(organization=organization).select_related(
            'employee', 'employee__department', 'approved_by', 'approved_by_admin'
        )

        if isinstance(user, AdminUser):
            pass
        elif isinstance(user, Employee):
            if user.has_permission('can_view_all_attendance'):
                pass
            elif user.has_permission('can_view_attendance'):
                queryset = queryset.filter(user_email=user.email)
            else:
                queryset = Attendance.objects.none()
        else:
            queryset = Attendance.objects.none()

        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        is_approved = self.request.query_params.get('is_approved', None)
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AttendanceCreateSerializer
        return AttendanceSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if isinstance(user, Employee):
            if not user.has_permission('can_create_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Vous n\'avez pas la permission de créer des pointages')
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if isinstance(user, Employee):
            if not user.has_permission('can_update_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Vous n\'avez pas la permission de modifier des pointages')
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if isinstance(user, Employee):
            if not user.has_permission('can_delete_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Vous n\'avez pas la permission de supprimer des pointages')
        instance.delete()

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        """
        Manual check-in endpoint - REQUIRES can_manual_checkin
        """
        user = request.user

        if isinstance(user, Employee):
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': "Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, AdminUser):
            pass
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AttendanceCheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.contenttypes.models import ContentType

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        employee = None
        content_type_obj = None
        object_id = None

        if isinstance(user, AdminUser):
            employee_id = request.data.get('employee_id')
            if employee_id:
                try:
                    employee = Employee.objects.get(id=employee_id, organization=organization)
                    user_email = employee.email
                    user_full_name = employee.get_full_name()
                except Employee.DoesNotExist:
                    return Response(
                        {'error': 'Employee not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                content_type_obj = ContentType.objects.get_for_model(AdminUser)
                object_id = user.id
                user_email = user.email
                user_full_name = user.get_full_name()
        elif isinstance(user, Employee):
            employee = user
            user_email = employee.email
            user_full_name = employee.get_full_name()
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        existing = Attendance.objects.filter(
            organization=organization,
            user_email=user_email,
            date=today
        ).first()

        if existing and existing.check_in:
            return Response(
                {'error': 'Already checked in today', 'attendance': AttendanceSerializer(existing).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        if existing:
            existing.check_in = timezone.now()
            existing.check_in_location = serializer.validated_data.get('location', '')
            existing.check_in_notes = serializer.validated_data.get('notes', '')
            existing.status = 'present'
            existing.save()
            attendance = existing
        else:
            attendance = Attendance.objects.create(
                employee=employee,
                content_type=content_type_obj,
                object_id=object_id,
                organization=organization,
                user_email=user_email,
                user_full_name=user_full_name,
                date=today,
                check_in=timezone.now(),
                check_in_location=serializer.validated_data.get('location', ''),
                check_in_notes=serializer.validated_data.get('notes', ''),
                status='present'
            )
        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        """
        Manual check-out endpoint - REQUIRES can_manual_checkin
        """
        user = request.user

        if isinstance(user, Employee):
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': "Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, AdminUser):
            pass
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AttendanceCheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        today = timezone.now().date()
        user_email = None

        if isinstance(user, AdminUser):
            employee_id = request.data.get('employee_id')
            if employee_id:
                try:
                    employee = Employee.objects.get(id=employee_id, organization=organization)
                    user_email = employee.email
                except Employee.DoesNotExist:
                    return Response(
                        {'error': 'Employee not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                user_email = user.email
        elif isinstance(user, Employee):
            user_email = user.email
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        attendance = Attendance.objects.filter(
            organization=organization,
            user_email=user_email,
            date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'No check-in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not attendance.check_in:
            return Response(
                {'error': 'Must check in before checking out'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.check_out:
            return Response(
                {'error': 'Already checked out today', 'attendance': AttendanceSerializer(attendance).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance.check_out = timezone.now()
        attendance.check_out_location = serializer.validated_data.get('location', '')
        attendance.check_out_notes = serializer.validated_data.get('notes', '')
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='today')
    def today(self, request):
        user = request.user

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if isinstance(user, AdminUser):
            user_email = user.email
        elif isinstance(user, Employee):
            user_email = user.email
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            organization=organization,
            user_email=user_email,
            date=today
        ).first()

        if not attendance:
            return Response(
                {'message': 'No attendance record for today'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(AttendanceSerializer(attendance).data)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        user = request.user

        is_admin = isinstance(user, AdminUser)
        is_employee_with_permission = isinstance(user, Employee) and user.has_permission('can_approve_attendance')

        if not (is_admin or is_employee_with_permission):
            return Response(
                {'error': 'You do not have permission to approve/reject attendance'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AttendanceApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        attendance = self.get_object()
        action = serializer.validated_data['action']

        if action == 'approve':
            attendance.approval_status = 'approved'
            attendance.is_approved = True
            attendance.rejection_reason = ''
        else:
            attendance.approval_status = 'rejected'
            attendance.is_approved = False
            attendance.rejection_reason = serializer.validated_data.get('rejection_reason', '')
        if is_admin:
            attendance.approved_by_admin = user
            attendance.approved_by = None
        else:
            attendance.approved_by = user
            attendance.approved_by_admin = None

        attendance.approval_date = timezone.now()
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='start-break')
    def start_break(self, request):
        user = request.user

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if isinstance(user, AdminUser):
            user_email = user.email
        elif isinstance(user, Employee):
            user_email = user.email
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            organization=organization,
            user_email=user_email,
            date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'No attendance record found for today'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not attendance.check_in:
            return Response(
                {'error': 'Must check in before starting a break'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.check_out:
            return Response(
                {'error': 'Cannot start a break after checking out'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.break_start and not attendance.break_end:
            return Response(
                {'error': 'Break already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance.break_start = timezone.now()
        attendance.break_end = None
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='end-break')
    def end_break(self, request):
        user = request.user

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        if isinstance(user, AdminUser):
            user_email = user.email
        elif isinstance(user, Employee):
            user_email = user.email
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()
        attendance = Attendance.objects.filter(
            organization=organization,
            user_email=user_email,
            date=today
        ).first()

        if not attendance:
            return Response(
                {'error': 'No attendance record found for today'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not attendance.break_start:
            return Response(
                {'error': 'No break in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.break_end:
            return Response(
                {'error': 'Break already ended'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance.break_end = timezone.now()
        attendance.calculate_hours()
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        user = request.user
        employee_id = request.query_params.get('employee_id', None)

        if employee_id:
            if isinstance(user, Employee) and not user.has_permission('can_view_all_attendance'):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de voir les stats pointage de cet employé'},
                    status=status.HTTP_403_FORBIDDEN
                )
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {'error': 'Employee not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            if not isinstance(user, Employee):
                return Response(
                    {'error': 'Employee ID required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            employee = user

        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        queryset = Attendance.objects.filter(employee=employee)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        total_days = queryset.count()
        present_days = queryset.filter(status='present').count()
        absent_days = queryset.filter(status='absent').count()
        late_days = queryset.filter(status='late').count()
        half_days = queryset.filter(status='half_day').count()
        on_leave_days = queryset.filter(status='on_leave').count()
        total_hours = queryset.aggregate(
            total=models.Sum('total_hours')
        )['total'] or 0
        overtime_hours = queryset.aggregate(
            total=models.Sum('overtime_hours')
        )['total'] or 0

        average_hours_per_day = total_hours / present_days if present_days > 0 else 0

        stats_data = {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'half_days': half_days,
            'on_leave_days': on_leave_days,
            'total_hours': total_hours,
            'overtime_hours': overtime_hours,
            'average_hours_per_day': average_hours_per_day
        }

        serializer = AttendanceStatsSerializer(data=stats_data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    # ===============================
    # QR CODE ATTENDANCE ENDPOINTS
    # ===============================

    @action(detail=False, methods=['post'], url_path='qr-session/create')
    def create_qr_session(self, request):

        if isinstance(request.user, Employee):
            if not request.user.has_permission('can_create_qr_session'):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de créer des sessions QR'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not isinstance(request.user, AdminUser):
            return Response(
                {'error': 'Authentification requise'},
                status=status.HTTP_403_FORBIDDEN
            )

        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug required in headers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import QRCodeSessionCreateSerializer, QRCodeSessionSerializer

        serializer = QRCodeSessionCreateSerializer(
            data=request.data,
            context={
                'organization': organization,
                'request': request
            }
        )
        if serializer.is_valid():
            session = serializer.save()
            response_serializer = QRCodeSessionSerializer(session)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='qr-session/(?P<session_id>[^/.]+)')
    def get_qr_session(self, request, session_id=None):
        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug required in headers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            session = QRCodeSession.objects.get(
                id=session_id,
                organization=organization
            )
            from .serializers import QRCodeSessionSerializer
            serializer = QRCodeSessionSerializer(session)
            return Response(serializer.data)
        except QRCodeSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], url_path='qr-check-in')
    def qr_check_in(self, request):
        """
        QR code attendance endpoint - handles both check-in and check-out automatically.
        Requires authentication - employee is identified from their login session.
        Returns action type and message for user feedback.
        """
        organization_slug = request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Response(
                {'error': 'Organization slug required in headers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import QRAttendanceCheckInSerializer

        # Pass request in context so serializer can identify the logged-in user
        serializer = QRAttendanceCheckInSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            attendance = serializer.save()
            from .serializers import AttendanceSerializer
            attendance_data = AttendanceSerializer(attendance).data
            
            # Build response with action and message
            response_data = {
                'success': True,
                'action': getattr(attendance, '_qr_action', 'check_in'),
                'message': getattr(attendance, '_qr_message', 'Pointage enregistré avec succès'),
                'attendance': attendance_data,
                'employee_name': attendance.user_full_name or (attendance.employee.get_full_name() if attendance.employee else ''),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

