
from backend.app.core.models import Organization
def get_organization_from_subdomain(subdomain):
    try:
        return Organization.objects.get(subdomain=subdomain)
    except Organization.DoesNotExist:
        return None