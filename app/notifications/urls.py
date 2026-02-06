"""
Notifications — URL Routing
============================
Enregistrement des ViewSets via le DRF DefaultRouter.

Routes générées :
    /api/notifications/notifications/                     → CRUD + actions
    /api/notifications/notifications/{id}/                → détail
    /api/notifications/notifications/{id}/mark-as-read/   → POST
    /api/notifications/notifications/mark-all-as-read/    → POST
    /api/notifications/notifications/unread-count/        → GET
    /api/notifications/notifications/stats/               → GET
    /api/notifications/preferences/                       → GET / PATCH
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Notifications CRUD + actions
router.register(r'notifications', views.NotificationViewSet, basename='notification')

# Préférences (list + partial_update uniquement)
router.register(r'preferences', views.NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
    # SSE — flux de notifications en temps réel
    path('stream/', views.notification_stream, name='notification-stream'),
]
