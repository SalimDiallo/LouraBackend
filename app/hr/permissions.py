from rest_framework import permissions


class IsEmployeeOfOrganization(permissions.BasePermission):
    """
    Permission check: Employee belongs to the organization
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is an Employee
        from hr.models import Employee
        return isinstance(request.user, Employee)

    def has_object_permission(self, request, view, obj):
        # Check if the object belongs to employee's organization
        from hr.models import Employee

        if not isinstance(request.user, Employee):
            return False

        # Get organization from object
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        elif hasattr(obj, 'employee'):
            return obj.employee.organization == request.user.organization

        return False


class IsHRAdminOrReadOnly(permissions.BasePermission):
    """
    Permission: HR Admin can edit, others can only read
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        if not isinstance(request.user, Employee):
            return False

        # Read permissions are allowed for any employee
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for HR admin
        return request.user.role == 'admin'


class IsHRAdmin(permissions.BasePermission):
    """
    Permission: Only HR Admin can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        if not isinstance(request.user, Employee):
            return False

        return request.user.role == 'admin'


class IsManagerOrHRAdmin(permissions.BasePermission):
    """
    Permission: Manager or HR Admin can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        if not isinstance(request.user, Employee):
            return False

        return request.user.role in ['admin', 'manager']


class IsOwnerOrHRAdmin(permissions.BasePermission):
    """
    Permission: Owner of the object or HR Admin can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        return isinstance(request.user, Employee)

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee

        if not isinstance(request.user, Employee):
            return False

        # HR Admin can access everything
        if request.user.role == 'admin':
            return True

        # Check if user is the owner
        if hasattr(obj, 'employee'):
            return obj.employee == request.user

        return obj == request.user


class IsAdminUserOrEmployee(permissions.BasePermission):
    """
    Permission: AdminUser (from core app) or Employee can access
    Used for mixed endpoints
    """

    def has_permission(self, request, view):
        from core.models import AdminUser
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        return isinstance(request.user, (AdminUser, Employee))
