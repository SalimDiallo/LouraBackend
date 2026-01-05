from django.conf import settings
from django.utils.module_loading import import_string
from django.apps import apps
from core.models import Permission

class PermissionRegistry:
    """
    Central registry for application permissions.
    Reads permissions from `app.permissions.PERMISSIONS` list in each installed app.
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
    def sync_permissions():
        """
        Syncs defined permissions with the database.
        Creates new ones, updates existing ones.
        Does NOT delete permissions to avoid breaking existing assignments.
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
