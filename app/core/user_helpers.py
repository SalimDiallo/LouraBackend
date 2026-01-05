"""
User Type Helpers
=================
Utilitaires pour travailler avec le système polymorphique BaseUser.
"""


def is_admin_user(user):
    """Vérifie si l'utilisateur est un Admin."""
    return getattr(user, 'user_type', None) == 'admin'


def is_employee_user(user):
    """Vérifie si l'utilisateur est un Employee."""
    return getattr(user, 'user_type', None) == 'employee'


def get_concrete_user(user):
    """
    Retourne l'objet concret (AdminUser ou Employee).
    Utilise la méthode get_concrete_user() de BaseUser si disponible.
    """
    if hasattr(user, 'get_concrete_user'):
        return user.get_concrete_user()
    return user


def get_user_organization(user):
    """
    Retourne l'organisation de l'utilisateur.
    - Admin: première organisation (ou None)
    - Employee: son organisation assignée
    """
    concrete = get_concrete_user(user)
    user_type = getattr(user, 'user_type', None)
    
    if user_type == 'employee':
        return getattr(concrete, 'organization', None)
    elif user_type == 'admin':
        orgs = getattr(concrete, 'organizations', None)
        if orgs:
            return orgs.first()
    return None


def get_user_organizations(user):
    """
    Retourne toutes les organisations de l'utilisateur.
    - Admin: toutes ses organisations
    - Employee: liste contenant son organisation unique
    """
    from core.models import Organization
    
    concrete = get_concrete_user(user)
    user_type = getattr(user, 'user_type', None)
    
    if user_type == 'employee':
        org = getattr(concrete, 'organization', None)
        if org:
            return Organization.objects.filter(id=org.id)
        return Organization.objects.none()
    elif user_type == 'admin':
        return concrete.organizations.all()
    
    return Organization.objects.none()


def user_has_permission(user, permission_code):
    """
    Vérifie si l'utilisateur a une permission.
    - Admin: toujours True
    - Employee: vérifie via assigned_role + custom_permissions
    """
    user_type = getattr(user, 'user_type', None)
    
    if user_type == 'admin':
        return True
    
    if user_type == 'employee':
        concrete = get_concrete_user(user)
        if hasattr(concrete, 'has_permission'):
            return concrete.has_permission(permission_code)
    
    return False


def user_belongs_to_organization(user, organization):
    """
    Vérifie si l'utilisateur appartient à une organisation.
    """
    if organization is None:
        return False
    
    concrete = get_concrete_user(user)
    user_type = getattr(user, 'user_type', None)
    
    if user_type == 'employee':
        user_org = getattr(concrete, 'organization', None)
        return user_org and str(user_org.id) == str(organization.id)
    elif user_type == 'admin':
        return concrete.organizations.filter(id=organization.id).exists()
    
    return False
