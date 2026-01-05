from rest_framework import permissions

class IsHRAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access for authenticated users.
    Write access is restricted to HR Admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return getattr(request.user, 'is_hr_admin', False)

class IsHRAdmin(permissions.BasePermission):
    """
    Access restricted to HR Admins only.
    """
    def has_permission(self, request, view):
        return getattr(request.user, 'is_hr_admin', False)

class IsManagerOrHRAdmin(permissions.BasePermission):
    """
    Access restricted to Managers or HR Admins.
    """
    def has_permission(self, request, view):
        is_hr = getattr(request.user, 'is_hr_admin', False)
        # Assuming is_manager property or check exists
        is_manager = getattr(request.user, 'is_manager', False) 
        return request.user.is_authenticated and (is_hr or is_manager)

class IsAdminUserOrEmployee(permissions.BasePermission):
    """
    Access allowed to Admin users or Employees.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

class RequiresPermission(permissions.BasePermission):
    """
    Base class for granular permission checks.
    """
    required_permission = None

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not self.required_permission:
            return True
        # Check if user has the specific permission code
        # Assuming has_permission method on user model
        return request.user.has_permission(self.required_permission)

class RequiresCRUDPermission(permissions.BasePermission):
    # Placeholder for CRUD logic
    pass

class CanAccessOwnOrManage(permissions.BasePermission):
     # Placeholder
    @staticmethod
    def for_resource(resource, permission):
        # Stub implementation
        return CanAccessOwnOrManage

class IsDepartmentHeadOrHR(permissions.BasePermission):
     # Placeholder
    pass

class IsManagerOfEmployee(permissions.BasePermission):
     # Placeholder
    pass

# Dynamic permission classes
class RequiresEmployeePermission(RequiresPermission):
    def has_permission(self, request, view):
        # Allow safe methods for everyone for now, or check 'hr.view_employees'
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_permission('hr.view_employees')
        return request.user.has_permission('hr.manage_employees')

class RequiresDepartmentPermission(RequiresPermission):
     def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_permission('hr.view_departments')
        return request.user.has_permission('hr.manage_departments')

class RequiresPositionPermission(permissions.BasePermission): pass # TODO
class RequiresContractPermission(permissions.BasePermission): pass # TODO
class RequiresLeavePermission(permissions.BasePermission): pass # TODO
class RequiresPayrollPermission(permissions.BasePermission): pass # TODO
class RequiresAttendancePermission(permissions.BasePermission): pass # TODO

class RequiresRolePermission(RequiresPermission):
     def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.has_permission('hr.view_roles')
        return request.user.has_permission('hr.manage_roles')
