from rest_framework import permissions

from core.models import AdminUser


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

        # Allow both AdminUser and Employee
        if not isinstance(request.user, (Employee, AdminUser)):
            return False

        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for HR admin or AdminUser
        if isinstance(request.user, AdminUser):
            return True

        if isinstance(request.user, Employee):
            return request.user.is_hr_admin()

        return False


class IsHRAdmin(permissions.BasePermission):
    """
    Permission: Only HR Admin or AdminUser can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        # AdminUser always has admin access
        if isinstance(request.user, AdminUser):
            return True

        # Employee must be HR admin
        if isinstance(request.user, Employee):
            return request.user.is_hr_admin()

        return False


class IsManagerOrHRAdmin(permissions.BasePermission):
    """
    Permission: Manager or HR Admin can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        # AdminUser always has access
        if isinstance(request.user, AdminUser):
            return True

        # Employee must be HR admin or have manager role
        if isinstance(request.user, Employee):
            if request.user.is_hr_admin():
                return True
            # Check if user has manager role or manages subordinates
            if request.user.assigned_role and request.user.assigned_role.code == 'manager':
                return True
            # Also check if employee manages anyone
            if request.user.subordinates.exists():
                return True

        return False


class IsOwnerOrHRAdmin(permissions.BasePermission):
    """
    Permission: Owner of the object or HR Admin can access
    """

    def has_permission(self, request, view):
        from hr.models import Employee

        if not request.user or not request.user.is_authenticated:
            return False

        return isinstance(request.user, (AdminUser, Employee))

    def has_object_permission(self, request, view, obj):
        from hr.models import Employee

        # AdminUser can access everything in their organizations
        if isinstance(request.user, AdminUser):
            if hasattr(obj, 'organization'):
                return obj.organization.admin == request.user
            elif hasattr(obj, 'employee'):
                return obj.employee.organization.admin == request.user
            return True

        if not isinstance(request.user, Employee):
            return False

        # HR Admin can access everything in their organization
        if request.user.is_hr_admin():
            # Check organization match
            if hasattr(obj, 'organization'):
                return obj.organization == request.user.organization
            elif hasattr(obj, 'employee'):
                return obj.employee.organization == request.user.organization
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
