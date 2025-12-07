"""
Management command to reset employee password
Usage: python manage.py reset_employee_password email@example.com newpassword
"""
from django.core.management.base import BaseCommand, CommandError
from hr.models import Employee


class Command(BaseCommand):
    help = 'Reset password for an employee'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Employee email address')
        parser.add_argument('password', type=str, help='New password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']

        try:
            employee = Employee.objects.get(email=email)
        except Employee.DoesNotExist:
            raise CommandError(f'Employee with email "{email}" does not exist')

        # Set new password
        employee.set_password(password)
        employee.save()

        self.stdout.write(
            self.style.SUCCESS(f'✅ Password reset successfully for {employee.get_full_name()} ({email})')
        )
        self.stdout.write(f'   New password: {password}')
