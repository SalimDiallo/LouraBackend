from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet,
    CategoryViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    # Register endpoint stays in core app
    # Login, logout, refresh, and me endpoints moved to authentication app
    path('', include(router.urls)),
]
