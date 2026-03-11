# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0010_leave_balance_optional_type'),
    ]

    operations = [
        # Supprimer les anciennes contraintes d'unicité
        migrations.RemoveConstraint(
            model_name='leavebalance',
            name='unique_balance_per_type',
        ),
        migrations.RemoveConstraint(
            model_name='leavebalance',
            name='unique_global_balance',
        ),

        # Supprimer le champ leave_type
        migrations.RemoveField(
            model_name='leavebalance',
            name='leave_type',
        ),

        # Ajouter la nouvelle contrainte d'unicité (employee, year)
        migrations.AddConstraint(
            model_name='leavebalance',
            constraint=models.UniqueConstraint(
                fields=['employee', 'year'],
                name='unique_employee_year_balance'
            ),
        ),

        # Mettre à jour l'ordering pour supprimer leave_type__name
        migrations.AlterModelOptions(
            name='leavebalance',
            options={
                'ordering': ['-year'],
                'verbose_name': 'Solde de congé',
                'verbose_name_plural': 'Soldes de congés'
            },
        ),
    ]
