from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.http import HttpResponse
from datetime import timedelta
import json
from django.core.serializers.json import DjangoJSONEncoder
from uuid import UUID
from decimal import Decimal

from core.models import Organization
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip, Permission, Role, Attendance
)
from .serializers import (
    EmployeeSerializer, EmployeeCreateSerializer, EmployeeListSerializer,
    EmployeeUpdateSerializer, EmployeeLoginSerializer, EmployeeChangePasswordSerializer,
    DepartmentSerializer, PositionSerializer, ContractSerializer,
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    PayrollPeriodSerializer, PayslipSerializer, PayslipCreateSerializer,
    PermissionSerializer, RoleSerializer, RoleListSerializer, RoleCreateSerializer,
    AttendanceSerializer, AttendanceCreateSerializer, AttendanceCheckInSerializer,
    AttendanceCheckOutSerializer, AttendanceApprovalSerializer, AttendanceStatsSerializer
)
from .permissions import (
    IsHRAdminOrReadOnly, IsHRAdmin,
    IsManagerOrHRAdmin, IsAdminUserOrEmployee
)


# -------------------------------
# JWT Cookie Helper Functions
# -------------------------------

def convert_uuids_to_strings(data):
    """Recursively convert all UUID objects to strings in a dictionary or list"""
    if isinstance(data, dict):
        return {key: convert_uuids_to_strings(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_uuids_to_strings(item) for item in data]
    elif isinstance(data, UUID):
        return str(data)
    else:
        return data


def set_jwt_cookies(response, access_token, refresh_token):
    """Set JWT tokens in HTTP-only cookies"""
    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )

    response.set_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
        httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
        samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )


def clear_jwt_cookies(response):
    """Clear JWT cookies"""
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )
    response.delete_cookie(
        key=settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
        path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
    )


# -------------------------------
# EMPLOYEE AUTHENTICATION VIEWS
# -------------------------------

class EmployeeLoginView(APIView):
    """Employee login endpoint"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmployeeLoginSerializer(data=request.data)
        if serializer.is_valid():
            employee = serializer.validated_data['employee']

            # Generate JWT tokens manually (without OutstandingToken)
            # This avoids the issue with token_blacklist expecting AdminUser
            access_token_obj = AccessToken()
            access_token_obj['user_id'] = str(employee.id)  # Convert UUID to string
            access_token_obj['email'] = employee.email
            access_token_obj['user_type'] = 'employee'
            access_token_obj.set_exp(lifetime=timedelta(minutes=15))
            access_token = str(access_token_obj)

            # Create a refresh token manually
            refresh_token_obj = AccessToken()
            refresh_token_obj['user_id'] = str(employee.id)  # Convert UUID to string
            refresh_token_obj['email'] = employee.email
            refresh_token_obj['user_type'] = 'employee'
            refresh_token_obj['token_type'] = 'refresh'
            refresh_token_obj.set_exp(lifetime=timedelta(days=7))
            refresh_token = str(refresh_token_obj)

            # Update last login
            employee.last_login = timezone.now()
            employee.save(update_fields=['last_login'])

            # Return employee data
            employee_data = EmployeeSerializer(employee).data

            # Convert all UUIDs to strings to ensure JSON serializability
            employee_data = convert_uuids_to_strings(employee_data)

            # Create response
            response = Response({
                'employee': employee_data,
                'message': 'Connexion reussie',
                'access': access_token,
                'refresh': refresh_token,
            }, status=status.HTTP_200_OK)

            # Set tokens in HTTP-only cookies
            set_jwt_cookies(response, access_token, refresh_token)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeLogoutView(APIView):
    """Employee logout endpoint"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'])
            if not refresh_token:
                refresh_token = request.data.get('refresh')

            # Note: Since we create tokens manually without OutstandingToken,
            # we can't use the blacklist feature. Just clear the cookies.
            # In production, consider implementing a custom blacklist for employee tokens.

            response = Response({
                'message': 'Deconnexion reussie'
            }, status=status.HTTP_200_OK)

            clear_jwt_cookies(response)
            return response

        except Exception as e:
            # Even on error, clear cookies for security
            response = Response({
                'message': 'Deconnexion reussie'
            }, status=status.HTTP_200_OK)

            clear_jwt_cookies(response)
            return response


class EmployeeMeView(APIView):
    """Get current employee info"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if isinstance(request.user, Employee):
            serializer = EmployeeSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({
            'error': 'Utilisateur non autorise'
        }, status=status.HTTP_403_FORBIDDEN)


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

class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing employees"""
    queryset = Employee.objects.all()
    permission_classes = [IsAdminUserOrEmployee, IsHRAdminOrReadOnly]

    def get_queryset(self):
        """Filter employees by organization"""
        user = self.request.user
        from core.models import AdminUser

        # Get organization filter from query params (subdomain or id)
        org_subdomain = self.request.query_params.get('organization_subdomain')
        org_id = self.request.query_params.get('organization')

        queryset = Employee.objects.none()

        if isinstance(user, AdminUser):
            # AdminUser can access employees from their organizations
            accessible_orgs = user.organizations.all()

            # If specific organization requested, filter by it
            if org_subdomain:
                queryset = Employee.objects.filter(
                    organization__subdomain=org_subdomain,
                    organization__in=accessible_orgs
                )
            elif org_id:
                queryset = Employee.objects.filter(
                    organization_id=org_id,
                    organization__in=accessible_orgs
                )
            else:
                # No specific org requested, return all employees from all user's orgs
                queryset = Employee.objects.filter(organization__in=accessible_orgs)

        elif isinstance(user, Employee):
            # Employee can only access employees from their organization
            queryset = Employee.objects.filter(organization=user.organization)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return EmployeeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        elif self.action == 'list':
            return EmployeeListSerializer
        return EmployeeSerializer

    def perform_create(self, serializer):
        """Set organization when creating employee"""
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_id = self.request.data.get('organization')
            if not org_id:
                raise serializers.ValidationError({'organization': 'Organisation requise'})

            organization = Organization.objects.filter(id=org_id, admin=user).first()
            if not organization:
                raise serializers.ValidationError({'organization': 'Organisation non autorisee'})

        elif isinstance(user, Employee):
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Type utilisateur non autorise'})

        serializer.save(organization=organization)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        employee = self.get_object()
        employee.is_active = True
        employee.save()
        return Response({
            'message': f'Employe {employee.get_full_name()} active'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        employee = self.get_object()
        employee.is_active = False
        employee.save()
        return Response({
            'message': f'Employe {employee.get_full_name()} desactive'
        }, status=status.HTTP_200_OK)


# -------------------------------
# HR CONFIGURATION VIEWS
# -------------------------------

class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUserOrEmployee, IsHRAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Department.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            return Department.objects.filter(organization=user.organization)
        return Department.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_id = self.request.data.get('organization')
            organization = Organization.objects.filter(id=org_id, admin=user).first()
        elif isinstance(user, Employee):
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorise'})

        serializer.save(organization=organization)


class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAdminUserOrEmployee, IsHRAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Position.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            return Position.objects.filter(organization=user.organization)
        return Position.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_id = self.request.data.get('organization')
            organization = Organization.objects.filter(id=org_id, admin=user).first()
        elif isinstance(user, Employee):
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorise'})

        serializer.save(organization=organization)


class ContractViewSet(viewsets.ModelViewSet):
    serializer_class = ContractSerializer
    permission_classes = [IsAdminUserOrEmployee, IsHRAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Contract.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.is_hr_admin():
                return Contract.objects.filter(employee__organization=user.organization)
            return Contract.objects.filter(employee=user)
        return Contract.objects.none()


# -------------------------------
# LEAVE MANAGEMENT VIEWS
# -------------------------------

class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAdminUserOrEmployee, IsHRAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveType.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            return LeaveType.objects.filter(organization=user.organization)
        return LeaveType.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_id = self.request.data.get('organization')
            organization = Organization.objects.filter(id=org_id, admin=user).first()
        elif isinstance(user, Employee):
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorise'})

        serializer.save(organization=organization)


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAdminUserOrEmployee]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveBalance.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.is_hr_admin():
                return LeaveBalance.objects.filter(employee__organization=user.organization)
            return LeaveBalance.objects.filter(employee=user)
        return LeaveBalance.objects.none()


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminUserOrEmployee]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return LeaveRequest.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
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
        from core.models import AdminUser

        if isinstance(self.request.user, Employee):
            # Employee creating their own leave request
            leave_request = serializer.save(employee=self.request.user)
        elif isinstance(self.request.user, AdminUser):
            # AdminUser creating a leave request for an employee
            # The employee must be specified in the request data
            employee_id = self.request.data.get('employee')
            if not employee_id:
                raise serializers.ValidationError({
                    'employee': 'L\'employé est requis pour créer une demande de congé'
                })

            try:
                employee = Employee.objects.get(id=employee_id)
                # Verify admin has access to this employee's organization
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
        # Si la demande est en attente, décrémenter pending_days
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
        leave_request = self.get_object()
        serializer = LeaveRequestApprovalSerializer(data=request.data)

        if serializer.is_valid():
            leave_request.status = 'approved'

            # Set approver using GenericForeignKey (supports both Employee and AdminUser)
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

            # Set approver using GenericForeignKey (supports both Employee and AdminUser)
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


# -------------------------------
# PAYROLL VIEWS
# -------------------------------

class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsAdminUserOrEmployee, IsHRAdmin]

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return PayrollPeriod.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            return PayrollPeriod.objects.filter(organization=user.organization)
        return PayrollPeriod.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_id = self.request.data.get('organization')
            organization = Organization.objects.filter(id=org_id, admin=user).first()
        elif isinstance(user, Employee):
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorise'})

        serializer.save(organization=organization)


class PayslipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOrEmployee]

    def get_serializer_class(self):
        if self.action == 'create':
            return PayslipCreateSerializer
        return PayslipSerializer

    def get_queryset(self):
        user = self.request.user
        from core.models import AdminUser

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Payslip.objects.filter(employee__organization_id__in=org_ids)
        elif isinstance(user, Employee):
            if user.is_hr_admin():
                return Payslip.objects.filter(employee__organization=user.organization)
            return Payslip.objects.filter(employee=user)
        return Payslip.objects.none()

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
        """Export une fiche de paie en PDF"""
        from .pdf_generator import generate_payslip_pdf

        payslip = self.get_object()

        # Générer le PDF
        pdf_buffer = generate_payslip_pdf(payslip)

        # Créer le nom du fichier
        filename = f"Fiche_Paie_{payslip.employee.get_full_name().replace(' ', '_')}_{payslip.payroll_period.name.replace(' ', '_')}.pdf"

        # Retourner le PDF en réponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    @action(detail=False, methods=['post'], permission_classes=[IsHRAdmin])
    def generate_for_period(self, request):
        """
        Génère les fiches de paie pour tous les employés actifs d'une période

        Body:
        {
            "payroll_period": "uuid",
            "employee_filters": {  # Optionnel
                "department": "uuid",
                "position": "uuid"
            }
        }
        """
        payroll_period_id = request.data.get('payroll_period')
        employee_filters = request.data.get('employee_filters', {})

        if not payroll_period_id:
            return Response(
                {'error': 'payroll_period est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupérer la période
        try:
            payroll_period = PayrollPeriod.objects.get(id=payroll_period_id)
        except PayrollPeriod.DoesNotExist:
            return Response(
                {'error': 'Période de paie non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Récupérer les employés actifs de l'organisation
        employees = Employee.objects.filter(
            organization=payroll_period.organization,
            employment_status='active'
        )

        # Appliquer les filtres optionnels
        if employee_filters.get('department'):
            employees = employees.filter(department_id=employee_filters['department'])

        if employee_filters.get('position'):
            employees = employees.filter(position_id=employee_filters['position'])

        # Statistiques
        created_count = 0
        skipped_count = 0
        errors = []

        for employee in employees:
            # Vérifier si une fiche existe déjà
            if Payslip.objects.filter(employee=employee, payroll_period=payroll_period).exists():
                skipped_count += 1
                continue

            try:
                # Récupérer le salaire de base du contrat actif
                contract = employee.contracts.filter(is_active=True).first()
                if not contract:
                    errors.append(f"{employee.get_full_name()}: Pas de contrat actif")
                    continue

                # Créer la fiche de paie
                payslip = Payslip.objects.create(
                    employee=employee,
                    payroll_period=payroll_period,
                    base_salary=contract.base_salary,
                    currency=contract.currency,
                    gross_salary=contract.base_salary,  # Sera recalculé si des items sont ajoutés
                    total_deductions=Decimal('0'),
                    net_salary=contract.base_salary,
                    status='draft'
                )

                created_count += 1

            except Exception as e:
                errors.append(f"{employee.get_full_name()}: {str(e)}")

        return Response({
            'message': f'{created_count} fiches de paie créées',
            'created': created_count,
            'skipped': skipped_count,
            'total_employees': employees.count(),
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
        from core.models import AdminUser

        # Get organization from query params
        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization
        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user has access to this organization
        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization:
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Base queryset
        queryset = Payslip.objects.filter(employee__organization=organization)

        # Apply filters
        year = request.query_params.get('year')
        month = request.query_params.get('month')

        if year:
            queryset = queryset.filter(payroll_period__start_date__year=year)

        if month:
            queryset = queryset.filter(payroll_period__start_date__month=month)

        # Calculate statistics
        total_payrolls = queryset.count()

        aggregates = queryset.aggregate(
            total_gross_salary=models.Sum('gross_salary'),
            total_net_salary=models.Sum('net_salary'),
            total_deductions=models.Sum('total_deductions'),
            avg_salary=models.Avg('net_salary')
        )

        # Count by status
        paid_count = queryset.filter(status='paid').count()
        pending_count = queryset.filter(status='pending').count()
        draft_count = queryset.filter(status='draft').count()

        # Build response
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

    Returns:
    - total_employees
    - active_employees
    - inactive_employees
    - on_leave_employees
    - departments_count
    - roles_count
    - pending_leave_requests
    - approved_leave_requests_this_month
    - total_payroll_this_month
    - average_salary
    - recent_hires (last 5 employees)
    - upcoming_leaves (next 10 leave requests)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.models import AdminUser
        from datetime import datetime, timedelta

        # Get organization from query params
        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization
        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user has access to this organization
        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization:
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Employee statistics
        employees = Employee.objects.filter(organization=organization)
        total_employees = employees.count()
        active_employees = employees.filter(employment_status='active').count()
        inactive_employees = employees.filter(employment_status='inactive').count()
        on_leave_employees = employees.filter(employment_status='on_leave').count()

        # Department and roles count
        departments_count = Department.objects.filter(organization=organization, is_active=True).count()
        roles_count = Role.objects.filter(
            models.Q(organization=organization) | models.Q(organization__isnull=True)
        ).count()

        # Leave requests statistics
        pending_leave_requests = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='pending'
        ).count()

        # Approved leave requests this month
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        approved_leave_requests_this_month = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='approved',
            approval_date__gte=start_of_month
        ).count()

        # Payroll statistics for current month
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

        # Recent hires (last 5)
        recent_hires = Employee.objects.filter(
            organization=organization,
            hire_date__isnull=False
        ).order_by('-hire_date')[:5]

        recent_hires_data = EmployeeListSerializer(recent_hires, many=True).data

        # Upcoming leaves (next 10)
        upcoming_leaves = LeaveRequest.objects.filter(
            employee__organization=organization,
            status='approved',
            start_date__gte=now
        ).order_by('start_date')[:10]

        upcoming_leaves_data = LeaveRequestSerializer(upcoming_leaves, many=True).data

        # Build response
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

    Returns list of departments with:
    - department info
    - employee_count
    - active_count
    - average_salary
    - leave_requests_pending
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.models import AdminUser

        # Get organization from query params
        org_subdomain = request.query_params.get('organization_subdomain')
        if not org_subdomain:
            return Response(
                {'error': 'organization_subdomain est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization
        try:
            organization = Organization.objects.get(subdomain=org_subdomain)
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organisation non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify user has access to this organization
        user = request.user
        if isinstance(user, AdminUser):
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, Employee):
            if user.organization != organization:
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Type d\'utilisateur non autorisé'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get all departments for the organization
        departments = Department.objects.filter(organization=organization, is_active=True)

        stats = []
        for dept in departments:
            # Employee counts
            dept_employees = Employee.objects.filter(department=dept)
            employee_count = dept_employees.count()
            active_count = dept_employees.filter(employment_status='active').count()

            # Average salary from contracts
            avg_salary = Contract.objects.filter(
                employee__department=dept,
                is_active=True
            ).aggregate(avg=models.Avg('base_salary'))['avg'] or 0

            # Pending leave requests
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


# -------------------------------
# PERMISSION & ROLE VIEWSETS
# -------------------------------

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing permissions (read-only)"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """All permissions are available to authenticated users"""
        queryset = Permission.objects.all().order_by('category', 'name')

        # Optional filters
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing roles"""
    queryset = Role.objects.all()
    permission_classes = [IsAuthenticated, IsHRAdminOrReadOnly]

    def get_queryset(self):
        """Filter roles by organization or system roles"""
        user = self.request.user
        from core.models import AdminUser

        queryset = Role.objects.all()

        if isinstance(user, AdminUser):
            # Admin can see system roles + their organization's roles
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = queryset.filter(
                models.Q(organization__isnull=True) |  # System roles
                models.Q(organization_id__in=org_ids)  # Org roles
            )
        elif isinstance(user, Employee):
            # Employee can see system roles + their organization's roles
            queryset = queryset.filter(
                models.Q(organization__isnull=True) |  # System roles
                models.Q(organization=user.organization)  # Org roles
            )
        else:
            queryset = Role.objects.none()

        # Filter by query params
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
        """Set organization when creating a role"""
        user = self.request.user
        from core.models import AdminUser

        # Only non-system roles need an organization
        if not serializer.validated_data.get('is_system_role', False):
            if isinstance(user, AdminUser):
                # Use the first organization of the admin
                org = user.organizations.first()
                if org:
                    serializer.save(organization=org)
                else:
                    raise serializers.ValidationError("Admin user has no organization")
            elif isinstance(user, Employee):
                serializer.save(organization=user.organization)
            else:
                raise serializers.ValidationError("Cannot determine organization")
        else:
            serializer.save()


# -------------------------------
# ATTENDANCE VIEWS
# -------------------------------

class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance records"""
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceSerializer
    filterset_fields = ['employee', 'date', 'status', 'is_approved']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__employee_id']
    ordering_fields = ['date', 'check_in', 'check_out', 'total_hours']
    ordering = ['-date']

    def get_queryset(self):
        """Get attendance records based on user permissions"""
        user = self.request.user
        from core.models import AdminUser

        # Get organization from header
        organization_slug = self.request.headers.get('X-Organization-Slug')
        if not organization_slug:
            return Attendance.objects.none()

        try:
            organization = Organization.objects.get(subdomain=organization_slug)
        except Organization.DoesNotExist:
            return Attendance.objects.none()

        # Base queryset with related data filtered by organization
        queryset = Attendance.objects.filter(organization=organization).select_related(
            'employee', 'employee__department', 'approved_by', 'approved_by_admin'
        )

        # Filter based on user type and permissions
        if isinstance(user, AdminUser):
            # AdminUser can see all attendance in the organization
            pass  # Already filtered by organization
        elif isinstance(user, Employee):
            # Check if employee has permission to view all attendance
            if user.has_permission('can_view_all_attendance'):
                # Can see all attendance in organization
                pass
            else:
                # Otherwise, only show their own attendance
                queryset = queryset.filter(user_email=user.email)
        else:
            return Attendance.objects.none()

        # Filter by query params
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
        """Create attendance with permission check"""
        user = self.request.user
        from core.models import AdminUser

        # Check permissions
        if isinstance(user, Employee):
            if not user.has_permission('can_create_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You do not have permission to create attendance records')
        # AdminUser can always create

        serializer.save()

    def perform_update(self, serializer):
        """Update attendance with permission check"""
        user = self.request.user
        from core.models import AdminUser

        # Check permissions
        if isinstance(user, Employee):
            if not user.has_permission('can_update_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You do not have permission to update attendance records')
        # AdminUser can always update

        serializer.save()

    def perform_destroy(self, instance):
        """Delete attendance with permission check"""
        user = self.request.user
        from core.models import AdminUser

        # Check permissions
        if isinstance(user, Employee):
            if not user.has_permission('can_delete_attendance'):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You do not have permission to delete attendance records')
        # AdminUser can always delete

        instance.delete()

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        """
        Manual check-in endpoint - REQUIRES SPECIAL PERMISSION
        Normal employees should use QR code check-in instead
        Only administrators with 'can_manual_checkin' permission can use this
        """
        user = request.user
        from core.models import AdminUser

        # Check permission for manual check-in
        if isinstance(user, Employee):
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': 'Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, AdminUser):
            # AdminUser needs explicit permission too
            # You can add additional checks here if needed
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

        # Determine the organization
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

        # Handle different user types
        if isinstance(user, AdminUser):
            # AdminUser can check in for themselves OR for an employee
            employee_id = request.data.get('employee_id')

            if employee_id:
                # Admin checking in for an employee
                try:
                    employee = Employee.objects.get(id=employee_id, organization=organization)
                    # Use employee fields
                    user_email = employee.email
                    user_full_name = employee.get_full_name()
                except Employee.DoesNotExist:
                    return Response(
                        {'error': 'Employee not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Admin checking in for themselves
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

        # Check if already checked in today
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

        # Create or update attendance record
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
        Manual check-out endpoint - REQUIRES SPECIAL PERMISSION
        Normal employees should use QR code check-out instead
        Only administrators with 'can_manual_checkin' permission can use this
        """
        user = request.user
        from core.models import AdminUser

        # Check permission for manual check-out
        if isinstance(user, Employee):
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': 'Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif isinstance(user, AdminUser):
            # AdminUser can always check-out
            pass
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AttendanceCheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Determine the organization
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

        # Handle different user types
        if isinstance(user, AdminUser):
            # AdminUser can check out for themselves OR for an employee
            employee_id = request.data.get('employee_id')

            if employee_id:
                # Admin checking out for an employee
                try:
                    employee = Employee.objects.get(id=employee_id, organization=organization)
                    user_email = employee.email
                except Employee.DoesNotExist:
                    return Response(
                        {'error': 'Employee not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Admin checking out for themselves
                user_email = user.email

        elif isinstance(user, Employee):
            user_email = user.email
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Find today's attendance record
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

        # Update check-out time
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
        """Get today's attendance for the current user (Employee or AdminUser)"""
        user = request.user
        from core.models import AdminUser

        # Determine the organization
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

        # Get user email based on type
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
        """Approve or reject an attendance record"""
        user = request.user
        from core.models import AdminUser

        # Check if user has permission
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
        else:  # reject
            attendance.approval_status = 'rejected'
            attendance.is_approved = False
            attendance.rejection_reason = serializer.validated_data.get('rejection_reason', '')

        # Set who approved/rejected
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
        """Start a break for today's attendance"""
        user = request.user
        from core.models import AdminUser

        # Determine the organization
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

        # Get user email
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
        attendance.break_end = None  # Reset break_end
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='end-break')
    def end_break(self, request):
        """End the current break for today's attendance"""
        user = request.user
        from core.models import AdminUser

        # Determine the organization
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

        # Get user email
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
        attendance.calculate_hours()  # Recalculate hours with break
        attendance.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Get attendance statistics for an employee"""
        user = request.user

        # Get employee_id from query params or use current user
        employee_id = request.query_params.get('employee_id', None)

        if employee_id:
            # Check permission to view other's stats
            if isinstance(user, Employee) and not user.has_permission('can_view_all_attendance'):
                return Response(
                    {'error': 'You do not have permission to view other employees\' statistics'},
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

        # Get date range
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        queryset = Attendance.objects.filter(employee=employee)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Calculate statistics
        total_days = queryset.count()
        present_days = queryset.filter(status='present').count()
        absent_days = queryset.filter(status='absent').count()
        late_days = queryset.filter(status='late').count()
        half_days = queryset.filter(status='half_day').count()
        on_leave_days = queryset.filter(status='on_leave').count()

        # Calculate total hours
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
        """
        Create a QR code session for an employee
        Requires 'can_create_qr_session' permission
        """
        from core.models import AdminUser

        # Check permission: AdminUser always allowed, Employee needs permission
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

        # Get organization from header
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
        """
        Get QR code session details
        """
        # Get organization from header
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

    @action(detail=False, methods=['post'], url_path='qr-check-in', permission_classes=[])
    def qr_check_in(self, request):
        """
        Check in using QR code (Public endpoint - no authentication required)
        """
        # Get organization from header
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

        serializer = QRAttendanceCheckInSerializer(data=request.data)

        if serializer.is_valid():
            attendance = serializer.save()
            from .serializers import AttendanceSerializer
            response_serializer = AttendanceSerializer(attendance)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
