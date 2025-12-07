"""
Management command to add QR attendance permissions
"""
from django.core.management.base import BaseCommand
from hr.models import Permission


class Command(BaseCommand):
    help = 'Add QR code attendance permissions to the database'

    def handle(self, *args, **options):
        permissions_to_create = [
            {
                'code': 'can_manual_checkin',
                'name': 'Peut effectuer un pointage manuel',
                'category': 'Pointages',
                'description': 'Permet de pointer manuellement sans QR code. Réservé aux administrateurs qui gèrent les pointages.'
            },
            {
                'code': 'can_create_qr_session',
                'name': 'Peut créer une session QR',
                'category': 'Pointages',
                'description': 'Permet de générer des QR codes pour le pointage des employés.'
            },
        ]

        created_count = 0
        updated_count = 0

        for perm_data in permissions_to_create:
            permission, created = Permission.objects.update_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'category': perm_data['category'],
                    'description': perm_data['description'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created permission: {permission.code}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated permission: {permission.code}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Done! Created {created_count}, Updated {updated_count} permissions.')
        )
