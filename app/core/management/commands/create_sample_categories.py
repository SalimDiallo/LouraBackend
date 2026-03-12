from django.core.management.base import BaseCommand
from core.models import Category
from core.modules import get_category_module_mapping


class Command(BaseCommand):
    help = 'Crée des catégories d\'exemple pour les organisations avec leurs modules par défaut'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-modules',
            action='store_true',
            help='Afficher les modules par défaut pour chaque catégorie',
        )

    def handle(self, *args, **options):
        show_modules = options.get('with_modules', False)

        # Récupérer le mapping catégories -> modules
        category_module_mapping = get_category_module_mapping()

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
             {
                'name': 'BTP',
                'description': 'Bâtiment et travaux publics : construction, génie civil'
            },
            {
                'name': 'Transports',
                'description': 'Transport de marchandises, logistique, mobilité'
            },
            {
                'name': 'Agriculture',
                'description': 'Exploitations agricoles, production végétale et animale'
            },
            {
                'name': 'Energie',
                'description': 'Production et distribution d\'énergie, énergies renouvelables'
            },
            {
                'name': 'Média & Communication',
                'description': 'Presse, agences de communication, médias numériques'
            },
            {
                'name': 'Immobilier',
                'description': 'Agences immobilières, gestion de biens, promotion'
            },
            {
                'name': 'Associatif',
                'description': 'Associations, ONG, fondations'
            },
             {
                'name': 'Agence de voyage',
                'description': 'Agence de voyage, de tourisme, de billetterie'
            },
            {
                'name': 'Art & Culture',
                'description': 'Galeries, musées, spectacles, organisations culturelles'
            },
        ]

        self.stdout.write(self.style.HTTP_INFO('='*70))
        self.stdout.write(self.style.HTTP_INFO('  Création des catégories d\'organisations'))
        self.stdout.write(self.style.HTTP_INFO('='*70))
        self.stdout.write('')

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

            # Afficher les modules par défaut si demandé
            if show_modules:
                modules = category_module_mapping.get(category.name, [])
                if modules:
                    self.stdout.write(f'  → Modules par défaut ({len(modules)}):')
                    for module_code in modules:
                        self.stdout.write(f'     • {module_code}')
                else:
                    self.stdout.write(f'  → Aucun module par défaut spécifique')
                self.stdout.write('')

        self.stdout.write('='*70)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Résumé: {created_count} créées, {existing_count} existantes'
            )
        )

        if not show_modules:
            self.stdout.write(
                self.style.HTTP_INFO(
                    '\n💡 Utilisez --with-modules pour voir les modules par défaut de chaque catégorie\n'
                )
            )
        else:
            self.stdout.write('')
