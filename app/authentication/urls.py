from django.urls import path
from .views import (
    AdminLoginView,
    EmployeeLoginView,
    LogoutView,
    RefreshTokenView,
    CurrentUserView,
    UpdateProfileView,
    ChangePasswordView,
)

urlpatterns = [
    # Admin authentication
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),

    # Employee authentication
    path('employee/login/', EmployeeLoginView.as_view(), name='employee-login'),

    # Common endpoints
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    
    # Profile management
    path('profile/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
]

