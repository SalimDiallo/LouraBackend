"""
Commande Django pour tester manuellement la vérification des échéances de crédit.

Usage:
    python manage.py check_credit_deadlines
    python manage.py check_credit_deadlines --dry-run  # Test sans envoyer de notifications
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventory.models import CreditSale
from notifications.notification_helpers import send_notification
from core.models import BaseUser


class Command(BaseCommand):
    help = 'Vérifie les échéances de ventes à crédit et envoie des notifications de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation - affiche les notifications sans les envoyer',
        )
        parser.add_argument(
            '--org',
            type=str,
            help='Slug de l\'organisation à traiter (toutes par défaut)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        org_slug = options.get('org')

        self.stdout.write(self.style.SUCCESS('=== Vérification des échéances de crédit ==='))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION (dry-run) - Aucune notification ne sera envoyée'))

        today = timezone.now().date()
        self.stdout.write(f'Date: {today.strftime("%d/%m/%Y")}')
        self.stdout.write('')

        # Filtrer par organisation si spécifié
        queryset = CreditSale.objects.filter(
            status__in=['pending', 'partial'],
            due_date__isnull=False
        ).select_related('customer', 'sale', 'organization')

        if org_slug:
            queryset = queryset.filter(organization__slug=org_slug)

        credit_sales = queryset.order_by('due_date')

        if not credit_sales.exists():
            self.stdout.write(self.style.WARNING('Aucune vente à crédit avec échéance trouvée.'))
            return

        self.stdout.write(f'Trouvé {credit_sales.count()} vente(s) à crédit avec échéance\n')

        stats = {
            'total': 0,
            'due_soon': 0,
            'overdue': 0,
            'ok': 0,
        }

        for credit_sale in credit_sales:
            stats['total'] += 1

            # Calculer la date limite effective avec délai de grâce
            effective_due_date = credit_sale.due_date
            if credit_sale.grace_period_days > 0:
                effective_due_date = credit_sale.due_date + timedelta(days=credit_sale.grace_period_days)

            days_until_due = (effective_due_date - today).days

            # Déterminer le statut
            status_icon = '✅'
            status_text = 'OK'
            should_notify = False
            notification_type = None

            if days_until_due < 0:
                status_icon = '🔴'
                status_text = f'RETARD ({abs(days_until_due)} jours)'
                stats['overdue'] += 1
                should_notify = True
                notification_type = 'overdue'
            elif days_until_due == 0:
                status_icon = '⚠️'
                status_text = 'ÉCHÉANCE AUJOURD\'HUI'
                stats['due_soon'] += 1
                should_notify = True
                notification_type = 'due_today'
            elif days_until_due <= 7:
                status_icon = '⏰'
                status_text = f'Échéance dans {days_until_due} jour(s)'
                stats['due_soon'] += 1
                if days_until_due in [1, 3, 7]:
                    should_notify = True
                    notification_type = 'approaching'
            else:
                stats['ok'] += 1

            # Afficher les informations
            customer_name = credit_sale.customer.name if credit_sale.customer else "N/A"
            sale_number = credit_sale.sale.sale_number if credit_sale.sale else "N/A"
            org_name = credit_sale.organization.name

            self.stdout.write(
                f'{status_icon} [{org_name}] Créance #{sale_number} - {customer_name}\n'
                f'   Montant restant: {credit_sale.remaining_amount:,.0f} FCFA\n'
                f'   Due: {credit_sale.due_date.strftime("%d/%m/%Y")} '
                f'{"(+ " + str(credit_sale.grace_period_days) + " jours grâce)" if credit_sale.grace_period_days > 0 else ""}\n'
                f'   Statut: {status_text}\n'
                f'   Rappels envoyés: {credit_sale.reminder_count}'
            )

            if should_notify:
                if dry_run:
                    self.stdout.write(self.style.WARNING(f'   → [DRY-RUN] Notification {notification_type} non envoyée'))
                else:
                    # Envoyer la notification
                    admins = BaseUser.objects.filter(
                        organizations=credit_sale.organization,
                        role__in=['admin', 'super_admin'],
                        is_active=True
                    )

                    for admin in admins:
                        try:
                            if notification_type == 'overdue':
                                title = f"🔴 Paiement en retard ({abs(days_until_due)} jours) - {customer_name}"
                            elif notification_type == 'due_today':
                                title = f"⚠️ Échéance aujourd'hui - {customer_name}"
                            else:
                                title = f"⏰ Échéance dans {days_until_due} jours - {customer_name}"

                            message = (
                                f"Créance #{sale_number}\n"
                                f"Client: {customer_name}\n"
                                f"Montant restant: {credit_sale.remaining_amount:,.0f} FCFA\n"
                                f"Date d'échéance: {credit_sale.due_date.strftime('%d/%m/%Y')}"
                            )

                            send_notification(
                                organization=credit_sale.organization,
                                recipient=admin,
                                title=title,
                                message=message,
                                notification_type='alert',
                                priority='high' if days_until_due <= 1 else 'medium',
                                entity_type='credit_sale',
                                entity_id=str(credit_sale.id),
                                action_url=f'/inventory/credit-sales/{credit_sale.id}'
                            )

                            self.stdout.write(self.style.SUCCESS(f'   → Notification envoyée à {admin.email}'))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'   → Erreur: {str(e)}'))

                    # Mettre à jour le tracking
                    if not dry_run:
                        credit_sale.last_reminder_date = today
                        credit_sale.reminder_count += 1
                        credit_sale.save(update_fields=['last_reminder_date', 'reminder_count'])

            self.stdout.write('')

        # Afficher les statistiques
        self.stdout.write(self.style.SUCCESS('=== STATISTIQUES ==='))
        self.stdout.write(f'Total: {stats["total"]}')
        self.stdout.write(self.style.SUCCESS(f'OK: {stats["ok"]}'))
        self.stdout.write(self.style.WARNING(f'Échéance proche: {stats["due_soon"]}'))
        self.stdout.write(self.style.ERROR(f'En retard: {stats["overdue"]}'))
