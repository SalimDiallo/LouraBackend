from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Auth views
    EmployeeChangePasswordView,
    # ViewSets
    EmployeeViewSet,
    DepartmentViewSet,
    PositionViewSet,
    ContractViewSet,
    LeaveTypeViewSet,
    # LeaveBalanceViewSet,
    LeaveRequestViewSet,
    PayrollPeriodViewSet,
    PayslipViewSet,
    PayrollAdvanceViewSet,
    PermissionViewSet,
    RoleViewSet,
    AttendanceViewSet,
    # Stats views
    PayrollStatsView,
    HROverviewStatsView,
    DepartmentStatsView,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'leave-types', LeaveTypeViewSet, basename='leavetype')
# router.register(r'leave-balances', LeaveBalanceViewSet,basename='leavebalance')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'payroll-periods', PayrollPeriodViewSet, basename='payrollperiod')
router.register(r'payslips', PayslipViewSet, basename='payslip')
router.register(r'payroll-advances', PayrollAdvanceViewSet, basename='payrolladvance')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'attendances', AttendanceViewSet, basename='attendance')

urlpatterns = [
    # Employee Authentication Endpoints
    # Login, refresh, logout, and me endpoints have been moved to authentication app
    path('auth/change-password/', EmployeeChangePasswordView.as_view(), name='employee-change-password'),

    # Stats Endpoints
    path('stats/payroll/', PayrollStatsView.as_view(), name='payroll-stats'),
    path('stats/overview/', HROverviewStatsView.as_view(), name='hr-overview-stats'),
    path('stats/departments/', DepartmentStatsView.as_view(), name='department-stats'),

    path('', include(router.urls)),
]
