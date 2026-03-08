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
    POST   /api/notifications/notifications/batch-delete/       → suppression par lot
    GET    /api/notifications/notifications/unread-count/        → nombre de non lues
    GET    /api/notifications/notifications/stats/               → stats récapitulatives

    GET    /api/notifications/preferences/            → préférences du user courant
    PATCH  /api/notifications/preferences/            → mettre à jour les préférences

    GET    /api/notifications/stream/                 → SSE temps réel
"""

import json
import time
import logging

from django.db.models import Q
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

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
from .notification_helpers import (
    mark_all_as_read,
    get_unread_count,
    _push_sse_unread_update,
)
from .websocket_helpers import send_notification_to_user, send_unread_count_to_user

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NotificationViewSet
# ---------------------------------------------------------------------------

class NotificationViewSet(OrganizationResolverMixin, viewsets.ModelViewSet):
    """
    ViewSet pour les notifications.

    Filtres supportés (query params) :
        - is_read        : true | false
        - notification_type : alert | system | user
        - priority       : low | medium | high | critical
        - entity_type    : product | order | etc.
        - search         : recherche dans title + message
        - ordering       : champ de tri (ex: -created_at, priority)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    # --- Queryset -----------------------------------------------------------
    def get_queryset(self):
        """Filtre les notifs par organisation + destinataire courant + query params."""
        organization = self.get_organization_from_request()
        user = self.request.user
        qs = Notification.objects.filter(
            organization=organization,
            recipient=user,
        ).select_related('sender')

        # Filtre is_read
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() in ('true', '1', 'yes'))

        # Filtre type
        ntype = self.request.query_params.get('notification_type')
        if ntype and ntype in ('alert', 'system', 'user'):
            qs = qs.filter(notification_type=ntype)

        # Filtre priorité
        priority = self.request.query_params.get('priority')
        if priority and priority in ('low', 'medium', 'high', 'critical'):
            qs = qs.filter(priority=priority)

        # Filtre entity_type
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        # Recherche textuelle
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )

        # Tri
        ordering = self.request.query_params.get('ordering', '-created_at')
        allowed = {'created_at', '-created_at', 'priority', '-priority', 'title', '-title'}
        if ordering in allowed:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-created_at')

        return qs

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
            # Aussi envoyer le compteur mis à jour
            unread = get_unread_count(organization, self.request.user)
            send_unread_count_to_user(str(self.request.user.id), unread)
        except Exception as e:
            logger.error("Erreur lors de l'envoi WebSocket: %s", e)

    # --- Suppression (DELETE) -----------------------------------------------
    def perform_destroy(self, instance):
        """Supprime et pousse la mise à jour en temps réel."""
        organization = instance.organization
        user = instance.recipient
        was_unread = not instance.is_read
        instance.delete()

        # Mettre à jour le compteur en temps réel si la notif était non lue
        if was_unread:
            _push_sse_unread_update(organization, user)

    # -----------------------------------------------------------------------
    # Actions personnalisées
    # -----------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='mark-as-read', url_name='mark-as-read')
    def mark_as_read(self, request, pk=None):
        """
        POST /notifications/{id}/mark-as-read/
        Marque une notification spécifique comme lue.
        Push le compteur mis à jour en temps réel.
        """
        notification = self.get_object()
        was_unread = not notification.is_read
        notification.mark_as_read()

        if was_unread:
            _push_sse_unread_update(notification.organization, notification.recipient)

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

    @action(detail=False, methods=['post'], url_path='batch-delete', url_name='batch-delete')
    def batch_delete(self, request):
        """
        POST /notifications/batch-delete/
        Supprime un lot de notifications par IDs.
        Body: { "ids": ["uuid1", "uuid2", ...] }
        """
        ids = request.data.get('ids', [])
        if not ids or not isinstance(ids, list):
            return Response(
                {'error': 'Fournissez une liste "ids" de UUIDs.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organization = self.get_organization_from_request()
        qs = Notification.objects.filter(
            id__in=ids,
            organization=organization,
            recipient=request.user,
        )
        count = qs.count()
        qs.delete()

        # Push la mise à jour du compteur
        _push_sse_unread_update(organization, request.user)

        return Response(
            {'message': f'{count} notification(s) supprimée(s).', 'count': count},
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

        Optimisé avec une seule requête et annotation.
        """
        from django.db.models import Count, Case, When, IntegerField

        qs = self.get_queryset()

        # Totaux en une requête
        agg = qs.aggregate(
            total=Count('id'),
            unread=Count(Case(When(is_read=False, then=1), output_field=IntegerField())),
        )

        # Par type
        by_type = dict(
            qs.values_list('notification_type')
            .annotate(c=Count('id'))
            .values_list('notification_type', 'c')
        )
        # Garantir toutes les clés
        for t_code, _ in Notification.TYPE_CHOICES:
            by_type.setdefault(t_code, 0)

        # Par priorité
        by_priority = dict(
            qs.values_list('priority')
            .annotate(c=Count('id'))
            .values_list('priority', 'c')
        )
        for p_code, _ in Notification.PRIORITY_CHOICES:
            by_priority.setdefault(p_code, 0)

        return Response({
            'total': agg['total'],
            'unread': agg['unread'],
            'read': agg['total'] - agg['unread'],
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

    def _get_or_create_preference(self):
        organization = self.get_organization_from_request()
        pref, _ = NotificationPreference.objects.get_or_create(
            organization=organization,
            user=self.request.user,
        )
        return pref

    def list(self, request, *args, **kwargs):
        """Retourne les préférences du user courant (créées par défaut si absentes)."""
        pref = self._get_or_create_preference()
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Met à jour les préférences du user courant."""
        pref = self._get_or_create_preference()
        serializer = NotificationPreferenceUpdateSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
    Utilise MultiUserJWTAuthentication pour supporter Admin + Employee,
    exactement comme le font les vues DRF.
    Retourne l'utilisateur (AdminUser ou Employee) ou None.
    """
    from lourabackend.authentication import MultiUserJWTAuthentication
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

    # Le middleware TokenFromQueryParamMiddleware a déjà mis le token query param
    # dans HTTP_AUTHORIZATION, donc on n'a plus besoin de le lire manuellement.
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        # Fallback: lire le query param directement
        raw_token = request.GET.get('token', '')
        if raw_token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {raw_token}'
        else:
            logger.warning("SSE auth: pas de token fourni")
            return None

    try:
        jwt_auth = MultiUserJWTAuthentication()
        result = jwt_auth.authenticate(request)
        if result is None:
            logger.warning("SSE auth: MultiUserJWTAuthentication a retourné None")
            return None
        user, _ = result
        logger.debug("SSE auth OK: user=%s (type=%s)", user.id, getattr(user, 'user_type', '?'))
        return user
    except (TokenError, InvalidToken) as e:
        logger.warning("SSE auth: token invalide ou expiré — %s", e)
        return None
    except Exception as e:
        logger.error("SSE auth: erreur inattendue — %s", e, exc_info=True)
        return None


def _resolve_organization_for_sse(request, user):
    """
    Résout l'organisation depuis le query param `org` (subdomain ou UUID)
    ou depuis l'utilisateur employee.
    """
    from core.models import Organization

    user_type = getattr(user, 'user_type', None)

    # Employee → organisation assignée (directement sur l'objet Employee)
    if user_type == 'employee':
        org = getattr(user, 'organization', None)
        if org:
            return org
        # Fallback: essayer via la relation reverse BaseUser → Employee
        try:
            return user.employee.organization
        except Exception:
            logger.warning("SSE org: employee %s n'a pas d'organisation", user.id)
            return None

    # Admin → param `org` obligatoire
    org_param = request.GET.get('org', '')
    if not org_param:
        logger.warning("SSE org: admin %s sans param 'org'", user.id)
        return None
    try:
        try:
            return Organization.objects.get(subdomain=org_param)
        except Organization.DoesNotExist:
            return Organization.objects.get(id=org_param)
    except Exception:
        logger.warning("SSE org: organization '%s' non trouvée", org_param)
        return None


# ---------------------------------------------------------------------------
# Async SSE Generator  — utilise asyncio.sleep() au lieu de time.sleep()
# pour que Daphne (ASGI) puisse annuler la tâche proprement.
# ---------------------------------------------------------------------------

import asyncio
from asgiref.sync import sync_to_async


async def _sse_event_generator(user, organization, poll_interval=2):
    """
    Générateur SSE **asynchrone**.

    - Utilise asyncio.sleep() au lieu de time.sleep() pour ne pas bloquer
      le thread et permettre à Daphne de fermer la connexion proprement.
    - Utilise sync_to_async pour les requêtes ORM.
    - Détecte les nouvelles notifications via created_at__gt.
    - Détecte les changements de compteur non lu.
    - Envoie un event `heartbeat` avec le compteur courant périodiquement.
    """
    from .serializers import NotificationSerializer

    # --- Helpers ORM wrappés en async ------------------------------------

    @sync_to_async
    def get_unread_count_db():
        return Notification.objects.filter(
            organization=organization, recipient=user, is_read=False
        ).count()

    @sync_to_async
    def get_latest_created_at():
        return (
            Notification.objects.filter(organization=organization, recipient=user)
            .order_by('-created_at')
            .values_list('created_at', flat=True)
            .first()
        )

    @sync_to_async
    def get_new_notifications(since):
        qs = Notification.objects.filter(
            organization=organization,
            recipient=user,
        ).select_related('sender')
        if since:
            qs = qs.filter(created_at__gt=since)
        notifs = list(qs.order_by('created_at'))
        # Sérialiser dans le thread synchrone (le serializer accède au ORM)
        return [(NotificationSerializer(n).data, n.created_at) for n in notifs]

    # --- État initial ----------------------------------------------------
    last_check_time = None
    last_unread_count = None

    try:
        # Envoyer le compteur initial
        unread = await get_unread_count_db()
        last_unread_count = unread
        yield f"event: unread_count\ndata: {json.dumps({'count': unread})}\n\n"

        # Dernier timestamp vu
        last_check_time = await get_latest_created_at()

        heartbeat_counter = 0

        while True:
            # asyncio.sleep est annulable : quand Daphne ferme la connexion,
            # CancelledError est levé ici et le générateur se termine proprement.
            await asyncio.sleep(poll_interval)

            # Ping keepalive
            yield ": ping\n\n"
            heartbeat_counter += 1

            try:
                # Chercher les nouvelles notifications
                new_notifs = await get_new_notifications(last_check_time)

                for notif_data, created_at in new_notifs:
                    yield f"event: notification\ndata: {json.dumps(notif_data)}\n\n"
                    last_check_time = created_at

                # Vérifier le compteur non lu
                current_unread = await get_unread_count_db()

                if current_unread != last_unread_count:
                    last_unread_count = current_unread
                    yield f"event: unread_count\ndata: {json.dumps({'count': current_unread})}\n\n"

                # Heartbeat complet toutes les 15 itérations (~30s)
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield f"event: heartbeat\ndata: {json.dumps({'count': current_unread, 'ts': int(time.time())})}\n\n"

            except Exception as e:
                logger.warning("SSE poll error for user=%s: %s", user.id, e)
                # Continue le loop, la prochaine itération réessaiera

    except (asyncio.CancelledError, GeneratorExit):
        # Daphne a annulé la tâche ou le client s'est déconnecté — OK
        logger.info("SSE stream fermé proprement : user=%s, org=%s", user.id, organization.id)
        return


@csrf_exempt
@require_GET
async def notification_stream(request):
    """
    GET /api/notifications/stream/
    Endpoint SSE pour les notifications en temps réel.

    Vue **asynchrone** — utilise un async generator avec asyncio.sleep()
    pour éviter de bloquer le worker ASGI et permettre un arrêt propre.

    Query params :
        - token  : JWT Bearer token (obligatoire si pas de header Authorization)
        - org    : subdomain ou UUID de l'organisation (obligatoire pour les admins)

    Protocole SSE :
        - event: notification  → nouvelle notification (data: JSON sérialisé)
        - event: unread_count  → mise à jour du compteur (data: {"count": N})
        - event: heartbeat     → keepalive avec compteur (data: {"count": N, "ts": epoch})
        - : ping               → keepalive léger
    """
    # L'authentification est synchrone (accès ORM), on la wrappe
    user = await sync_to_async(_authenticate_sse)(request)
    if user is None:
        return StreamingHttpResponse(
            iter([f"event: error\ndata: {json.dumps({'message': 'Authentification requise'})}\n\n"]),
            content_type='text/event-stream',
            status=401,
        )

    organization = await sync_to_async(_resolve_organization_for_sse)(request, user)
    if organization is None:
        return StreamingHttpResponse(
            iter([f"event: error\ndata: {json.dumps({'message': 'Organisation non trouvée'})}\n\n"]),
            content_type='text/event-stream',
            status=400,
        )

    logger.info("SSE stream ouvert : user=%s, org=%s", user.id, organization.id)

    response = StreamingHttpResponse(
        _sse_event_generator(user, organization),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    return response

