"""
Authentication app - Centralized authentication for admin and employee users

This app provides:
- JWT authentication utilities (token generation, cookies management)
- Permission classes for role-based access control
- Login/logout views for both AdminUser and Employee
- Token refresh and validation

Usage:
    from authentication.utils import set_jwt_cookies, clear_jwt_cookies
    from authentication.permissions import IsAdminUser, IsEmployee, IsAdminOrEmployee
"""

default_app_config = 'authentication.apps.AuthenticationConfig'

# Note: Do not import modules here to avoid circular imports during app loading.
# Import directly from submodules:
# - authentication.utils
# - authentication.permissions
# - authentication.views
# - authentication.serializers
