"""
Management command to initialize HR permissions and system roles
Usage: python manage.py init_permissions
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from hr.models import Permission, Role
from hr.constants import PERMISSIONS, PREDEFINED_ROLES


class Command(BaseCommand):
    help = 'Initialize HR permissions and system roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Initializing HR permissions and roles...'))

        with transaction.atomic():
            # Create permissions
            self.stdout.write('Creating permissions...')
            permissions_created = 0
            permissions_updated = 0

            for code, perm_data in PERMISSIONS.items():
                permission, created = Permission.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': perm_data['name'],
                        'category': perm_data['category'],
                        'description': perm_data['description'],
                    }
                )

                if created:
                    permissions_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {permission.name}'))
                else:
                    permissions_updated += 1
                    self.stdout.write(f'  - Updated: {permission.name}')

            self.stdout.write(self.style.SUCCESS(
                f'\nPermissions: {permissions_created} created, {permissions_updated} updated'
            ))

            # Create system roles
            self.stdout.write('\nCreating system roles...')
            roles_created = 0
            roles_updated = 0

            for role_code, role_data in PREDEFINED_ROLES.items():
                # Get or create the role
                role, created = Role.objects.update_or_create(
                    code=role_code,
                    organization=None,  # System roles have no organization
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'is_system_role': role_data['is_system_role'],
                        'is_active': True,
                    }
                )

                # Clear existing permissions and add new ones
                role.permissions.clear()

                permission_objects = Permission.objects.filter(
                    code__in=role_data['permissions']
                )
                role.permissions.add(*permission_objects)

                if created:
                    roles_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ Created role: {role.name} ({len(role_data["permissions"])} permissions)'
                    ))
                else:
                    roles_updated += 1
                    self.stdout.write(
                        f'  - Updated role: {role.name} ({len(role_data["permissions"])} permissions)'
                    )

            self.stdout.write(self.style.SUCCESS(
                f'\nRoles: {roles_created} created, {roles_updated} updated'
            ))

            # Display summary
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
            self.stdout.write(self.style.SUCCESS('Initialization complete!'))
            self.stdout.write(self.style.SUCCESS(f'Total permissions: {Permission.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'Total system roles: {Role.objects.filter(is_system_role=True).count()}'))
            self.stdout.write(self.style.SUCCESS('=' * 50))
