from django.core.management.base import BaseCommand
from core.permissions_registry import PermissionRegistry

class Command(BaseCommand):
    help = 'Syncs application permissions to the database'

    def handle(self, *args, **options):
        self.stdout.write('Syncing permissions...')
        
        try:
            created, updated = PermissionRegistry.sync_permissions()
            self.stdout.write(self.style.SUCCESS(f'Successfully synced permissions. Created: {created}, Updated: {updated}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error syncing permissions: {e}'))
