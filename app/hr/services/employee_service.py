"""
Employee Service - Service Layer pour les opérations sur les employés

Ce service encapsule toute la logique métier liée aux employés.
Il est indépendant des vues (Single Responsibility Principle).
"""
import logging
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet
from django.utils import timezone

logger = logging.getLogger(__name__)


class EmployeeService:
    """
    Service pour les opérations métier sur les employés.
    
    Ce service peut être utilisé par :
    - Les ViewSets
    - Les commandes management
    - Les tâches Celery (onboarding automatique, etc.)
    - Les tests
    """
    
    @staticmethod
    def get_employees_for_organization(organization, include_inactive: bool = False) -> QuerySet:
        """
        Retourne les employés d'une organisation.
        
        Args:
            organization: L'organisation
            include_inactive: Inclure les employés inactifs
            
        Returns:
            QuerySet d'employés
        """
        from hr.models import Employee
        
        queryset = Employee.objects.filter(organization=organization)
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @staticmethod
    def get_employee_by_id(employee_id: str, organization=None):
        """
        Récupère un employé par son ID.
        
        Args:
            employee_id: L'ID de l'employé
            organization: Si fourni, vérifie l'appartenance
            
        Returns:
            Employee ou None
        """
        from hr.models import Employee
        
        filters = {'id': employee_id}
        if organization:
            filters['organization'] = organization
            
        return Employee.objects.filter(**filters).first()
    
    @staticmethod
    def get_employee_by_email(email: str, organization=None):
        """
        Récupère un employé par son email.
        
        Args:
            email: L'email de l'employé
            organization: Si fourni, limite la recherche à cette organisation
            
        Returns:
            Employee ou None
        """
        from hr.models import Employee
        
        filters = {'email': email}
        if organization:
            filters['organization'] = organization
            
        return Employee.objects.filter(**filters).first()
    
    @staticmethod
    def create_employee(
        organization,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **kwargs
    ):
        """
        Crée un nouvel employé.
        
        Args:
            organization: L'organisation de l'employé
            email: Email (unique par organisation)
            password: Mot de passe
            first_name: Prénom
            last_name: Nom
            **kwargs: Autres champs (department, position, etc.)
            
        Returns:
            Employee créé
        """
        from hr.models import Employee
        
        employee = Employee.objects.create_user(
            organization=organization,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
        
        logger.info(f"Employee '{email}' created for organization '{organization.name}'")
        return employee
    
    @staticmethod
    def activate_employee(employee) -> bool:
        """Active un employé."""
        employee.is_active = True
        employee.save(update_fields=['is_active'])
        logger.info(f"Employee '{employee.email}' activated")
        return True
    
    @staticmethod
    def deactivate_employee(employee) -> bool:
        """Désactive un employé."""
        employee.is_active = False
        employee.save(update_fields=['is_active'])
        logger.info(f"Employee '{employee.email}' deactivated")
        return True
    
    @staticmethod
    def update_last_login(employee) -> None:
        """Met à jour la date de dernière connexion."""
        employee.last_login = timezone.now()
        employee.save(update_fields=['last_login'])
    
    @staticmethod
    def assign_role(employee, role) -> None:
        """Assigne un rôle à un employé."""
        from hr.models import Role
        
        if isinstance(role, str):
            role = Role.objects.filter(
                code=role,
                organization=employee.organization
            ).first()
            if not role:
                raise ValueError(f"Role '{role}' not found")
        
        employee.assigned_role = role
        employee.save(update_fields=['assigned_role'])
        logger.info(f"Role '{role.name}' assigned to employee '{employee.email}'")
    
    @staticmethod
    def add_custom_permission(employee, permission_code: str) -> bool:
        """Ajoute une permission personnalisée à un employé."""
        from hr.models import Permission
        
        permission = Permission.objects.filter(code=permission_code).first()
        if not permission:
            logger.warning(f"Permission '{permission_code}' not found")
            return False
        
        employee.custom_permissions.add(permission)
        logger.info(f"Permission '{permission_code}' added to employee '{employee.email}'")
        return True
    
    @staticmethod
    def remove_custom_permission(employee, permission_code: str) -> bool:
        """Retire une permission personnalisée d'un employé."""
        from hr.models import Permission
        
        permission = Permission.objects.filter(code=permission_code).first()
        if not permission:
            return False
        
        employee.custom_permissions.remove(permission)
        logger.info(f"Permission '{permission_code}' removed from employee '{employee.email}'")
        return True
    
    @staticmethod
    def get_subordinates(employee) -> QuerySet:
        """Retourne les subordonnés directs d'un employé."""
        from hr.models import Employee
        return Employee.objects.filter(manager=employee, is_active=True)
    
    @staticmethod
    def get_team_members(employee) -> QuerySet:
        """Retourne tous les membres de l'équipe d'un manager (récursif)."""
        from hr.models import Employee
        
        def get_all_subordinates(emp, visited=None):
            if visited is None:
                visited = set()
            
            if emp.id in visited:
                return []
            
            visited.add(emp.id)
            subordinates = list(emp.subordinates.filter(is_active=True))
            
            for sub in subordinates[:]:  # Copy to avoid modification during iteration
                subordinates.extend(get_all_subordinates(sub, visited))
            
            return subordinates
        
        return get_all_subordinates(employee)
    
    @staticmethod
    def employee_has_permission(employee, permission_code: str) -> bool:
        """
        Vérifie si un employé a une permission.
        
        Checks:
        1. Custom permissions
        2. Role permissions
        """
        return employee.has_permission(permission_code)
    
    @staticmethod
    def get_employee_stats(organization) -> Dict[str, Any]:
        """
        Retourne les statistiques des employés d'une organisation.
        
        Returns:
            Dict avec:
            - total: Nombre total
            - active: Nombre actifs
            - inactive: Nombre inactifs
            - by_department: Dict par département
            - by_employment_status: Dict par statut
        """
        from hr.models import Employee
        from django.db.models import Count
        
        employees = Employee.objects.filter(organization=organization)
        
        by_department = employees.values('department__name').annotate(
            count=Count('id')
        ).order_by('department__name')
        
        by_status = employees.values('employment_status').annotate(
            count=Count('id')
        )
        
        return {
            'total': employees.count(),
            'active': employees.filter(is_active=True).count(),
            'inactive': employees.filter(is_active=False).count(),
            'by_department': {item['department__name'] or 'Aucun': item['count'] for item in by_department},
            'by_employment_status': {item['employment_status']: item['count'] for item in by_status},
        }
