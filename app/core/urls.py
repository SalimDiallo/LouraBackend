from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet,
    CategoryViewSet,
    ModuleViewSet,
    OrganizationModuleViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'organization-modules', OrganizationModuleViewSet, basename='organization-module')

urlpatterns = [
    # Register endpoint stays in core app
    # Login, logout, refresh, and me endpoints moved to authentication app
    path('', include(router.urls)),
]
