#!/usr/bin/env python
"""
Script de test pour l'API de gestion des organisations.
Ce script teste la création, modification et affichage des organisations.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lourabackend.settings')
django.setup()

from core.models import AdminUser, Organization, Category
from django.db import transaction


def test_organization_management():
    """Test complet de la gestion des organisations"""

    print("=" * 60)
    print("TEST DE GESTION DES ORGANISATIONS")
    print("=" * 60)

    # 1. Créer un AdminUser de test
    print("\n1️⃣  Création d'un AdminUser de test...")
    try:
        with transaction.atomic():
            admin_user, created = AdminUser.objects.get_or_create(
                email="test@example.com",
                defaults={
                    "first_name": "Test",
                    "last_name": "User"
                }
            )
            if created:
                admin_user.set_password("password123")
                admin_user.save()
                print(f"   ✅ AdminUser créé: {admin_user.email}")
            else:
                print(f"   ℹ️  AdminUser existant: {admin_user.email}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 2. Afficher les catégories disponibles
    print("\n2️⃣  Catégories disponibles:")
    categories = Category.objects.all()
    for cat in categories:
        print(f"   - [{cat.id}] {cat.name}: {cat.description}")

    if not categories.exists():
        print("   ⚠️  Aucune catégorie disponible!")
        print("   💡 Exécutez: python manage.py create_sample_categories")
        return

    # 3. Créer une organisation
    print("\n3️⃣  Création d'une organisation...")
    try:
        category_tech = Category.objects.get(name="Technologie")

        organization, created = Organization.objects.get_or_create(
            subdomain="test-enterprise",
            defaults={
                "name": "Test Enterprise",
                "admin": admin_user,
                "category": category_tech,
                "logo_url": "https://example.com/logo.png"
            }
        )

        if created:
            print(f"   ✅ Organisation créée: {organization.name}")
            print(f"      - Subdomain: {organization.subdomain}")
            print(f"      - Catégorie: {organization.category.name}")
            print(f"      - Admin: {organization.admin.email}")
        else:
            print(f"   ℹ️  Organisation existante: {organization.name}")
    except Category.DoesNotExist:
        print("   ❌ Catégorie 'Technologie' non trouvée!")
        category_tech = categories.first()
        print(f"   💡 Utilisation de '{category_tech.name}' à la place")

        organization, created = Organization.objects.get_or_create(
            subdomain="test-enterprise",
            defaults={
                "name": "Test Enterprise",
                "admin": admin_user,
                "category": category_tech,
                "logo_url": "https://example.com/logo.png"
            }
        )
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return

    # 4. Modifier l'organisation
    print("\n4️⃣  Modification de l'organisation...")
    try:
        organization.name = "Test Enterprise - MODIFIÉ"
        organization.is_active = False
        organization.save()
        print(f"   ✅ Organisation modifiée:")
        print(f"      - Nouveau nom: {organization.name}")
        print(f"      - Active: {organization.is_active}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

    # 5. Afficher toutes les organisations de l'admin
    print("\n5️⃣  Organisations de l'admin:")
    user_organizations = admin_user.get_organizations_for_admin()
    for org in user_organizations:
        status = "✓ Active" if org.is_active else "✗ Inactive"
        print(f"   - {org.name} ({org.subdomain}) [{status}]")
        print(f"     Catégorie: {org.category.name if org.category else 'Aucune'}")
        print(f"     Créée le: {org.created_at.strftime('%Y-%m-%d %H:%M')}")

    # 6. Tester les settings de l'organisation
    print("\n6️⃣  Settings de l'organisation:")
    settings = organization.settings
    print(f"   - Pays: {settings.country or 'Non défini'}")
    print(f"   - Devise: {settings.currency}")
    print(f"   - Thème: {settings.theme or 'Non défini'}")
    print(f"   - Email contact: {settings.contact_email or 'Non défini'}")

    # 7. Statistiques finales
    print("\n7️⃣  Statistiques:")
    print(f"   - Total AdminUsers: {AdminUser.objects.count()}")
    print(f"   - Total Organisations: {Organization.objects.count()}")
    print(f"   - Total Catégories: {Category.objects.count()}")
    print(f"   - Organisations actives: {Organization.objects.filter(is_active=True).count()}")
    print(f"   - Organisations inactives: {Organization.objects.filter(is_active=False).count()}")

    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS AVEC SUCCÈS!")
    print("=" * 60)


if __name__ == "__main__":
    test_organization_management()
