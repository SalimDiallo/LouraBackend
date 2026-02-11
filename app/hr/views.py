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

# PDF Generation
from inventory.pdf_base import PDFGeneratorMixin

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
    LeaveTypeSerializer, LeaveRequestSerializer,
    LeaveRequestApprovalSerializer,
    PayrollPeriodSerializer, PayslipSerializer, PayslipCreateSerializer,
    PayrollAdvanceSerializer, PayrollAdvanceCreateSerializer, PayrollAdvanceListSerializer,
    PayrollAdvanceApprovalSerializer,
    PermissionSerializer, RoleSerializer, RoleListSerializer, RoleCreateSerializer,
    AttendanceSerializer, AttendanceCreateSerializer, AttendanceCheckInSerializer,
    AttendanceCheckOutSerializer, AttendanceApprovalSerializer, AttendanceStatsSerializer
)

# Permissions (depuis le nouveau fichier unifié)
from .permissions import (
    IsHRAdmin,
    IsManagerOrHRAdmin, IsAdminUserOrEmployee,
    CanAccessOwnOrManage,
    RequiresEmployeePermission, RequiresDepartmentPermission,
    RequiresContractPermission,
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
# Note: Les services sont disponibles mais pas encore intégrés dans les views
# from .services import EmployeeService, LeaveService, PayrollService

# Utils centralisés
from authentication.utils import convert_uuids_to_strings

# Constants - Permissions et Rôles prédéfinis sont définis dans constants.py
# Usage: from hr.constants import PERMISSIONS, PREDEFINED_ROLES

# Module logger
logger = logging.getLogger(__name__)


# -------------------------------
# EMPLOYEE AUTHENTICATION VIEWS
# -------------------------------


class EmployeeChangePasswordView(APIView):
    """Change employee password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Vérifier que l'utilisateur est un Employee
        if getattr(request.user, 'user_type', None) != 'employee':
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
    view_permission = 'hr.view_employees'
    create_permission = 'hr.create_employees'
    activation_permission = 'hr.activate_employees'
    
    # Filtres et recherche (pour référence, filtrage manuel dans get_queryset)
    filterset_fields = ['department', 'position', 'employment_status', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']

    def get_queryset(self):
        """
        Retourne le queryset avec filtrage par organisation et filtres supplémentaires.
        """
        queryset = super().get_queryset()
        
        # Filtrage par département
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filtrage par position
        position = self.request.query_params.get('position')
        if position:
            queryset = queryset.filter(position_id=position)
        
        # Filtrage par statut d'emploi
        employment_status = self.request.query_params.get('employment_status')
        if employment_status:
            queryset = queryset.filter(employment_status=employment_status)
        
        # Filtrage par is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None and is_active != '':
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Recherche
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return queryset

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
    view_permission = 'hr.view_departments'
    create_permission = 'hr.create_departments'
    allow_list_without_permission = True  # Permet de lister pour les dropdowns

    @action(detail=True, methods=['post'] , url_path='deactivate')
    def deactivate(self, request, pk=None):
        """Désactive un département."""
        return super().deactivate(request, pk)

    @action(detail=True, methods=['post'] , url_path='activate')
    def activate(self, request, pk=None):
        """Active un département."""
        return super().activate(request, pk)

    def destroy(self, request, *args, **kwargs):
        """
        Supprime un département.
        
        Vérifie qu'aucun employé n'est associé au département avant suppression.
        """
        department = self.get_object()
        
        # Vérifier s'il y a des employés associés
        employee_count = department.employees.count()
        if employee_count > 0:
            return Response(
                {
                    'error': f'Impossible de supprimer ce département. '
                             f'{employee_count} employé(s) y sont encore affecté(s). '
                             f'Veuillez d\'abord réaffecter ou supprimer ces employés.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


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
    view_permission = 'hr.view_positions'
    create_permission = 'hr.create_positions'
    allow_list_without_permission = True  # Permet de lister pour les dropdowns



class ContractViewSet(PDFGeneratorMixin, BaseOrganizationViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des contrats.
    
    Règle métier importante : Un employé ne peut avoir qu'un seul contrat actif
    à un instant donné. L'activation d'un contrat désactive automatiquement
    les autres contrats de l'employé.
    
    Note: Ce ViewSet surcharge perform_create car Contract n'a pas de champ
    organization direct - il est lié via employee.organization.
    """
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresContractPermission]
    
    # Configuration du mixin - les contrats sont liés à employee.organization
    organization_field = 'employee__organization'
    view_permission = 'hr.view_contracts'
    create_permission = 'hr.create_contracts'

    def perform_create(self, serializer):
        """
        Crée un contrat sans passer organization (Contract n'a pas ce champ).
        Valide que l'employé appartient à l'organisation de l'utilisateur.
        """
        from rest_framework import serializers as drf_serializers
        
        user = self.request.user
        user_type = getattr(user, 'user_type', None)
        
        # Vérifier la permission pour Employee
        if user_type == 'employee' and self.create_permission:
            if not user.has_permission(self.create_permission):
                raise drf_serializers.ValidationError({'permission': 'Permission refusée'})
        
        # Valider que l'employé appartient à l'organisation de l'utilisateur
        employee = serializer.validated_data.get('employee')
        if employee:
            if user_type == 'admin':
                if not user.organizations.filter(id=employee.organization_id).exists():
                    raise drf_serializers.ValidationError({
                        'employee': "Cet employé n'appartient pas à vos organisations"
                    })
            elif user_type == 'employee':
                if user.organization != employee.organization:
                    raise drf_serializers.ValidationError({
                        'employee': "Cet employé n'appartient pas à votre organisation"
                    })
        
        # Sauvegarder sans passer organization
        serializer.save()

    def get_queryset(self):
        user = self.request.user
        employee_id = self.request.query_params.get('employee')
        
        # Filtrer par subdomain d'organisation si fourni en paramètre de requête
        org_subdomain = self.request.query_params.get('organization_subdomain')
        if org_subdomain:
            queryset = Contract.objects.filter(employee__organization__subdomain=org_subdomain)
            return queryset.select_related('employee')

        if getattr(user, 'user_type', None) == 'admin':
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = Contract.objects.filter(employee__organization_id__in=org_ids)
        elif getattr(user, 'user_type', None) == 'employee':
            if user.has_permission("can_view_contract"):
                if user.is_hr_admin():
                    queryset = Contract.objects.filter(employee__organization=user.organization)
                else:
                    queryset = Contract.objects.filter(employee=user)
            else:
                queryset = Contract.objects.none()
        else:
            queryset = Contract.objects.none()

        # Filtrer par employé si spécifié
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        

        
        # Filtrer par statut actif si spécifié
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.select_related('employee')

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """
        Active ce contrat.
        
        Règle métier : L'activation d'un contrat désactive automatiquement
        tous les autres contrats actifs de l'employé.
        """
        contract = self.get_object()
        
        if contract.is_active:
            return Response(
                {'message': 'Ce contrat est déjà actif'},
                status=status.HTTP_200_OK
            )
        
        # La méthode activate() du modèle gère la désactivation des autres contrats
        contract.activate()

        # --- Notification vers l'employé : nouveau contrat actif ---
        try:
            from notifications.notification_helpers import send_notification
            send_notification(
                organization=contract.employee.organization,
                recipient=contract.employee,
                sender=request.user,
                title="Nouveau contrat actif",
                message=(
                    f"Votre contrat a été activé. "
                    f"Les autres contrats précédents ont été désactivés automatiquement."
                ),
                notification_type='user',
                priority='medium',
                entity_type='contract',
                entity_id=str(contract.id),
            )
        except Exception:
            pass

        serializer = self.get_serializer(contract)
        return Response({
            'message': f'Contrat activé avec succès. Les autres contrats de {contract.employee.get_full_name()} ont été désactivés.',
            'contract': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        """
        Désactive ce contrat.
        
        Note : Si c'était le seul contrat actif, l'employé n'aura plus de contrat actif.
        """
        contract = self.get_object()
        
        if not contract.is_active:
            return Response(
                {'message': 'Ce contrat est déjà inactif'},
                status=status.HTTP_200_OK
            )
        
        contract.deactivate()
        
        serializer = self.get_serializer(contract)
        return Response({
            'message': 'Contrat désactivé avec succès',
            'contract': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='active/(?P<employee_id>[^/.]+)')
    def get_active_for_employee(self, request, employee_id=None):
        """
        Retourne le contrat actif d'un employé.
        
        Returns 404 si l'employé n'a pas de contrat actif.
        """
        try:
            from .models import Employee
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employé non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier les permissions
        user = request.user
        if getattr(user, 'user_type', None) == 'admin':
            if not user.organizations.filter(id=employee.organization_id).exists():
                return Response(
                    {'error': 'Accès non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'employee':
            if user.organization != employee.organization:
                return Response(
                    {'error': 'Accès non autorisé'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        active_contract = Contract.get_active_contract(employee)
        
        if not active_contract:
            return Response(
                {'message': 'Aucun contrat actif pour cet employé', 'contract': None},
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(active_contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export a contract as PDF - supports preview mode"""
        from .pdf_generator import generate_contract_pdf

        contract = self.get_object()

        employee_name = contract.employee.get_full_name().replace(' ', '_')
        contract_type = contract.contract_type.upper()
        filename = f"Contrat_{contract_type}_{employee_name}.pdf"

        return self.generate_and_respond(
            generator_func=generate_contract_pdf,
            generator_args=(contract,),
            filename=filename,
            request=request
        )


# -------------------------------
# LEAVE MANAGEMENT VIEWS
# -------------------------------

class LeaveTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave types"""
    serializer_class = LeaveTypeSerializer
    # Remove RequiresLeavePermission for listing; set permissions for modification only
    permission_classes = [IsAdminUserOrEmployee]

    def get_queryset(self):
        user = self.request.user
        
        # Accès selon le type d'utilisateur
        if getattr(user, 'user_type', None) == 'admin':
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = LeaveType.objects.filter(organization_id__in=org_ids)
        elif getattr(user, 'user_type', None) == 'employee':
            queryset = LeaveType.objects.filter(organization=user.organization)
        else:
            queryset = LeaveType.objects.none()
        
        org_subdomain = self.request.query_params.get('organization_subdomain') or self.request.data.get('organization_subdomain')

        # Si le subdomain d'organisation est fourni en paramètre de requête
        if org_subdomain:
            queryset = LeaveType.objects.filter(organization__subdomain=org_subdomain)
        else:
            raise serializers.ValidationError({'organization_subdomain': "Subdomain d'organisation requis"})


        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if getattr(user, 'user_type', None) == 'admin':
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
        elif getattr(user, 'user_type', None) == 'employee':
            if not user.has_permission("hr.manage_leave_types"):
                raise serializers.ValidationError({'permission': 'Permission refusée'})
            organization = user.organization
        else:
            raise serializers.ValidationError({'user': 'Non autorisé'})

        serializer.save(organization=organization)


# class LeaveBalanceViewSet(viewsets.ModelViewSet):
#     """ViewSet for managing leave balances"""
#     serializer_class = LeaveBalanceSerializer
#     permission_classes = [IsAdminUserOrEmployee, CanAccessOwnOrManage.for_resource('leave', 'can_manage_leave_balances')]

#     def get_queryset(self):
#         user = self.request.user

#         if getattr(user, 'user_type', None) == 'admin':
#             org_ids = user.organizations.values_list('id', flat=True)
#             return LeaveBalance.objects.filter(employee__organization_id__in=org_ids)
#         elif getattr(user, 'user_type', None) == 'employee':
#             if user.has_permission("hr.manage_leave_balances") or user.is_hr_admin():
#                 return LeaveBalance.objects.filter(employee__organization=user.organization)
#             return LeaveBalance.objects.filter(employee=user)
#         return LeaveBalance.objects.none()


class LeaveRequestViewSet(PDFGeneratorMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing leave requests.
    Tous les employés peuvent créer une demande de congé.
    Seule l'approbation (et rejet) requiert des permissions spéciales.
    La liste de toutes les demandes n'est visible que si on a la permission hr.view_leave.
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAdminUserOrEmployee]

    def get_queryset(self):
        """
        Retourne le queryset de LeaveRequest accessible à l'utilisateur courant.
        Note IMPORTANTE :
          - Par défaut, DRF appelle get_queryset() même pour les endpoints retrieve (détail: /pk/).
          - Si le queryset exclut l'objet demandé (ex: simple employé ne voit pas ses propres demandes dans la liste),
            alors une requête GET /leave-requests/{id}/ retournera 404: No LeaveRequest matches the given query.
        
        Ce comportement arrive car DRF fait un filter(pk=...) sur le queryset retourné ici.
        """
        user = self.request.user
        org_subdomain = self.request.query_params.get('organization_subdomain')
        
        if getattr(user, 'user_type', None) == 'admin':
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = LeaveRequest.objects.filter(employee__organization_id__in=org_ids)
            
            # Filter by specific organization if subdomain provided
            if org_subdomain:
                queryset = queryset.filter(employee__organization__subdomain=org_subdomain)
            
            return queryset
        elif getattr(user, 'user_type', None) == 'employee':
            if user.has_permission("hr.view_leave_requests"):
                # INSERT_YOUR_CODE
                exclude = self.request.query_params.get('exclude')
                queryset = LeaveRequest.objects.filter(employee__organization=user.organization)
                if exclude:
                    queryset = queryset.exclude(employee=user)
                return queryset
            
            # On veut permettre à l'employé de voir ses propres demandes dans retrieve OU destroy
            # Récriture ici: pour retrieve et destroy, inclure LeaveRequest de l'utilisateur
            if self.action in ["retrieve", "destroy"]:
                return LeaveRequest.objects.filter(employee=user)
            return LeaveRequest.objects.none()
        return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'employee':
            # Toute employé peut créer une demande, sans permission spécifique
            leave_request = serializer.save(employee=user)
        elif getattr(user, 'user_type', None) == 'admin':
            # AdminUser créant une demande pour un employé spécifique
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
        user = self.request.user
        # Si employé: peut supprimer sa propre demande uniquement si non approuvée
        if getattr(user, 'user_type', None) == 'employee':
            if instance.employee != user:
                raise serializers.ValidationError({'detail': "Vous ne pouvez supprimer que vos propres demandes."})
            if instance.status == 'approved':
                raise serializers.ValidationError({'detail': "Impossible de supprimer une demande déjà approuvée."})
        # Si admin, il peut supprimer toute demande

        # Mise à jour LeaveBalance que si la demande est encore pending ou rejetée mais pas approuvée
        if instance.status == 'pending' or instance.status == 'rejected':
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

            # --- Notification vers l'employé : congé approuvé ---
            try:
                from notifications.notification_helpers import send_notification
                send_notification(
                    organization=leave_request.employee.organization,
                    recipient=leave_request.employee,
                    sender=request.user,
                    title="Congé approuvé",
                    message=(
                        f"Votre demande de congé du {leave_request.start_date} "
                        f"au {leave_request.end_date} a été approuvée."
                    ),
                    notification_type='user',
                    priority='medium',
                    entity_type='leave_request',
                    entity_id=str(leave_request.id),
                )
            except Exception:
                pass

            return Response({'message': 'Demande approuvée'}, status=status.HTTP_200_OK)

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

            # --- Notification vers l'employé : congé rejeté ---
            try:
                from notifications.notification_helpers import send_notification
                notes = leave_request.approval_notes or "Aucun commentaire."
                send_notification(
                    organization=leave_request.employee.organization,
                    recipient=leave_request.employee,
                    sender=request.user,
                    title="Congé rejeté",
                    message=(
                        f"Votre demande de congé du {leave_request.start_date} "
                        f"au {leave_request.end_date} a été rejetée. Motif : {notes}"
                    ),
                    notification_type='user',
                    priority='high',
                    entity_type='leave_request',
                    entity_id=str(leave_request.id),
                )
            except Exception:
                pass

            return Response({'message': 'Demande rejetée'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export a leave request as PDF - supports preview mode"""
        from .pdf_generator import generate_leave_request_pdf

        leave_request = self.get_object()

        employee_name = leave_request.employee.get_full_name().replace(' ', '_')
        filename = f"Conge_{employee_name}_{leave_request.start_date.strftime('%Y%m%d')}.pdf"

        return self.generate_and_respond(
            generator_func=generate_leave_request_pdf,
            generator_args=(leave_request,),
            filename=filename,
            request=request
        )

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """
        Endpoint qui retourne l'historique paginé et filtrable des demandes de congé de l'utilisateur courant (employé).
        - Seul un employé peut voir son historique.
        - Un admin a une réponse vide.
        """
        user = request.user
        if not hasattr(user, "user_type") or user.user_type not in ("employee", "admin"):
            return Response({'detail': 'Utilisateur non autorisé'}, status=status.HTTP_403_FORBIDDEN)

        # Seul l'employé peut voir son propre historique
        if user.user_type == "employee":
            qs = LeaveRequest.objects.filter(employee=user)
        else:
            # Admin: réponse vide
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }, status=status.HTTP_200_OK)

        # Optional filters
        status_param = request.query_params.get('status')
        leave_type_param = request.query_params.get('leave_type')
        start_date_param = request.query_params.get('start_date')
        end_date_param = request.query_params.get('end_date')

        if status_param:
            qs = qs.filter(status=status_param)
        if leave_type_param:
            qs = qs.filter(leave_type=leave_type_param)
        if start_date_param:
            qs = qs.filter(start_date__gte=start_date_param)
        if end_date_param:
            qs = qs.filter(end_date__lte=end_date_param)

        # Pagination
        page = self.paginate_queryset(qs.order_by('-start_date'))
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(qs.order_by('-start_date'), many=True)
            return Response({
                "count": qs.count(),
                "next": None,
                "previous": None,
                "results": serializer.data,
            })


# -------------------------------
# PAYROLL VIEWS
# -------------------------------

class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payroll periods"""
    serializer_class = PayrollPeriodSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresPayrollPermission]

    def get_queryset(self):
        user = self.request.user
        org_subdomain = self.request.query_params.get('organization_subdomain') or self.request.data.get('organization_subdomain')

        if getattr(user, 'user_type', None) == 'admin':
            # L'admin peut accéder aux périodes de paie de ses organisations
            if org_subdomain:
                # Filtrer par l'organisation spécifiée ET vérifier que l'admin y a accès
                try:
                    organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                    return PayrollPeriod.objects.filter(organization=organization)
                except Organization.DoesNotExist:
                    return PayrollPeriod.objects.none()
            else:
                # Sans subdomain, retourner toutes les périodes de toutes ses organisations
                org_ids = user.organizations.values_list('id', flat=True)
                return PayrollPeriod.objects.filter(organization_id__in=org_ids)

        elif getattr(user, 'user_type', None) == 'employee':
            # L'employé doit avoir la permission et ne peut voir que son organisation
            if not user.has_permission("can_view_payroll"):
                return PayrollPeriod.objects.none()
            return PayrollPeriod.objects.filter(organization=user.organization)

        return PayrollPeriod.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if getattr(user, 'user_type', None) == 'admin':
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

        elif getattr(user, 'user_type', None) == 'employee':
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


class PayslipViewSet(PDFGeneratorMixin, viewsets.ModelViewSet):
    """ViewSet for managing payslips
    
    Règles métier:
    - Tout utilisateur peut voir ses propres fiches de paie (via history)
    - Un utilisateur avec hr.view_payroll peut voir toutes les fiches de l'organisation
    - Un utilisateur avec hr.process_payroll peut marquer les paies comme payées
    - Un utilisateur NE PEUT PAS marquer ses propres paies comme payées
    - L'endpoint 'history' retourne uniquement les fiches de l'utilisateur connecté
    """
    permission_classes = [IsAdminUserOrEmployee, CanAccessOwnOrManage.for_resource('payroll', 'can_view_payroll')]

    def get_serializer_class(self):
        if self.action == 'create':
            return PayslipCreateSerializer
        return PayslipSerializer

    def get_queryset(self):
        user = self.request.user
        exclude_own = self.request.query_params.get('exclude_own')  # Nouveau: exclure ses propres

        # Base queryset selon le type d'utilisateur
        org_subdomain = self.request.query_params.get('organization_subdomain')
        if org_subdomain:
            queryset = Payslip.objects.filter(employee__organization__subdomain=org_subdomain)
        else:
            raise serializers.ValidationError({'permission': "Subdomain d'organisation requis"})
        
        if getattr(user, 'user_type', None) == 'admin':
            org_ids = user.organizations.values_list('id', flat=True)
            queryset = Payslip.objects.filter(employee__organization_id__in=org_ids)
            queryset = Payslip.objects.filter(employee__organization__subdomain=org_subdomain)
            return queryset

        if getattr(user, 'user_type', None) == 'employee':
            if user.has_permission("hr.view_payroll") or user.is_hr_admin():
                queryset = Payslip.objects.filter(employee__organization=user.organization)
                # Optionnel: exclure ses propres fiches de la liste globale
                if exclude_own and exclude_own.lower() == 'true':
                    queryset = queryset.exclude(employee=user)
            else:
                # Utilisateur sans permission: uniquement ses propres fiches
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

        return queryset.select_related('employee', 'payroll_period')

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """Endpoint pour voir l'historique de ses propres fiches de paie.
        
        Retourne uniquement les fiches de l'utilisateur connecté.
        Supporte la pagination et le filtrage par statut.
        """
        user = request.user
        
        if getattr(user, 'user_type', None) == 'employee':
            queryset = Payslip.objects.filter(employee=user)
        elif getattr(user, 'user_type', None) == 'admin':
            # Admin n'a pas de fiches personnelles
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Utilisateur non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        # Filtrage optionnel par statut
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        queryset = queryset.order_by('-created_at').select_related('payroll_period')
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PayslipSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PayslipSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "next": None,
            "previous": None,
            "results": serializer.data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def mark_as_paid(self, request, pk=None):
        """Marquer une fiche de paie comme payée
        
        Règles:
        - Requiert la permission hr.process_payroll ou être admin
        - Un utilisateur NE PEUT PAS marquer sa propre paie comme payée
        """
        payslip = self.get_object()
        user = request.user
        
        # Vérifier que l'utilisateur ne tente pas de marquer sa propre paie
        if getattr(user, 'user_type', None) == 'employee':
            if payslip.employee == user:
                return Response(
                    {'error': 'Vous ne pouvez pas marquer votre propre paie comme payée'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not (user.has_permission("hr.process_payroll") or user.is_hr_admin()):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de traiter les paies'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        payslip.status = 'paid'
        payslip.payment_date = timezone.now().date()
        payslip.payment_reference = request.data.get('payment_reference', '')
        payslip.save()

        # --- Notification vers l'employé : paie payée ---
        try:
            from notifications.notification_helpers import send_notification
            send_notification(
                organization=payslip.employee.organization,
                recipient=payslip.employee,
                sender=request.user,
                title="Fiche de paie payée",
                message=(
                    f"Votre fiche de paie pour la période "
                    f"{payslip.payroll_period.name} a été marquée comme payée."
                ),
                notification_type='user',
                priority='medium',
                entity_type='payslip',
                entity_id=str(payslip.id),
            )
        except Exception:
            pass

        return Response({'message': 'Fiche marquée comme payée'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[IsAdminUserOrEmployee], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export payslip as PDF - supports preview mode"""
        from .pdf_generator import generate_payslip_pdf


        payslip = self.get_object()

        # Handle both period-based and ad-hoc payslips
        period_part = payslip.payroll_period.name if payslip.payroll_period else payslip.description or 'AdHoc'
        filename = f"Fiche_Paie_{payslip.employee.get_full_name().replace(' ', '_')}_{period_part.replace(' ', '_')}.pdf"

        return self.generate_and_respond(
            generator_func=generate_payslip_pdf,
            generator_args=(payslip,),
            filename=filename,
            request=request
        )

    @action(detail=False, methods=['post'], permission_classes=[IsHRAdmin])
    def generate_for_period(self, request):
        """Génération intelligente de fiches de paie avec déduction automatique des avances
        
        Supporte maintenant:
        - Période optionnelle (mode ad-hoc)
        - Données personnalisées par employé (salaire de base, notes, primes, déductions, avances)
        """

        payroll_period_id = request.data.get('payroll_period')
        employee_filters = request.data.get('employee_filters', {})
        auto_deduct_advances = request.data.get('auto_deduct_advances', True)
        auto_approve = request.data.get('auto_approve', False)
        employee_ids = request.data.get('employee_ids', [])
        
        # ✨ Nouvelles données personnalisées par employé
        # Format: { employee_id: { base_salary, notes, allowances, deductions, advance_ids } }
        employee_custom_data = request.data.get('employee_custom_data', {})
        
        # ✨ Organization subdomain pour mode ad-hoc (sans période)
        org_subdomain = request.query_params.get('organization_subdomain')

        # Récupérer la période (optionnelle maintenant)
        payroll_period = None
        organization = None
        
        if payroll_period_id:
            try:
                payroll_period = PayrollPeriod.objects.get(id=payroll_period_id)
                organization = payroll_period.organization
            except PayrollPeriod.DoesNotExist:
                return Response(
                    {'error': 'Période de paie non trouvée'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Mode ad-hoc: récupérer l'organisation depuis le subdomain
            if not org_subdomain:
                return Response(
                    {'error': 'organization_subdomain est requis en mode ad-hoc (sans période)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                user = request.user
                if getattr(user, 'user_type', None) == 'admin':
                    organization = Organization.objects.get(subdomain=org_subdomain, admin=user)
                elif getattr(user, 'user_type', None) == 'employee':
                    organization = Organization.objects.get(subdomain=org_subdomain)
                    if organization != user.organization:
                        return Response(
                            {'error': 'Accès non autorisé à cette organisation'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    return Response(
                        {'error': 'Type d\'utilisateur non autorisé'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Organization.DoesNotExist:
                return Response(
                    {'error': 'Organisation non trouvée'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Filtrer par IDs spécifiques si fournis, sinon tous les employés actifs
        if employee_ids:
            employees = Employee.objects.filter(
                organization=organization,
                id__in=employee_ids,
                employment_status='active'
            )
        else:
            employees = Employee.objects.filter(
                organization=organization,
                employment_status='active'
            )

        # Appliquer les filtres additionnels
        if employee_filters.get('department'):
            employees = employees.filter(department_id=employee_filters['department'])
        if employee_filters.get('position'):
            employees = employees.filter(position_id=employee_filters['position'])

        created_count = 0
        skipped_count = 0
        advances_deducted = 0
        errors = []

        for employee in employees:
            # Vérifier si fiche existe déjà (seulement si période spécifiée)
            if payroll_period and Payslip.objects.filter(employee=employee, payroll_period=payroll_period).exists():
                skipped_count += 1
                logger.info(f"Payslip already exists for {employee.get_full_name()}")
                continue

            try:
                # Récupérer le contrat actif
                contract = employee.contracts.filter(is_active=True).first()
                if not contract:
                    errors.append(f"{employee.get_full_name()}: Pas de contrat actif")
                    continue

                # ✨ Données personnalisées pour cet employé
                custom_data = employee_custom_data.get(str(employee.id), {})
                
                # Salaire de base (personnalisé ou du contrat)
                base_salary = Decimal(str(custom_data.get('base_salary'))) if custom_data.get('base_salary') is not None else contract.base_salary
                currency = contract.currency
                
                # Notes/description
                description = custom_data.get('notes', '')

                # ✨ Primes personnalisées
                custom_allowances = custom_data.get('allowances', [])
                total_allowances = Decimal('0')
                allowance_items = []
                for allowance in custom_allowances:
                    amount = Decimal(str(allowance.get('amount', 0)))
                    total_allowances += amount
                    allowance_items.append({
                        'name': allowance.get('name', 'Prime'),
                        'amount': amount,
                        'is_deduction': False,
                    })

                # ✨ Déductions personnalisées
                custom_deductions = custom_data.get('deductions', [])
                total_custom_deductions = Decimal('0')
                deduction_items = []
                for deduction in custom_deductions:
                    amount = Decimal(str(deduction.get('amount', 0)))
                    total_custom_deductions += amount
                    deduction_items.append({
                        'name': deduction.get('name', 'Déduction'),
                        'amount': amount,
                        'is_deduction': True,
                    })

                # ✨ Avances sélectionnées manuellement ou auto-déduction
                selected_advance_ids = custom_data.get('advance_ids', [])
                paid_advances = []
                advance_deduction_items = []
                total_advance_amount = Decimal('0')

                if selected_advance_ids:
                    # Utiliser les avances sélectionnées manuellement
                    paid_advances = PayrollAdvance.objects.filter(
                        id__in=selected_advance_ids,
                        employee=employee,
                        status=PayrollAdvance.AdvanceStatus.APPROVED,
                        payslip__isnull=True
                    )
                elif auto_deduct_advances:
                    # Auto-déduire toutes les avances approuvées non déduites
                    paid_advances = PayrollAdvance.objects.filter(
                        employee=employee,
                        status=PayrollAdvance.AdvanceStatus.APPROVED,
                        payslip__isnull=True
                    )

                for advance in paid_advances:
                    advance_deduction_items.append({
                        'name': f'Remboursement avance - {advance.reason[:30] if advance.reason else "Avance"}',
                        'amount': advance.amount,
                        'is_deduction': True,
                    })
                    total_advance_amount += advance.amount
                    logger.info(f"Deducting advance {advance.id} ({advance.amount}) for {employee.get_full_name()}")

                # Calculer totaux
                gross_salary = base_salary + total_allowances
                total_deductions = total_custom_deductions + total_advance_amount
                net_salary = gross_salary - total_deductions
                
                # Vérifier que le net n'est pas négatif
                if net_salary < 0:
                    errors.append(f"{employee.get_full_name()}: Le salaire net serait négatif ({net_salary})")
                    continue

                # Déterminer le statut initial
                initial_status = 'approved' if auto_approve else 'draft'

                # Créer la fiche de paie
                payslip = Payslip.objects.create(
                    employee=employee,
                    payroll_period=payroll_period,  # Peut être None en mode ad-hoc
                    base_salary=base_salary,
                    description=description,
                    currency=currency,
                    gross_salary=gross_salary,
                    total_deductions=total_deductions,
                    net_salary=net_salary,
                    status=initial_status
                )

                # Créer les items (primes)
                for item in allowance_items:
                    PayslipItem.objects.create(payslip=payslip, **item)

                # Créer les items (déductions)
                for item in deduction_items:
                    PayslipItem.objects.create(payslip=payslip, **item)

                # Créer les items (avances)
                for item in advance_deduction_items:
                    PayslipItem.objects.create(payslip=payslip, **item)

                # Lier les avances à la fiche et marquer comme déduites
                if paid_advances:
                    for advance in paid_advances:
                        advance.status = PayrollAdvance.AdvanceStatus.DEDUCTED
                        advance.payslip = payslip
                        advance.deduction_month = payroll_period.end_date if payroll_period else timezone.now().date()
                        advance.save()
                        advances_deducted += 1

                created_count += 1
                logger.info(f"Created payslip for {employee.get_full_name()} with {len(list(paid_advances))} advances deducted (status: {initial_status})")

            except Exception as e:
                logger.exception(f"Error creating payslip for {employee.get_full_name()}")
                errors.append(f"{employee.get_full_name()}: {str(e)}")

        return Response({
            'message': f'{created_count} fiches de paie créées avec {advances_deducted} avance(s) déduite(s) automatiquement',
            'created': created_count,
            'skipped': skipped_count,
            'total_employees': employees.count(),
            'advances_deducted': advances_deducted,
            'auto_approved': auto_approve,
            'ad_hoc_mode': payroll_period is None,
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
        if getattr(user, 'user_type', None) == 'admin':
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'employee':
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
        if getattr(user, 'user_type', None) == 'admin':
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'employee':
            if user.organization != organization or not user.has_permission("hr.view_employees"):
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

        # Contract stats
        contracts = Contract.objects.filter(employee__organization=organization)
        total_contracts = contracts.count()
        active_contracts = contracts.filter(is_active=True).count()
        # Contracts expiring within 30 days
        thirty_days_from_now = now + timedelta(days=30)
        expiring_contracts = contracts.filter(
            is_active=True,
            end_date__isnull=False,
            end_date__lte=thirty_days_from_now.date(),
            end_date__gte=now.date()
        ).count()

        # Payroll trend (last 6 months)
        payroll_trend = []
        for i in range(5, -1, -1):
            # Calculate the month
            month_date = now - timedelta(days=i * 30)  # Approximate
            target_year = month_date.year
            target_month = month_date.month
            
            # Get payrolls for this month
            month_payrolls = Payslip.objects.filter(
                employee__organization=organization,
                payroll_period__start_date__year=target_year,
                payroll_period__start_date__month=target_month
            )
            
            month_aggregates = month_payrolls.aggregate(
                total=models.Sum('net_salary'),
                count=models.Count('id')
            )
            
            payroll_trend.append({
                'month': month_date.strftime('%b'),
                'full_month': month_date.strftime('%B %Y'),
                'year': target_year,
                'month_number': target_month,
                'montant': float(month_aggregates['total'] or 0),
                'employes': month_aggregates['count'] or 0,
            })

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
            # Contract stats
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'expiring_contracts': expiring_contracts,
            # Payroll trend
            'payroll_trend': payroll_trend,
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
        if getattr(user, 'user_type', None) == 'admin':
            if not user.organizations.filter(id=organization.id).exists():
                return Response(
                    {'error': 'Accès non autorisé à cette organisation'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'employee':
            print(user.get_all_permissions)
            if user.organization != organization or not user.has_permission("hr.view_departments"):
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
    """ViewSet for managing payroll advance requests
    
    Règles métier:
    - Tout utilisateur peut créer une demande d'avance pour lui-même
    - Un utilisateur avec hr.view_payroll peut voir toutes les avances de l'organisation
    - Un utilisateur avec hr.approve_payroll peut approuver/rejeter les avances
    - Un utilisateur NE PEUT PAS approuver/rejeter ses propres avances
    - Tout utilisateur peut voir/modifier/supprimer ses propres demandes (si pending)
    - L'endpoint 'history' retourne uniquement les avances de l'utilisateur connecté
    """
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
        exclude_own = self.request.query_params.get('exclude_own')  # Nouveau: exclure ses propres

        queryset = PayrollAdvance.objects.all()

        if getattr(user, 'user_type', None) == 'admin':
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
        elif getattr(user, 'user_type', None) == 'employee':
            # Utilisateur avec permission view_payroll voit toutes les avances de l'organisation
            if user.has_permission("hr.view_payroll") or user.is_hr_admin():
                queryset = queryset.filter(employee__organization=user.organization)
                # Optionnel: exclure ses propres demandes de la liste globale
                if exclude_own and exclude_own.lower() == 'true':
                    queryset = queryset.exclude(employee=user)
            else:
                # Utilisateur sans permission: uniquement ses propres demandes
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

    def perform_create(self, serializer):
        """Crée une demande d'avance.
        
        Règles:
        - Par défaut, crée une demande pour l'utilisateur connecté (s'il est un employé)
        - Un admin ou utilisateur avec permission peut créer une demande pour n'importe quel employé
        """
        user = self.request.user
        employee_id = self.request.data.get('employee')
        
        if getattr(user, 'user_type', None) == 'employee':
            if employee_id and str(employee_id) != str(user.id):
                # L'employé veut créer une demande pour quelqu'un d'autre
                if not (user.has_permission("hr.create_payroll") or user.is_hr_admin()):
                    raise serializers.ValidationError({
                        'employee': 'Vous ne pouvez créer des demandes que pour vous-même'
                    })
                # Vérifier que l'employé cible est dans la même organisation
                try:
                    target_employee = Employee.objects.get(id=employee_id, organization=user.organization)
                    serializer.save(employee=target_employee)
                except Employee.DoesNotExist:
                    raise serializers.ValidationError({
                        'employee': 'Employé introuvable dans votre organisation'
                    })
            else:
                # Demande pour soi-même
                serializer.save(employee=user)
        elif getattr(user, 'user_type', None) == 'admin':
            if not employee_id:
                raise serializers.ValidationError({
                    'employee': 'L\'employé est requis pour créer une demande d\'avance'
                })
            try:
                org_ids = user.organizations.values_list('id', flat=True)
                target_employee = Employee.objects.get(id=employee_id, organization_id__in=org_ids)
                serializer.save(employee=target_employee)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({
                    'employee': 'Employé introuvable'
                })
        else:
            raise serializers.ValidationError({
                'user': 'Type d\'utilisateur non autorisé'
            })

    def perform_update(self, serializer):
        """Met à jour une demande d'avance.
        
        Règles:
        - Un utilisateur peut modifier sa propre demande uniquement si elle est en statut 'pending'
        - Un utilisateur avec permission peut modifier n'importe quelle demande
        """
        user = self.request.user
        instance = self.get_object()
        
        if getattr(user, 'user_type', None) == 'employee':
            if instance.employee == user:
                # C'est sa propre demande
                if instance.status != 'pending':
                    raise serializers.ValidationError({
                        'detail': 'Vous ne pouvez modifier que vos demandes en attente'
                    })
            elif not (user.has_permission("hr.update_payroll") or user.is_hr_admin()):
                raise serializers.ValidationError({
                    'detail': 'Vous n\'avez pas la permission de modifier cette demande'
                })
        
        serializer.save()

    def perform_destroy(self, instance):
        """Supprime une demande d'avance.
        
        Règles:
        - Un utilisateur peut supprimer sa propre demande uniquement si elle est en statut 'pending'
        - Un utilisateur avec permission peut supprimer n'importe quelle demande pending ou rejected
        """
        user = self.request.user
        
        if getattr(user, 'user_type', None) == 'employee':
            if instance.employee == user:
                # C'est sa propre demande
                if instance.status != 'pending':
                    raise serializers.ValidationError({
                        'detail': 'Vous ne pouvez supprimer que vos demandes en attente'
                    })
            elif not (user.has_permission("hr.delete_payroll") or user.is_hr_admin()):
                raise serializers.ValidationError({
                    'detail': 'Vous n\'avez pas la permission de supprimer cette demande'
                })
            elif instance.status in ['approved', 'deducted']:
                raise serializers.ValidationError({
                    'detail': 'Impossible de supprimer une avance approuvée ou déduite'
                })
        
        instance.delete()

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """Endpoint pour voir l'historique de ses propres demandes d'avance.
        
        Retourne uniquement les avances de l'utilisateur connecté.
        Supporte la pagination et le filtrage par statut.
        """
        user = request.user
        
        if getattr(user, 'user_type', None) == 'employee':
            queryset = PayrollAdvance.objects.filter(employee=user)
        elif getattr(user, 'user_type', None) == 'admin':
            # Admin n'a pas d'avances personnelles
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Utilisateur non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        
        # Filtrage optionnel par statut
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        queryset = queryset.order_by('-request_date', '-created_at')
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PayrollAdvanceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PayrollAdvanceListSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "next": None,
            "previous": None,
            "results": serializer.data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def approve(self, request, pk=None):
        """Approuver une demande d'avance
        
        Règles:
        - Requiert la permission hr.approve_payroll ou être admin
        - Un utilisateur NE PEUT PAS approuver sa propre demande
        """
        advance = self.get_object()
        user = request.user

        # Vérifier que l'utilisateur ne tente pas d'approuver sa propre demande
        if getattr(user, 'user_type', None) == 'employee':
            if advance.employee == user:
                return Response(
                    {'error': 'Vous ne pouvez pas approuver votre propre demande d\'avance'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not (user.has_permission("hr.approve_payroll") or user.is_hr_admin()):
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
        advance.approved_by = user
        advance.approved_date = timezone.now()
        advance.payment_date = data.get('payment_date')
        advance.deduction_month = data.get('deduction_month')
        if data.get('notes'):
            advance.notes = data['notes']
        advance.save()

        # --- Notification vers l'employé : avance approuvée ---
        try:
            from notifications.notification_helpers import send_notification
            send_notification(
                organization=advance.employee.organization,
                recipient=advance.employee,
                sender=user,
                title="Avance sur paie approuvée",
                message=f"Votre demande d'avance de {advance.amount} {advance.employee.organization.currency} a été approuvée.",
                notification_type='user',
                priority='medium',
                entity_type='payroll_advance',
                entity_id=str(advance.id),
            )
        except Exception:
            pass

        return Response(
            PayrollAdvanceSerializer(advance).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserOrEmployee])
    def reject(self, request, pk=None):
        """Rejeter une demande d'avance
        
        Règles:
        - Requiert la permission hr.approve_payroll ou être admin
        - Un utilisateur NE PEUT PAS rejeter sa propre demande
        """
        advance = self.get_object()
        user = request.user

        # Vérifier que l'utilisateur ne tente pas de rejeter sa propre demande
        if getattr(user, 'user_type', None) == 'employee':
            if advance.employee == user:
                return Response(
                    {'error': 'Vous ne pouvez pas rejeter votre propre demande d\'avance'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if not (user.has_permission("hr.approve_payroll") or user.is_hr_admin()):
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
        advance.approved_by = user
        advance.approved_date = timezone.now()
        advance.rejection_reason = data.get('rejection_reason', '')
        advance.save()

        # --- Notification vers l'employé : avance rejetée ---
        try:
            from notifications.notification_helpers import send_notification
            reason = advance.rejection_reason or "Aucun motif précisé."
            send_notification(
                organization=advance.employee.organization,
                recipient=advance.employee,
                sender=user,
                title="Avance sur paie rejetée",
                message=f"Votre demande d'avance de {advance.amount} {advance.employee.organization.currency} a été rejetée. Motif : {reason}",
                notification_type='user',
                priority='high',
                entity_type='payroll_advance',
                entity_id=str(advance.id),
            )
        except Exception:
            pass

        return Response(
            PayrollAdvanceSerializer(advance).data,
            status=status.HTTP_200_OK
        )

    # SIMPLIFIÉ: Les actions mark_as_paid et deduct_from_payslip ont été supprimées.
    # Les avances approuvées sont maintenant automatiquement déduites lors de la génération
    # des fiches de paie via l'action generate_for_period du PayslipViewSet.



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
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUserOrEmployee, RequiresRolePermission]
    allow_list_without_permission = True  # Permet de lister pour les dropdowns
    
    def get_queryset(self):
        user = self.request.user

        queryset = Role.objects.all()

        # Récupérer l'organisation depuis les paramètres de requête
        org_subdomain = self.request.query_params.get('organization_subdomain')
        org_id = self.request.query_params.get('organization')

        if getattr(user, 'user_type', None) == 'admin':
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
        elif getattr(user, 'user_type', None) == 'employee':
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
            if getattr(user, 'user_type', None) == 'admin':
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
            elif getattr(user, 'user_type', None) == 'employee':
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
    permission_classes = [IsAdminUserOrEmployee]
    serializer_class = AttendanceSerializer
    filterset_fields = ['user', 'date', 'status', 'is_approved']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
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
            'user', 'organization', 'approved_by'
        )

        if getattr(user, 'user_type', None) == 'admin':
            pass
        elif getattr(user, 'user_type', None) == 'employee':
            if user.has_permission('can_view_all_attendance'):
                pass
            else:
                queryset = queryset.filter(user_email=user.email)
        else:
            queryset = Attendance.objects.none()

        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter(user_id=employee_id)
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
        if getattr(user, 'user_type', None) == 'employee':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Vous n\'avez pas la permission de créer des pointages')
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'employee':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Vous n\'avez pas la permission de modifier des pointages')
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if getattr(user, 'user_type', None) == 'employee':
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

        if getattr(user, 'user_type', None) == 'employee':
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': "Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'admin':
            pass
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AttendanceCheckInSerializer(data=request.data)
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
        employee = None

        if getattr(user, 'user_type', None) == 'admin':
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
                # Admin pointe pour lui-même
                user_email = user.email
                user_full_name = user.get_full_name()
        elif getattr(user, 'user_type', None) == 'employee':
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
            # Déterminer l'utilisateur à associer
            # Si employee est défini, c'est lui l'utilisateur
            # Sinon c'est l'admin lui-même
            attendance_user = employee if employee else user
            
            attendance = Attendance.objects.create(
                user=attendance_user,
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

        if getattr(user, 'user_type', None) == 'employee':
            if not user.has_permission('can_manual_checkin'):
                return Response(
                    {'error': "Vous devez utiliser le système de pointage par QR code. Seuls les administrateurs autorisés peuvent effectuer un pointage manuel."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif getattr(user, 'user_type', None) == 'admin':
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

        if getattr(user, 'user_type', None) == 'admin':
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
        elif getattr(user, 'user_type', None) == 'employee':
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

        if getattr(user, 'user_type', None) == 'admin':
            user_email = user.email
        elif getattr(user, 'user_type', None) == 'employee':
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

        is_admin = getattr(user, 'user_type', None) == 'admin'
        is_employee_with_permission = getattr(user, 'user_type', None) == 'employee' and user.has_permission('can_approve_attendance')

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
        
        # Utiliser approved_by pour tous les types d'utilisateurs
        attendance.approved_by = user

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
        if getattr(user, 'user_type', None) == 'admin':
            user_email = user.email
        elif getattr(user, 'user_type', None) == 'employee':
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
        if getattr(user, 'user_type', None) == 'admin':
            user_email = user.email
        elif getattr(user, 'user_type', None) == 'employee':
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
            if getattr(user, 'user_type', None) == 'employee' and not user.has_permission('can_view_all_attendance'):
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
            if not getattr(user, 'user_type', None) == 'employee':
                return Response(
                    {'error': 'Employee ID required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            employee = user

        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        queryset = Attendance.objects.filter(user=employee)
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

        if getattr(request.user, 'user_type', None) == 'employee':
            if not request.user.has_permission('can_create_qr_session'):
                return Response(
                    {'error': 'Vous n\'avez pas la permission de créer des sessions QR'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not getattr(request.user, 'user_type', None) == 'admin':
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
                'employee_name': attendance.user_full_name or (attendance.user.get_full_name() if attendance.user else ''),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

