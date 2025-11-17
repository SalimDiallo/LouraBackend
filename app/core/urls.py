from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
    OrganizationViewSet,
    CategoryViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('auth/me/', CurrentUserView.as_view(), name='current-user'),
    path('', include(router.urls)),
]
