"""
Authentication URLs
===================
Routes pour l'authentification unifiée Admin/Employee.
"""

from django.urls import path
from .views import (
    LoginView,
    RegisterAdminView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
    UpdateProfileView,
    ChangePasswordView,
    # Legacy
    AdminLoginView,
    EmployeeLoginView,
)

urlpatterns = [
    # === Endpoints principaux ===
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterAdminView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    
    # === Profile management ===
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # === Legacy endpoints (rétrocompatibilité) ===
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('employee/login/', EmployeeLoginView.as_view(), name='employee-login'),
]
