from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Auth views
    EmployeeLoginView,
    EmployeeLogoutView,
    EmployeeMeView,
    EmployeeChangePasswordView,
    # ViewSets
    EmployeeViewSet,
    DepartmentViewSet,
    PositionViewSet,
    ContractViewSet,
    LeaveTypeViewSet,
    LeaveBalanceViewSet,
    LeaveRequestViewSet,
    PayrollPeriodViewSet,
    PayslipViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'leave-types', LeaveTypeViewSet, basename='leavetype')
router.register(r'leave-balances', LeaveBalanceViewSet, basename='leavebalance')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leaverequest')
router.register(r'payroll-periods', PayrollPeriodViewSet, basename='payrollperiod')
router.register(r'payslips', PayslipViewSet, basename='payslip')

urlpatterns = [
    # Employee Authentication Endpoints
    path('auth/login/', EmployeeLoginView.as_view(), name='employee-login'),
    path('auth/logout/', EmployeeLogoutView.as_view(), name='employee-logout'),
    path('auth/me/', EmployeeMeView.as_view(), name='employee-me'),
    path('auth/change-password/', EmployeeChangePasswordView.as_view(), name='employee-change-password'),

    # Include router URLs
    path('', include(router.urls)),
]
