#!/usr/bin/env python
"""
Script de démonstration de l'API de gestion des organisations.
Ce script montre comment interagir avec l'API via des requêtes HTTP.

IMPORTANT: Assurez-vous que le serveur Django est en cours d'exécution:
    python manage.py runserver
"""

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000/api/core"


def print_section(title):
    """Afficher un titre de section"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_response(response, title="Réponse"):
    """Afficher une réponse HTTP formatée"""
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    if response.status_code >= 200 and response.status_code < 300:
        print("✅ Succès")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(response.text)
    else:
        print("❌ Erreur")
        print(response.text)


def main():
    """Fonction principale de démonstration"""

    print_section("🚀 DÉMONSTRATION DE L'API DE GESTION DES ORGANISATIONS")

    # Variables globales pour stocker les données
    access_token = None
    organization_id = None

    # ========================================================================
    # 1. INSCRIPTION D'UN NOUVEL ADMINUSER
    # ========================================================================
    print_section("1️⃣  Inscription d'un nouvel AdminUser")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    register_data = {
        "email": f"demo{timestamp}@example.com",
        "first_name": "Demo",
        "last_name": "User",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }

    print("\nDonnées d'inscription:")
    print(json.dumps(register_data, indent=2))

    response = requests.post(
        f"{BASE_URL}/auth/register/",
        json=register_data
    )

    print_response(response, "Réponse de l'inscription")

    if response.status_code == 201:
        data = response.json()
        access_token = data.get("access")
        print(f"\n🔑 Token d'accès obtenu: {access_token[:50]}...")
    else:
        print("\n⚠️  Inscription échouée. Arrêt du script.")
        return

    # En-têtes avec authentification
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # ========================================================================
    # 2. RÉCUPÉRATION DES INFORMATIONS DE L'UTILISATEUR CONNECTÉ
    # ========================================================================
    print_section("2️⃣  Informations de l'utilisateur connecté")

    response = requests.get(
        f"{BASE_URL}/auth/me/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # 3. LISTER LES CATÉGORIES DISPONIBLES
    # ========================================================================
    print_section("3️⃣  Liste des catégories disponibles")

    response = requests.get(
        f"{BASE_URL}/categories/",
        headers=headers
    )

    print_response(response)

    categories = []
    if response.status_code == 200:
        categories = response.json()
        print(f"\n📊 {len(categories)} catégories disponibles:")
        for cat in categories:
            print(f"   [{cat['id']}] {cat['name']}")

    # ========================================================================
    # 4. CRÉER UNE NOUVELLE ORGANISATION
    # ========================================================================
    print_section("4️⃣  Création d'une nouvelle organisation")

    if not categories:
        print("⚠️  Aucune catégorie disponible. Création impossible.")
        print("💡 Exécutez: python manage.py create_sample_categories")
        return

    # Sélectionner la première catégorie
    selected_category = categories[0]

    organization_data = {
        "name": f"Entreprise Demo {timestamp}",
        "subdomain": f"demo-{timestamp}",
        "logo_url": "https://via.placeholder.com/150",
        "category": selected_category["id"],
        "settings": {
            "country": "GN",
            "currency": "GNF",
            "theme": "light",
            "contact_email": f"contact@demo-{timestamp}.com"
        }
    }

    print("\nDonnées de l'organisation:")
    print(json.dumps(organization_data, indent=2))

    response = requests.post(
        f"{BASE_URL}/organizations/",
        json=organization_data,
        headers=headers
    )

    print_response(response, "Réponse de création")

    if response.status_code == 201:
        data = response.json()
        organization_id = data.get("id")
        print(f"\n🏢 Organisation créée avec l'ID: {organization_id}")
    else:
        print("\n⚠️  Création échouée. Arrêt du script.")
        return

    # ========================================================================
    # 5. LISTER TOUTES LES ORGANISATIONS DE L'UTILISATEUR
    # ========================================================================
    print_section("5️⃣  Liste de mes organisations")

    response = requests.get(
        f"{BASE_URL}/organizations/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # 6. AFFICHER LES DÉTAILS D'UNE ORGANISATION
    # ========================================================================
    print_section("6️⃣  Détails de l'organisation créée")

    response = requests.get(
        f"{BASE_URL}/organizations/{organization_id}/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # 7. MODIFIER L'ORGANISATION (PATCH)
    # ========================================================================
    print_section("7️⃣  Modification partielle de l'organisation")

    update_data = {
        "name": f"Entreprise Demo MODIFIÉE {timestamp}",
        "category": categories[1]["id"] if len(categories) > 1 else categories[0]["id"]
    }

    print("\nDonnées de modification:")
    print(json.dumps(update_data, indent=2))

    response = requests.patch(
        f"{BASE_URL}/organizations/{organization_id}/",
        json=update_data,
        headers=headers
    )

    print_response(response, "Réponse de modification")

    # ========================================================================
    # 8. DÉSACTIVER L'ORGANISATION
    # ========================================================================
    print_section("8️⃣  Désactivation de l'organisation")

    response = requests.post(
        f"{BASE_URL}/organizations/{organization_id}/deactivate/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # 9. RÉACTIVER L'ORGANISATION
    # ========================================================================
    print_section("9️⃣  Réactivation de l'organisation")

    response = requests.post(
        f"{BASE_URL}/organizations/{organization_id}/activate/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # 10. DÉCONNEXION
    # ========================================================================
    print_section("🔟 Déconnexion")

    response = requests.post(
        f"{BASE_URL}/auth/logout/",
        headers=headers
    )

    print_response(response)

    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    print_section("✅ DÉMONSTRATION TERMINÉE")

    print("""
🎉 Félicitations ! Vous avez testé avec succès:

✅ Inscription d'un AdminUser
✅ Authentification JWT
✅ Récupération des informations utilisateur
✅ Liste des catégories
✅ Création d'une organisation avec catégorie
✅ Liste des organisations
✅ Affichage des détails d'une organisation
✅ Modification d'une organisation
✅ Désactivation d'une organisation
✅ Activation d'une organisation
✅ Déconnexion

📚 Pour plus d'informations, consultez:
   - ORGANISATION_API.md (Documentation complète de l'API)
   - GUIDE_ORGANISATIONS.md (Guide d'utilisation)

🚀 L'API est prête à être intégrée avec votre frontend !
    """)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter au serveur Django.")
        print("💡 Assurez-vous que le serveur est en cours d'exécution:")
        print("   python manage.py runserver")
    except KeyboardInterrupt:
        print("\n\n⚠️  Démonstration interrompue par l'utilisateur.")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
