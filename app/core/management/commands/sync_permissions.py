from django.core.management.base import BaseCommand
from core.permissions_registry import PermissionRegistry


class Command(BaseCommand):
    help = 'Synchronise les permissions définies dans les apps avec la base de données'

    def handle(self, *args, **options):
        self.stdout.write('Synchronisation des permissions...')
        
        created, updated = PermissionRegistry.sync_permissions()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Terminé: {created} permissions créées, {updated} permissions mises à jour'
            )
        )
