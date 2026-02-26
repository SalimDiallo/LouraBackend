"""
URL Configuration for Services Module
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BusinessProfileViewSet,
    ServiceTypeViewSet,
    ServiceFieldViewSet,
    ServiceStatusViewSet,
    ServiceViewSet,
    ServiceActivityViewSet,
    ServiceCommentViewSet,
    ServiceTemplateViewSet,
)

# Create router and register viewsets
router = DefaultRouter()

router.register(r'business-profiles', BusinessProfileViewSet, basename='businessprofile')
router.register(r'service-types', ServiceTypeViewSet, basename='servicetype')
router.register(r'service-fields', ServiceFieldViewSet, basename='servicefield')
router.register(r'service-statuses', ServiceStatusViewSet, basename='servicestatus')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'service-activities', ServiceActivityViewSet, basename='serviceactivity')
router.register(r'service-comments', ServiceCommentViewSet, basename='servicecomment')
router.register(r'service-templates', ServiceTemplateViewSet, basename='servicetemplate')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
