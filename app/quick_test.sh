#!/bin/bash

# Script de test rapide pour l'API Loura
# Usage: ./quick_test.sh

BASE_URL="http://localhost:8000/api/core"
EMAIL="test_$(date +%s)@loura.com"  # Email unique avec timestamp

echo "======================================"
echo "  TEST API LOURA - $(date)"
echo "======================================"
echo ""

# Vérifier si le serveur est accessible
echo "🔍 Vérification du serveur..."
if ! curl -s -f "$BASE_URL/" > /dev/null 2>&1; then
    echo "❌ Erreur: Le serveur n'est pas accessible sur $BASE_URL"
    echo "💡 Assurez-vous que le serveur Django est lancé avec: python manage.py runserver"
    exit 1
fi
echo "✅ Serveur accessible"
echo ""

# 1. INSCRIPTION
echo "📝 1. INSCRIPTION - Création d'un compte AdminUser"
echo "   Email: $EMAIL"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/core/register/" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"first_name\": \"Test\",
    \"last_name\": \"User\",
    \"password\": \"SecurePass123\",
    \"password_confirm\": \"SecurePass123\"
  }")

# Extraire le token
TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Échec de l'inscription"
    echo "$REGISTER_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$REGISTER_RESPONSE"
    exit 1
fi

echo "✅ Inscription réussie!"
echo "   Token: ${TOKEN:0:20}..."
echo ""

# 2. PROFIL
echo "👤 2. RÉCUPÉRATION DU PROFIL"
PROFILE_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me/" \
  -H "Authorization: Token $TOKEN")

echo "$PROFILE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PROFILE_RESPONSE"
echo ""

# 3. CRÉER ORGANISATION 1
echo "🏢 3. CRÉATION D'ORGANISATION #1"
ORG1_RESPONSE=$(curl -s -X POST "$BASE_URL/organizations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{
    "name": "Ma Première Organisation",
    "subdomain": "org-1-'$(date +%s)'"
  }')

echo "$ORG1_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ORG1_RESPONSE"
echo ""

# 4. CRÉER ORGANISATION 2 (avec settings)
echo "🏢 4. CRÉATION D'ORGANISATION #2 (avec settings)"
ORG2_RESPONSE=$(curl -s -X POST "$BASE_URL/organizations/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{
    "name": "Tech Solutions",
    "subdomain": "tech-'$(date +%s)'",
    "logo_url": "https://example.com/logo.png",
    "settings": {
      "country": "GN",
      "currency": "GNF",
      "theme": "dark",
      "contact_email": "contact@tech-solutions.com"
    }
  }')

echo "$ORG2_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ORG2_RESPONSE"
echo ""

# 5. LISTER ORGANISATIONS
echo "📋 5. LISTE DE MES ORGANISATIONS"
ORGS_RESPONSE=$(curl -s -X GET "$BASE_URL/organizations/" \
  -H "Authorization: Token $TOKEN")

echo "$ORGS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ORGS_RESPONSE"
echo ""

# Extraire l'ID de la première organisation
ORG_ID=$(echo "$ORGS_RESPONSE" | python3 -c "import sys, json; orgs = json.load(sys.stdin); print(orgs[0]['id'] if orgs else '')" 2>/dev/null)

if [ ! -z "$ORG_ID" ]; then
    # 6. MODIFIER ORGANISATION
    echo "✏️  6. MODIFICATION DE L'ORGANISATION"
    echo "   ID: $ORG_ID"
    UPDATE_RESPONSE=$(curl -s -X PATCH "$BASE_URL/organizations/$ORG_ID/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Token $TOKEN" \
      -d '{
        "name": "Organisation Modifiée"
      }')

    echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
    echo ""

    # 7. DÉSACTIVER ORGANISATION
    echo "⏸️  7. DÉSACTIVATION DE L'ORGANISATION"
    DEACTIVATE_RESPONSE=$(curl -s -X POST "$BASE_URL/organizations/$ORG_ID/deactivate/" \
      -H "Authorization: Token $TOKEN")

    echo "$DEACTIVATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DEACTIVATE_RESPONSE"
    echo ""

    # 8. RÉACTIVER ORGANISATION
    echo "▶️  8. RÉACTIVATION DE L'ORGANISATION"
    ACTIVATE_RESPONSE=$(curl -s -X POST "$BASE_URL/organizations/$ORG_ID/activate/" \
      -H "Authorization: Token $TOKEN")

    echo "$ACTIVATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ACTIVATE_RESPONSE"
    echo ""
fi

# 9. LISTER CATÉGORIES
echo "🗂️  9. LISTE DES CATÉGORIES"
CATEGORIES_RESPONSE=$(curl -s -X GET "$BASE_URL/categories/" \
  -H "Authorization: Token $TOKEN")

echo "$CATEGORIES_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CATEGORIES_RESPONSE"
echo ""

# 10. PROFIL FINAL
echo "👤 10. PROFIL FINAL (après création des organisations)"
FINAL_PROFILE=$(curl -s -X GET "$BASE_URL/auth/me/" \
  -H "Authorization: Token $TOKEN")

echo "$FINAL_PROFILE" | python3 -m json.tool 2>/dev/null || echo "$FINAL_PROFILE"
echo ""

# 11. DÉCONNEXION
echo "👋 11. DÉCONNEXION"
LOGOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/core/logout/" \
  -H "Authorization: Token $TOKEN")

echo "$LOGOUT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGOUT_RESPONSE"
echo ""

echo "======================================"
echo "✅ TOUS LES TESTS SONT TERMINÉS!"
echo "======================================"
echo ""
echo "📊 Résumé:"
echo "   • Email créé: $EMAIL"
echo "   • Token: ${TOKEN:0:30}..."
echo "   • Organisations créées: 2"
echo ""
echo "💡 Pour refaire ces tests, relancez: ./quick_test.sh"
echo "📖 Pour plus de détails, consultez: GUIDE_TEST.md"
