"""
Notifications — ViewSets
=========================
API REST pour la gestion des notifications et des préférences.

Endpoints générés par le router :
    GET    /api/notifications/notifications/          → liste des notifs du user courant
    POST   /api/notifications/notifications/          → créer une notif (admin)
    GET    /api/notifications/notifications/{id}/     → détail
    PATCH  /api/notifications/notifications/{id}/     → marquer comme lu
    DELETE /api/notifications/notifications/{id}/     → supprimer

    POST   /api/notifications/notifications/mark-as-read/       → marquer une notif comme lue
    POST   /api/notifications/notifications/mark-all-as-read/   → marquer toutes comme lues
    GET    /api/notifications/notifications/unread-count/        → nombre de non lues
    GET    /api/notifications/notifications/stats/               → stats récapitulatives

    GET    /api/notifications/preferences/            → préférences du user courant
    PATCH  /api/notifications/preferences/            → mettre à jour les préférences
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.mixins import OrganizationResolverMixin
from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
)
from .notification_helpers import mark_all_as_read, get_unread_count


# ---------------------------------------------------------------------------
# NotificationViewSet
# ---------------------------------------------------------------------------

class NotificationViewSet(OrganizationResolverMixin, viewsets.ModelViewSet):
    """
    ViewSet pour les notifications.

    - list / retrieve : uniquement les notifs du user courant dans son org.
    - create : crée une notif ciblant le user courant (l'organisation est résolue auto).
    - destroy : supprime une notif appartenant au user courant.
    - actions custom : mark-as-read, mark-all-as-read, unread-count, stats.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    # --- Queryset -----------------------------------------------------------
    def get_queryset(self):
        """Filtre les notifs par organisation + destinataire courant."""
        organization = self.get_organization_from_request()
        user = self.request.user
        return Notification.objects.filter(
            organization=organization,
            recipient=user,
        ).select_related('sender')

    # --- Sérialiseur selon l'action -----------------------------------------
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    # --- Création (POST) ----------------------------------------------------
    def perform_create(self, serializer):
        """Injecte organisation + destinataire (user courant) à la création."""
        organization = self.get_organization_from_request()
        serializer.save(
            organization=organization,
            recipient=self.request.user,
        )

    # -----------------------------------------------------------------------
    # Actions personnalisées
    # -----------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='mark-as-read', url_name='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """
        POST /notifications/{id}/mark-as-read/
        Marque une notification spécifique comme lue.
        """
        notification = self.get_object()
        notification.mark_as_read()
        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='mark-all-as-read', url_name='mark-all-as-read')
    def mark_all_as_read_action(self, request):
        """
        POST /notifications/mark-all-as-read/
        Marque toutes les notifications non lues du user courant comme lues.
        """
        organization = self.get_organization_from_request()
        count = mark_all_as_read(organization, request.user)
        return Response(
            {'message': f'{count} notification(s) marquée(s) comme lue(s).', 'count': count},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='unread-count', url_name='unread-count')
    def unread_count(self, request):
        """
        GET /notifications/unread-count/
        Retourne le nombre de notifications non lues.
        """
        organization = self.get_organization_from_request()
        count = get_unread_count(organization, request.user)
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='stats', url_name='stats')
    def stats(self, request):
        """
        GET /notifications/stats/
        Récapitulatif : total, non lues, par type, par priorité.
        """
        qs = self.get_queryset()

        total = qs.count()
        unread = qs.filter(is_read=False).count()

        # Par type
        by_type = {}
        for t_code, t_label in Notification.TYPE_CHOICES:
            by_type[t_code] = qs.filter(notification_type=t_code).count()

        # Par priorité
        by_priority = {}
        for p_code, p_label in Notification.PRIORITY_CHOICES:
            by_priority[p_code] = qs.filter(priority=p_code).count()

        return Response({
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_type': by_type,
            'by_priority': by_priority,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# NotificationPreferenceViewSet
# ---------------------------------------------------------------------------

class NotificationPreferenceViewSet(OrganizationResolverMixin, viewsets.GenericViewSet):
    """
    ViewSet pour les préférences de notification du user courant.

    - GET  /preferences/  → retourne les préférences actuelles (ou les crée par défaut)
    - PATCH /preferences/ → met à jour les préférences
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer

    # --- Récupérer ou créer les préférences ---------------------------------
    def _get_or_create_preference(self):
        organization = self.get_organization_from_request()
        pref, _ = NotificationPreference.objects.get_or_create(
            organization=organization,
            user=self.request.user,
        )
        return pref

    # --- list (GET /) -------------------------------------------------------
    def list(self, request, *args, **kwargs):
        """Retourne les préférences du user courant (créées par défaut si absentes)."""
        pref = self._get_or_create_preference()
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # --- partial_update (PATCH /) -------------------------------------------
    def partial_update(self, request, *args, **kwargs):
        """Met à jour les préférences du user courant."""
        pref = self._get_or_create_preference()
        serializer = NotificationPreferenceUpdateSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Retourner la version complète après mise à jour
        return Response(
            NotificationPreferenceSerializer(pref).data,
            status=status.HTTP_200_OK,
        )
