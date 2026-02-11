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

import json
import time
import logging

from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

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
from .websocket_helpers import send_notification_to_user, send_unread_count_to_user

logger = logging.getLogger(__name__)


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
        notification = serializer.save(
            organization=organization,
            recipient=self.request.user,
        )

        # Envoyer la notification en temps réel via WebSocket
        try:
            send_notification_to_user(notification)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi WebSocket: {e}")

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


# ---------------------------------------------------------------------------
# SSE — Server-Sent Events : flux de notifications en temps réel
# ---------------------------------------------------------------------------

def _authenticate_sse(request):
    """
    Authentifie la requête SSE via le Bearer token JWT.
    Retourne l'utilisateur ou None.
    """
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from core.models import BaseUser

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        # Fallback : token dans query param (utile pour EventSource qui ne supporte pas les headers)
        token_qs = request.GET.get('token', '')
        if not token_qs:
            return None
        raw_token = token_qs
    else:
        raw_token = auth_header.split(' ', 1)[1]

    try:
        token = AccessToken(raw_token)
        user_id = token.get('user_id')
        user = BaseUser.objects.get(pk=user_id)
        return user
    except (TokenError, BaseUser.DoesNotExist, Exception):
        return None


def _resolve_organization_for_sse(request, user):
    """
    Résout l'organisation depuis le query param `org` (subdomain ou UUID)
    ou depuis l'utilisateur employee.
    """
    from core.models import Organization

    user_type = getattr(user, 'user_type', None)

    # Employee → organisation assignée
    if user_type == 'employee':
        try:
            return user.employee.organization
        except Exception:
            return None

    # Admin → param `org` obligatoire
    org_param = request.GET.get('org', '')
    if not org_param:
        return None
    try:
        # Essayer comme subdomain d'abord, puis comme UUID
        try:
            return Organization.objects.get(subdomain=org_param)
        except Organization.DoesNotExist:
            return Organization.objects.get(id=org_param)
    except Exception:
        return None


def _sse_event_generator(user, organization, poll_interval=3):
    """
    Générateur SSE.
    - Envoie un `ping` toutes les `poll_interval` secondes pour garder la connexion.
    - Détecte les nouvelles notifications (créées après le dernier `seen_id`) et les envoie.
    """
    # Dernier ID vu à l'instant de la connexion
    last_seen = (
        Notification.objects.filter(organization=organization, recipient=user)
        .order_by('-created_at')
        .values_list('id', flat=True)
        .first()
    )

    # Envoyer l'état initial : nombre de non lues
    unread = Notification.objects.filter(
        organization=organization, recipient=user, is_read=False
    ).count()
    yield f"event: unread_count\ndata: {json.dumps({{'count': {unread}}})}  \n\n"

    while True:
        time.sleep(poll_interval)

        # Ping pour garder la connexion vivante
        yield ": ping\n\n"

        # Chercher les nouvelles notifications depuis le dernier check
        qs = Notification.objects.filter(
            organization=organization,
            recipient=user,
        )

        if last_seen:
            # Récupérer les notifs créées après le dernier seen
            # On compare via created_at du dernier seen
            try:
                last_notif = Notification.objects.get(id=last_seen)
                qs = qs.filter(created_at__gt=last_notif.created_at)
            except Notification.DoesNotExist:
                pass

        new_notifs = qs.order_by('created_at').select_related('sender')

        for notif in new_notifs:
            payload = {
                'id': str(notif.id),
                'title': notif.title,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'entity_type': notif.entity_type,
                'entity_id': notif.entity_id,
                'action_url': notif.action_url,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'sender': {
                    'id': str(notif.sender.id),
                    'email': notif.sender.email,
                } if notif.sender else None,
            }
            yield f"event: notification\ndata: {json.dumps(payload)}\n\n"
            last_seen = notif.id

        # Envoyer le compteur mis à jour si des nouvelles notifs ont été trouvées
        if new_notifs.exists():
            unread = Notification.objects.filter(
                organization=organization, recipient=user, is_read=False
            ).count()
            yield f"event: unread_count\ndata: {json.dumps({{'count': {unread}}})}  \n\n"


@csrf_exempt
@require_GET
def notification_stream(request):
    """
    GET /api/notifications/stream/
    Endpoint SSE pour les notifications en temps réel.

    Query params :
        - token  : JWT Bearer token (obligatoire si pas de header Authorization)
        - org    : subdomain ou UUID de l'organisation (obligatoire pour les admins)

    Protocole SSE :
        - event: notification  → nouvelle notification (data: JSON)
        - event: unread_count  → mise à jour du compteur (data: {"count": N})
        - : ping               → keepalive
    """
    user = _authenticate_sse(request)
    if user is None:
        return StreamingHttpResponse(
            iter([f"event: error\ndata: {json.dumps({{'message': 'Authentification requise'}})}\n\n"]),
            content_type='text/event-stream',
            status=401,
        )

    organization = _resolve_organization_for_sse(request, user)
    if organization is None:
        return StreamingHttpResponse(
            iter([f"event: error\ndata: {json.dumps({{'message': 'Organisation non trouvée'}})}\n\n"]),
            content_type='text/event-stream',
            status=400,
        )

    logger.info("SSE stream ouvert : user=%s, org=%s", user.id, organization.id)

    response = StreamingHttpResponse(
        _sse_event_generator(user, organization),
        content_type='text/event-stream',
    )
    # Headers SSE standard
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Nginx
    response['Access-Control-Allow-Origin'] = '*'
    return response
