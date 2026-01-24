from django.conf import settings
from django.utils.module_loading import import_string
from django.apps import apps
from core.models import Permission, Role

class PermissionRegistry:
    """
    Central registry for application permissions and roles.
    Reads from `app.permissions.PERMISSIONS` and `app.permissions.PREDEFINED_ROLES`.
    """
    
    @staticmethod
    def get_all_permissions():
        """
        Collects all permissions from all installed apps.
        Returns a list of dicts.
        """
        all_permissions = []
        
        for app_config in apps.get_app_configs():
            try:
                # Try to import permissions module from the app
                from importlib import import_module
                permissions_module = import_module(f"{app_config.name}.permissions")
                
                # Look for PERMISSIONS list
                if hasattr(permissions_module, 'PERMISSIONS'):
                    app_permissions = getattr(permissions_module, 'PERMISSIONS')
                    if isinstance(app_permissions, list):
                        all_permissions.extend(app_permissions)
            except ImportError:
                # App doesn't have a permissions module, skip
                continue
            except Exception as e:
                print(f"Error loading permissions from {app_config.name}: {e}")
                
        return all_permissions

    @staticmethod
    def get_all_predefined_roles():
        """
        Collects all predefined roles from all installed apps.
        Returns a dict of roles.
        """
        all_roles = {}
        
        for app_config in apps.get_app_configs():
            try:
                from importlib import import_module
                permissions_module = import_module(f"{app_config.name}.permissions")
                
                if hasattr(permissions_module, 'PREDEFINED_ROLES'):
                    app_roles = getattr(permissions_module, 'PREDEFINED_ROLES')
                    if isinstance(app_roles, dict):
                        all_roles.update(app_roles)
            except ImportError:
                continue
            except Exception as e:
                print(f"Error loading roles from {app_config.name}: {e}")
                
        return all_roles

    @staticmethod
    def sync_permissions():
        """
        Syncs defined permissions with the database.
        """
        defined_permissions = PermissionRegistry.get_all_permissions()
        created_count = 0
        updated_count = 0
        
        for perm_data in defined_permissions:
            code = perm_data.get('code')
            if not code:
                continue
                
            defaults = {
                'name': perm_data.get('name', code),
                'category': perm_data.get('category', 'General'),
                'description': perm_data.get('description', ''),
            }
            
            obj, created = Permission.objects.update_or_create(
                code=code,
                defaults=defaults
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        return created_count, updated_count

    @staticmethod
    def sync_roles():
        """
        Syncs predefined roles with the database.
        """
        defined_roles = PermissionRegistry.get_all_predefined_roles()
        created_count = 0
        updated_count = 0
        
        for role_code, role_data in defined_roles.items():
            defaults = {
                'name': role_data.get('name', role_code),
                'description': role_data.get('description', ''),
                'is_system_role': role_data.get('is_system_role', True),
            }
            
            # System roles have NO organization (None)
            role_obj, created = Role.objects.update_or_create(
                code=role_code,
                organization=None,
                defaults=defaults
            )
            
            # Sync permissions for this role
            perm_codes = role_data.get('permissions', [])
            permissions = Permission.objects.filter(code__in=perm_codes)
            role_obj.permissions.set(permissions)
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        return created_count, updated_count

    @staticmethod
    def sync_all():
        """
        Syncs both permissions and roles.
        """
        p_created, p_updated = PermissionRegistry.sync_permissions()
        r_created, r_updated = PermissionRegistry.sync_roles()
        return p_created, p_updated, r_created, r_updated
