"""
Management command to initialize all modules in the database.
This command reads module definitions from core.modules and creates/updates them in the database.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Module
from core.modules import ModuleRegistry


class Command(BaseCommand):
    help = 'Initialize or update all modules in the database from module definitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually modifying the database',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update of all modules, even if they already exist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 MODE DRY-RUN: Aucune modification ne sera effectuée\n'))

        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write(self.style.HTTP_INFO('  Initialisation des modules'))
        self.stdout.write(self.style.HTTP_INFO('='*60))

        # Récupérer toutes les définitions de modules
        module_definitions = ModuleRegistry.get_all_modules()

        if not module_definitions:
            self.stdout.write(self.style.WARNING('\n⚠️  Aucun module trouvé dans le registry'))
            return

        self.stdout.write(f'\n📦 {len(module_definitions)} module(s) trouvé(s) dans le registry\n')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for module_def in module_definitions:
                try:
                    module, created = Module.objects.get_or_create(
                        code=module_def.code,
                        defaults=module_def.to_dict()
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Module créé: {module.name} ({module.code})'
                            )
                        )
                        self._print_module_details(module_def)

                    elif force:
                        # Mise à jour forcée
                        module_data = module_def.to_dict()
                        for key, value in module_data.items():
                            setattr(module, key, value)

                        if not dry_run:
                            module.save()

                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⟳ Module mis à jour: {module.name} ({module.code})'
                            )
                        )

                    else:
                        skipped_count += 1
                        self.stdout.write(
                            f'  - Module existant (ignoré): {module.name} ({module.code})'
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Erreur pour {module_def.code}: {str(e)}'
                        )
                    )

            if dry_run:
                # Rollback en mode dry-run
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING('\n🔄 Rollback effectué (dry-run)\n'))

        # Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✅ Résumé de l\'initialisation:'))
        self.stdout.write(f'   • Modules créés: {created_count}')
        self.stdout.write(f'   • Modules mis à jour: {updated_count}')
        self.stdout.write(f'   • Modules ignorés: {skipped_count}')
        self.stdout.write(f'   • Total: {created_count + updated_count + skipped_count}\n')

        if not dry_run and created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '💡 Les modules ont été initialisés avec succès !\n'
                )
            )

        if force and updated_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  {updated_count} module(s) ont été mis à jour (--force)\n'
                )
            )

        # Conseils
        if skipped_count > 0 and not force:
            self.stdout.write(
                self.style.HTTP_INFO(
                    '💡 Utilisez --force pour mettre à jour les modules existants\n'
                )
            )

    def _print_module_details(self, module_def):
        """Affiche les détails d'un module"""
        if module_def.default_for_all:
            self.stdout.write(f'     → Activé par défaut pour toutes les catégories')
        elif module_def.default_categories:
            categories_str = ', '.join(module_def.default_categories[:3])
            if len(module_def.default_categories) > 3:
                categories_str += f' (+{len(module_def.default_categories) - 3} autres)'
            self.stdout.write(f'     → Par défaut pour: {categories_str}')

        if module_def.is_core:
            self.stdout.write(f'     → Module core (ne peut pas être désactivé)')

        if module_def.depends_on:
            self.stdout.write(f'     → Dépend de: {", ".join(module_def.depends_on)}')
