"""
HR Services - Service Layer pour les opérations métier HR

Ce module implémente le Service Layer Pattern pour l'app HR.
Chaque service encapsule une responsabilité unique (Single Responsibility Principle).
"""
from .employee_service import EmployeeService
from .leave_service import LeaveService
from .payroll_service import PayrollService

__all__ = [
    'EmployeeService',
    'LeaveService',
    'PayrollService',
]
