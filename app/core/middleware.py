"""
Custom middleware for JWT authentication with HTTP-only cookies
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class JWTAuthCookieMiddleware(MiddlewareMixin):
    """
    Middleware to extract JWT token from HTTP-only cookie and add it to the Authorization header.
    This allows DRF JWT authentication to work with cookies instead of requiring the client
    to manually set the Authorization header.
    """

    def process_request(self, request):
        # Get access token from cookie
        access_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if access_token:
            # Add token to Authorization header if not already present
            if not request.META.get('HTTP_AUTHORIZATION'):
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        return None
