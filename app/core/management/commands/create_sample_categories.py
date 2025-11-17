from django.core.management.base import BaseCommand
from core.models import Category


class Command(BaseCommand):
    help = 'Crée des catégories d\'exemple pour les organisations'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Technologie',
                'description': 'Entreprises du secteur technologique et informatique'
            },
            {
                'name': 'Santé',
                'description': 'Établissements de santé, cliniques, hôpitaux'
            },
            {
                'name': 'Éducation',
                'description': 'Écoles, universités, centres de formation'
            },
            {
                'name': 'Commerce',
                'description': 'Commerces de détail et distribution'
            },
            {
                'name': 'Services',
                'description': 'Entreprises de services professionnels'
            },
            {
                'name': 'Finance',
                'description': 'Banques, assurances, institutions financières'
            },
            {
                'name': 'Industrie',
                'description': 'Entreprises industrielles et manufacturières'
            },
            {
                'name': 'Restauration',
                'description': 'Restaurants, hôtels, services de restauration'
            },
        ]

        created_count = 0
        existing_count = 0

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Catégorie créée: {category.name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- Catégorie existante: {category.name}')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRésumé: {created_count} créées, {existing_count} existantes'
            )
        )
