"""
ViewSets for Services Module API
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone

from .models import (
    BusinessProfile,
    ServiceType,
    ServiceField,
    ServiceStatus,
    Service,
    ServiceStatusHistory,
    ServiceActivity,
    ServiceComment,
    ServiceTemplate
)
from .serializers import (
    BusinessProfileSerializer,
    BusinessProfileListSerializer,
    ServiceTypeSerializer,
    ServiceTypeListSerializer,
    ServiceFieldSerializer,
    ServiceStatusSerializer,
    ServiceSerializer,
    ServiceListSerializer,
    ServiceCreateSerializer,
    ServiceUpdateSerializer,
    ServiceStatusChangeSerializer,
    ServiceActivitySerializer,
    ServiceCommentSerializer,
    ServiceTemplateSerializer,
    ServiceStatusHistorySerializer,
)


class BusinessProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for BusinessProfile management"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return BusinessProfile.objects.filter(organization=org)
        return BusinessProfile.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return BusinessProfileListSerializer
        return BusinessProfileSerializer

    def perform_create(self, serializer):
        """Set organization on create"""
        org = self.request.user.get_organization()
        serializer.save(organization=org)


class ServiceTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceType management"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['business_profile', 'is_active', 'allow_nested_services', 'has_pricing']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceType.objects.filter(
                business_profile__organization=org
            ).select_related('business_profile')
        return ServiceType.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceTypeListSerializer
        return ServiceTypeSerializer

    @action(detail=True, methods=['get'])
    def fields(self, request, pk=None):
        """Get fields for a service type"""
        service_type = self.get_object()
        fields = service_type.fields.filter(is_active=True).order_by('order')
        serializer = ServiceFieldSerializer(fields, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statuses(self, request, pk=None):
        """Get statuses for a service type"""
        service_type = self.get_object()
        statuses = service_type.statuses.filter(is_active=True).order_by('order')
        serializer = ServiceStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def templates(self, request, pk=None):
        """Get templates for a service type"""
        service_type = self.get_object()
        templates = service_type.templates.filter(is_active=True)
        serializer = ServiceTemplateSerializer(templates, many=True)
        return Response(serializer.data)


class ServiceFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceField management"""

    permission_classes = [IsAuthenticated]
    serializer_class = ServiceFieldSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'field_key', 'description']
    filterset_fields = ['service_type', 'field_type', 'is_required', 'is_active']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceField.objects.filter(
                service_type__business_profile__organization=org
            ).select_related('service_type')
        return ServiceField.objects.none()


class ServiceStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceStatus management"""

    permission_classes = [IsAuthenticated]
    serializer_class = ServiceStatusSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['service_type', 'status_type', 'is_initial', 'is_final', 'is_active']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceStatus.objects.filter(
                service_type__business_profile__organization=org
            ).select_related('service_type')
        return ServiceStatus.objects.none()


class ServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Service management"""

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['reference', 'title', 'description', 'client_name', 'client_email']
    filterset_fields = [
        'service_type', 'current_status', 'assigned_to',
        'priority', 'client_type', 'is_archived'
    ]
    ordering_fields = ['created_at', 'start_date', 'reference', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by organization with optimizations"""
        user = self.request.user
        org = user.get_organization()

        if not org:
            return Service.objects.none()

        queryset = Service.objects.filter(organization=org).select_related(
            'service_type',
            'service_type__business_profile',
            'current_status',
            'assigned_to',
            'client_user',
            'parent_service'
        ).prefetch_related(
            'child_services',
            'status_history',
            'comments',
            'activities'
        )

        # Filtres personnalisés
        parent_service = self.request.query_params.get('parent_service', None)
        if parent_service:
            if parent_service == 'null':
                queryset = queryset.filter(parent_service__isnull=True)
            else:
                queryset = queryset.filter(parent_service_id=parent_service)

        # Filtre par période
        start_date_from = self.request.query_params.get('start_date_from', None)
        start_date_to = self.request.query_params.get('start_date_to', None)
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        elif self.action == 'create':
            return ServiceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ServiceUpdateSerializer
        return ServiceSerializer

    def perform_create(self, serializer):
        """Set organization on create"""
        org = self.request.user.get_organization()
        serializer.save(organization=org)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change service status"""
        service = self.get_object()
        serializer = ServiceStatusChangeSerializer(
            data=request.data,
            context={'service': service, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated_service = serializer.save()

        return Response(
            ServiceSerializer(updated_service, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get service activities"""
        service = self.get_object()
        activities = service.activities.all().order_by('-created_at')

        # Pagination optionnelle
        page = self.paginate_queryset(activities)
        if page is not None:
            serializer = ServiceActivitySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ServiceActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """Get or create service comments"""
        service = self.get_object()

        if request.method == 'GET':
            comments = service.comments.filter(
                parent_comment__isnull=True
            ).order_by('-created_at')

            serializer = ServiceCommentSerializer(
                comments,
                many=True,
                context={'request': request}
            )
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = ServiceCommentSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            comment = serializer.save(service=service, user=request.user)

            # Log activity
            ServiceActivity.objects.create(
                service=service,
                activity_type='comment_added',
                user=request.user,
                title='Nouveau commentaire',
                description=comment.content[:100],
                data={'comment_id': str(comment.id)}
            )

            return Response(
                ServiceCommentSerializer(comment, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get service status history"""
        service = self.get_object()
        history = service.status_history.all().order_by('-created_at')
        serializer = ServiceStatusHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a service"""
        service = self.get_object()
        service.is_archived = True
        service.save()

        ServiceActivity.objects.create(
            service=service,
            activity_type='custom',
            user=request.user,
            title='Service archivé',
            description=f'Le service {service.reference} a été archivé.'
        )

        return Response({'status': 'Service archivé'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived service"""
        service = self.get_object()
        service.is_archived = False
        service.save()

        ServiceActivity.objects.create(
            service=service,
            activity_type='custom',
            user=request.user,
            title='Service restauré',
            description=f'Le service {service.reference} a été restauré.'
        )

        return Response({'status': 'Service restauré'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get service statistics"""
        org = request.user.get_organization()
        if not org:
            return Response({'error': 'Organization not found'}, status=400)

        services = Service.objects.filter(organization=org, is_archived=False)

        stats = {
            'total': services.count(),
            'by_status': {},
            'by_priority': {},
            'by_service_type': {},
            'by_month': {},
        }

        # Par statut
        status_stats = services.values(
            'current_status__name',
            'current_status__color'
        ).annotate(count=Count('id'))

        for stat in status_stats:
            stats['by_status'][stat['current_status__name']] = {
                'count': stat['count'],
                'color': stat['current_status__color']
            }

        # Par priorité
        priority_stats = services.values('priority').annotate(count=Count('id'))
        for stat in priority_stats:
            stats['by_priority'][stat['priority']] = stat['count']

        # Par type de service
        type_stats = services.values('service_type__name').annotate(count=Count('id'))
        for stat in type_stats:
            stats['by_service_type'][stat['service_type__name']] = stat['count']

        return Response(stats)


class ServiceActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ServiceActivity (read-only)"""

    permission_classes = [IsAuthenticated]
    serializer_class = ServiceActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['service', 'activity_type', 'user']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceActivity.objects.filter(
                service__organization=org
            ).select_related('service', 'user')
        return ServiceActivity.objects.none()


class ServiceCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceComment management"""

    permission_classes = [IsAuthenticated]
    serializer_class = ServiceCommentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content']
    filterset_fields = ['service', 'user', 'is_internal']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceComment.objects.filter(
                service__organization=org
            ).select_related('service', 'user', 'parent_comment')
        return ServiceComment.objects.none()

    def perform_create(self, serializer):
        """Set user on create"""
        serializer.save(user=self.request.user)


class ServiceTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for ServiceTemplate management"""

    permission_classes = [IsAuthenticated]
    serializer_class = ServiceTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['service_type', 'is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter by organization"""
        user = self.request.user
        org = user.get_organization()
        if org:
            return ServiceTemplate.objects.filter(
                service_type__business_profile__organization=org
            ).select_related('service_type')
        return ServiceTemplate.objects.none()

    @action(detail=True, methods=['post'])
    def create_service(self, request, pk=None):
        """Create a service from template"""
        template = self.get_object()

        # Préparer les données avec les valeurs du template
        data = {
            'organization': request.user.get_organization().id,
            'service_type': template.service_type.id,
            'title': template.default_title_template or template.name,
            'field_values': template.default_field_values,
            **request.data  # Override avec les données fournies
        }

        serializer = ServiceCreateSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        service = serializer.save()

        return Response(
            ServiceSerializer(service, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
