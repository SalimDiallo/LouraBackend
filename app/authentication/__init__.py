"""
Authentication app - Centralized authentication for admin and employee users

This app provides:
- JWT authentication utilities (token generation, cookies management)
- Permission classes (re-exported from core.permissions)
- Login/logout views for both AdminUser and Employee
- Token refresh and validation

Usage:
    from authentication.utils import set_jwt_cookies, clear_jwt_cookies
    from authentication.permissions import IsAdminUser, IsEmployee
"""

default_app_config = 'authentication.apps.AuthenticationConfig'

