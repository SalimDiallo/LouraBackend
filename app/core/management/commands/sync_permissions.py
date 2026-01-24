from django.core.management.base import BaseCommand
from core.permissions_registry import PermissionRegistry


class Command(BaseCommand):
    help = 'Synchronise les permissions et les rôles définis dans les apps avec la base de données'

    def handle(self, *args, **options):
        self.stdout.write('Synchronisation du système de permissions...')
        
        p_created, p_updated, r_created, r_updated = PermissionRegistry.sync_all()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Permissions : {p_created} créées, {p_updated} mises à jour'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Rôles : {r_created} créés, {r_updated} mis à jour'
            )
        )
        self.stdout.write(self.style.SUCCESS('Synchronisation terminée avec succès !'))
