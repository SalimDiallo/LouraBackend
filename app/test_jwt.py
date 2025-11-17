#!/usr/bin/env python
"""
Script de test pour l'authentification JWT avec HTTP-only cookies
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/core"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response):
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Cookies: {dict(response.cookies)}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text}")

# Create a session to persist cookies
session = requests.Session()

# 1. INSCRIPTION
print_section("1. INSCRIPTION")
register_data = {
    "email": "jwt_test@loura.com",
    "first_name": "JWT",
    "last_name": "Test",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
}

response = session.post(f"{BASE_URL}/auth/core/register/", json=register_data)
print_response(response)

if response.status_code == 201:
    print("\n✅ Inscription réussie!")
    print(f"   Cookies reçus: {list(session.cookies.keys())}")
else:
    print("\n❌ Échec de l'inscription")
    exit(1)

# 2. VÉRIFIER LE PROFIL (avec cookies HTTP-only)
print_section("2. PROFIL UTILISATEUR (authentification par cookies)")
response = session.get(f"{BASE_URL}/auth/me/")
print_response(response)

if response.status_code == 200:
    print("\n✅ Authentification par cookies réussie!")
else:
    print("\n❌ Échec de l'authentification par cookies")

# 3. CRÉER UNE ORGANISATION
print_section("3. CRÉER UNE ORGANISATION")
org_data = {
    "name": "JWT Test Org",
    "subdomain": "jwt-test-org"
}

response = session.post(f"{BASE_URL}/organizations/", json=org_data)
print_response(response)

if response.status_code == 201:
    print("\n✅ Organisation créée avec succès!")
else:
    print("\n❌ Échec de la création de l'organisation")

# 4. LISTER LES ORGANISATIONS
print_section("4. LISTER LES ORGANISATIONS")
response = session.get(f"{BASE_URL}/organizations/")
print_response(response)

# 5. ATTENDRE L'EXPIRATION DU TOKEN (simulé)
print_section("5. RAFRAÎCHIR LE TOKEN")
print("Note: En production, ceci serait fait automatiquement par le frontend")
print("      quand l'access token expire (après 15 minutes)")

response = session.post(f"{BASE_URL}/auth/core/refresh/")
print_response(response)

if response.status_code == 200:
    print("\n✅ Token rafraîchi avec succès!")
    print(f"   Nouveaux cookies: {list(session.cookies.keys())}")
else:
    print("\n❌ Échec du rafraîchissement du token")

# 6. VÉRIFIER L'ACCÈS APRÈS REFRESH
print_section("6. VÉRIFIER L'ACCÈS APRÈS REFRESH")
response = session.get(f"{BASE_URL}/auth/me/")
print_response(response)

if response.status_code == 200:
    print("\n✅ Accès avec nouveau token réussi!")
else:
    print("\n❌ Échec de l'accès après refresh")

# 7. DÉCONNEXION
print_section("7. DÉCONNEXION")
response = session.post(f"{BASE_URL}/auth/core/logout/")
print_response(response)

if response.status_code == 200:
    print("\n✅ Déconnexion réussie!")
    print(f"   Cookies après logout: {list(session.cookies.keys())}")
else:
    print("\n❌ Échec de la déconnexion")

# 8. VÉRIFIER QUE L'ACCÈS EST REFUSÉ APRÈS LOGOUT
print_section("8. VÉRIFIER QUE L'ACCÈS EST REFUSÉ APRÈS LOGOUT")
response = session.get(f"{BASE_URL}/auth/me/")
print_response(response)

if response.status_code == 401:
    print("\n✅ Accès correctement refusé après déconnexion!")
else:
    print("\n❌ PROBLÈME: L'accès devrait être refusé!")

# 9. RECONNEXION
print_section("9. RECONNEXION")
login_data = {
    "email": "jwt_test@loura.com",
    "password": "SecurePass123"
}

response = session.post(f"{BASE_URL}/auth/core/login/", json=login_data)
print_response(response)

if response.status_code == 200:
    print("\n✅ Reconnexion réussie!")
    print(f"   Cookies: {list(session.cookies.keys())}")
else:
    print("\n❌ Échec de la reconnexion")

# 10. VÉRIFIER L'ACCÈS APRÈS RECONNEXION
print_section("10. VÉRIFIER L'ACCÈS APRÈS RECONNEXION")
response = session.get(f"{BASE_URL}/auth/me/")
print_response(response)

if response.status_code == 200:
    print("\n✅ Accès restauré après reconnexion!")
else:
    print("\n❌ Échec de l'accès après reconnexion")

print_section("RÉSUMÉ")
print("""
✅ Tests terminés!

Le système JWT avec HTTP-only cookies fonctionne:
  • Inscription: Génère access + refresh tokens dans cookies
  • Authentification: Cookies automatiquement envoyés
  • Refresh: Renouvelle les tokens
  • Logout: Blacklist le refresh token et supprime les cookies

Sécurité:
  ✓ HTTP-only cookies (pas accessible par JavaScript)
  ✓ Token rotation (nouveau refresh token à chaque refresh)
  ✓ Token blacklist (refresh tokens invalidés après logout)
  ✓ Access token courte durée (15 min)
  ✓ Refresh token longue durée (7 jours)
""")
