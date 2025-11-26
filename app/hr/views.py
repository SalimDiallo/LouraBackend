from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils import timezone

from core.models import Organization
from .models import (
    Employee, Department, Position, Contract,
    LeaveType, LeaveBalance, LeaveRequest,
    PayrollPeriod, Payslip
)
from .serializers import (
    EmployeeSerializer, EmployeeCreateSerializer, EmployeeListSerializer,
    EmployeeUpdateSerializer, EmployeeLoginSerializer, EmployeeChangePasswordSerializer,
    DepartmentSerializer, PositionSerializer, ContractSerializer,
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    PayrollPeriodSerializer, PayslipSerializer, PayslipCreateSerializer
)
from .permissions import (
    IsHRAdminOrReadOnly, IsHRAdmin,
    IsManagerOrHRAdmin, IsAdminUserOrEmployee
)


# -------------------------------
# JWT Cookie Helper Functions
# -------------------------------

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

            # Generate JWT tokens
            refresh = RefreshToken.for_user(employee)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Update last login
            employee.last_login = timezone.now()
            employee.save(update_fields=['last_login'])

            # Return employee data
            employee_data = EmployeeSerializer(employee).data

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

            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            response = Response({
                'message': 'Deconnexion reussie'
            }, status=status.HTTP_200_OK)

            clear_jwt_cookies(response)
            return response

        except Exception:
            response = Response({
                'error': 'Erreur lors de la deconnexion'
            }, status=status.HTTP_400_BAD_REQUEST)

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

        if isinstance(user, AdminUser):
            org_ids = user.organizations.values_list('id', flat=True)
            return Employee.objects.filter(organization_id__in=org_ids)
        elif isinstance(user, Employee):
            return Employee.objects.filter(organization=user.organization)

        return Employee.objects.none()

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
            if user.role == 'admin':
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
            if user.role == 'admin':
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
            if user.role in ['admin', 'manager']:
                return LeaveRequest.objects.filter(employee__organization=user.organization)
            return LeaveRequest.objects.filter(employee=user)
        return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        if isinstance(self.request.user, Employee):
            serializer.save(employee=self.request.user)
        else:
            raise serializers.ValidationError({'user': 'Seuls les employees peuvent creer des demandes'})

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrHRAdmin])
    def approve(self, request, pk=None):
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
            if user.role == 'admin':
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
