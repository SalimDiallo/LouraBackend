# Guide de test - API Loura Backend

## Démarrage du serveur

```bash
# Assurez-vous d'être dans le bon répertoire
cd /home/salim/Projets/loura/stack/backend/app

# Activez l'environnement virtuel
source ../venv/bin/activate

# Lancez le serveur
python manage.py runserver
```

Le serveur sera accessible sur `http://localhost:8000`

---

## Méthode 1 : Test avec cURL (Ligne de commande)

### 1. Inscription d'un AdminUser

```bash
curl -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@loura.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
  }'
```

**Réponse attendue :**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "admin@loura.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T...",
    "organizations_count": 0
  },
  "token": "votre-token-ici",
  "message": "Inscription réussie"
}
```

**⚠️ Important : Copiez le token pour les prochaines requêtes !**

### 2. Connexion

```bash
curl -X POST http://localhost:8000/api/core/auth/core/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@loura.com",
    "password": "SecurePass123"
  }'
```

### 3. Récupérer son profil

```bash
# Remplacez <TOKEN> par votre token
curl -X GET http://localhost:8000/api/core/auth/me/ \
  -H "Authorization: Token <TOKEN>"
```

### 4. Créer une organisation

```bash
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <TOKEN>" \
  -d '{
    "name": "Mon Entreprise",
    "subdomain": "mon-entreprise"
  }'
```

**Réponse attendue :**
```json
{
  "name": "Mon Entreprise",
  "subdomain": "mon-entreprise",
  "logo_url": null,
  "category": null,
  "settings": {
    "country": null,
    "currency": "MAD",
    "theme": null,
    "contact_email": null
  }
}
```

### 5. Lister ses organisations

```bash
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token <TOKEN>"
```

### 6. Créer une organisation avec settings

```bash
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <TOKEN>" \
  -d '{
    "name": "Tech Solutions",
    "subdomain": "tech-solutions",
    "logo_url": "https://example.com/logo.png",
    "settings": {
      "country": "GN",
      "currency": "GNF",
      "theme": "dark",
      "contact_email": "contact@tech-solutions.com"
    }
  }'
```

### 7. Modifier une organisation

```bash
# Remplacez <ORG_ID> par l'ID de votre organisation
curl -X PATCH http://localhost:8000/api/core/organizations/<ORG_ID>/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <TOKEN>" \
  -d '{
    "name": "Nouveau nom"
  }'
```

### 8. Activer/Désactiver une organisation

```bash
# Désactiver
curl -X POST http://localhost:8000/api/core/organizations/<ORG_ID>/deactivate/ \
  -H "Authorization: Token <TOKEN>"

# Activer
curl -X POST http://localhost:8000/api/core/organizations/<ORG_ID>/activate/ \
  -H "Authorization: Token <TOKEN>"
```

### 9. Lister les catégories

```bash
curl -X GET http://localhost:8000/api/core/categories/ \
  -H "Authorization: Token <TOKEN>"
```

### 10. Déconnexion

```bash
curl -X POST http://localhost:8000/api/core/auth/core/logout/ \
  -H "Authorization: Token <TOKEN>"
```

---

## Méthode 2 : Test avec Python (Script)

Créez un fichier `test_api.py` :

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/core"

# 1. Inscription
print("=== INSCRIPTION ===")
register_data = {
    "email": "test@loura.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
}

response = requests.post(f"{BASE_URL}/auth/core/register/", json=register_data)
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2))

# Sauvegarder le token
token = result.get('token')
headers = {"Authorization": f"Token {token}"}

# 2. Profil utilisateur
print("\n=== MON PROFIL ===")
response = requests.get(f"{BASE_URL}/auth/me/", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 3. Créer une organisation
print("\n=== CRÉER ORGANISATION ===")
org_data = {
    "name": "Ma Startup",
    "subdomain": "ma-startup",
    "settings": {
        "country": "GN",
        "currency": "GNF"
    }
}

response = requests.post(f"{BASE_URL}/organizations/", json=org_data, headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# 4. Lister mes organisations
print("\n=== MES ORGANISATIONS ===")
response = requests.get(f"{BASE_URL}/organizations/", headers=headers)
print(f"Status: {response.status_code}")
organizations = response.json()
print(json.dumps(organizations, indent=2))

# 5. Modifier une organisation
if organizations:
    org_id = organizations[0]['id']
    print(f"\n=== MODIFIER ORGANISATION {org_id} ===")
    update_data = {"name": "Ma Startup Modifiée"}
    response = requests.patch(
        f"{BASE_URL}/organizations/{org_id}/",
        json=update_data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

# 6. Déconnexion
print("\n=== DÉCONNEXION ===")
response = requests.post(f"{BASE_URL}/auth/core/logout/", headers=headers)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

**Exécuter le script :**
```bash
python test_api.py
```

---

## Méthode 3 : Test avec Postman

### Configuration initiale

1. **Installer Postman** : https://www.postman.com/downloads/

2. **Créer une nouvelle collection** : "Loura API"

3. **Configurer une variable d'environnement** :
   - Nom : `base_url`
   - Valeur : `http://localhost:8000/api/core`
   - Nom : `token`
   - Valeur : (sera rempli après login)

### Requêtes à créer

#### 1. Register (POST)
- URL : `{{base_url}}/auth/core/register/`
- Method : POST
- Headers : `Content-Type: application/json`
- Body (raw JSON) :
```json
{
  "email": "postman@loura.com",
  "first_name": "Postman",
  "last_name": "Test",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```
- Tests (pour sauvegarder le token) :
```javascript
if (pm.response.code === 201) {
    const response = pm.response.json();
    pm.environment.set("token", response.token);
}
```

#### 2. Login (POST)
- URL : `{{base_url}}/auth/core/login/`
- Method : POST
- Headers : `Content-Type: application/json`
- Body :
```json
{
  "email": "postman@loura.com",
  "password": "SecurePass123"
}
```
- Tests :
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("token", response.token);
}
```

#### 3. Get Profile (GET)
- URL : `{{base_url}}/auth/me/`
- Method : GET
- Headers : `Authorization: Token {{token}}`

#### 4. Create Organization (POST)
- URL : `{{base_url}}/organizations/`
- Method : POST
- Headers :
  - `Content-Type: application/json`
  - `Authorization: Token {{token}}`
- Body :
```json
{
  "name": "Postman Org",
  "subdomain": "postman-org"
}
```

#### 5. List Organizations (GET)
- URL : `{{base_url}}/organizations/`
- Method : GET
- Headers : `Authorization: Token {{token}}`

---

## Méthode 4 : Test avec HTTPie (Plus simple que cURL)

### Installation
```bash
pip install httpie
```

### Exemples d'utilisation

```bash
# Inscription
http POST http://localhost:8000/api/core/auth/core/register/ \
  email=httpie@loura.com \
  first_name=HTTP \
  last_name=IE \
  password=SecurePass123 \
  password_confirm=SecurePass123

# Connexion
http POST http://localhost:8000/api/core/auth/core/login/ \
  email=httpie@loura.com \
  password=SecurePass123

# Avec le token
TOKEN="votre-token-ici"

# Profil
http GET http://localhost:8000/api/core/auth/me/ \
  "Authorization: Token $TOKEN"

# Créer organisation
http POST http://localhost:8000/api/core/organizations/ \
  "Authorization: Token $TOKEN" \
  name="HTTPie Org" \
  subdomain=httpie-org

# Lister organisations
http GET http://localhost:8000/api/core/organizations/ \
  "Authorization: Token $TOKEN"
```

---

## Méthode 5 : Interface Admin Django

### Créer un superuser

```bash
python manage.py createsuperuser
```

Entrez :
- Email : admin@localhost.com
- Prénom : Admin
- Nom : Super
- Mot de passe : (votre choix)

### Accéder à l'admin

1. Ouvrez `http://localhost:8000/admin/`
2. Connectez-vous avec vos identifiants
3. Vous pouvez gérer :
   - AdminUsers
   - Organizations
   - Categories

---

## Scénario de test complet

### Workflow typique

```bash
# 1. Démarrer le serveur
python manage.py runserver

# 2. Inscription (terminal 2)
TOKEN=$(curl -s -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","first_name":"Test","last_name":"User","password":"Pass1234","password_confirm":"Pass1234"}' \
  | python -m json.tool | grep '"token"' | cut -d'"' -f4)

echo "Token: $TOKEN"

# 3. Créer 3 organisations
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/core/organizations/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d "{\"name\":\"Organisation $i\",\"subdomain\":\"org-$i\"}"
  echo ""
done

# 4. Lister les organisations
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token $TOKEN" | python -m json.tool

# 5. Récupérer le profil
curl -X GET http://localhost:8000/api/core/auth/me/ \
  -H "Authorization: Token $TOKEN" | python -m json.tool
```

---

## Vérification des erreurs courantes

### Erreur 400 - Bad Request
```bash
# Problème : mots de passe ne correspondent pas
curl -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Pass1","password_confirm":"Pass2"}'

# Réponse : {"password":["Les mots de passe ne correspondent pas"]}
```

### Erreur 401 - Unauthorized
```bash
# Problème : token manquant ou invalide
curl -X GET http://localhost:8000/api/core/organizations/

# Solution : ajouter le header Authorization
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token <TOKEN>"
```

### Erreur 404 - Not Found
```bash
# Problème : mauvaise URL
curl -X POST http://localhost:8000/api/core/auth/registers/  # Mauvais

# Solution : vérifier l'URL correcte
curl -X POST http://localhost:8000/api/core/auth/core/register/  # Correct
```

---

## Outils de monitoring

### Voir les logs du serveur
Les requêtes s'affichent dans le terminal où vous avez lancé `runserver` :
```
[17/Nov/2025 17:14:48] "POST /api/core/auth/core/register/ HTTP/1.1" 201 285
[17/Nov/2025 17:14:55] "POST /api/core/auth/core/login/ HTTP/1.1" 200 283
```

### Formater les réponses JSON
```bash
# Avec python
curl http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token $TOKEN" | python -m json.tool

# Avec jq (si installé)
curl http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token $TOKEN" | jq
```

---

## Tests automatisés (Bonus)

Créez `core/tests.py` :

```python
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import AdminUser

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        data = {
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "Pass1234",
            "password_confirm": "Pass1234"
        }
        response = self.client.post('/api/core/auth/core/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_login(self):
        # Créer un user d'abord
        user = AdminUser.objects.create_user(
            email="login@test.com",
            password="Pass1234",
            first_name="Login",
            last_name="Test"
        )

        # Tester le login
        data = {"email": "login@test.com", "password": "Pass1234"}
        response = self.client.post('/api/core/auth/core/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
```

**Lancer les tests :**
```bash
python manage.py test core
```

---

## Résumé des endpoints

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| POST | `/api/core/auth/core/register/` | Non | Inscription |
| POST | `/api/core/auth/core/login/` | Non | Connexion |
| POST | `/api/core/auth/core/logout/` | Oui | Déconnexion |
| GET | `/api/core/auth/me/` | Oui | Profil utilisateur |
| GET | `/api/core/organizations/` | Oui | Liste organisations |
| POST | `/api/core/organizations/` | Oui | Créer organisation |
| GET | `/api/core/organizations/{id}/` | Oui | Détails organisation |
| PATCH | `/api/core/organizations/{id}/` | Oui | Modifier organisation |
| DELETE | `/api/core/organizations/{id}/` | Oui | Supprimer organisation |
| POST | `/api/core/organizations/{id}/activate/` | Oui | Activer organisation |
| POST | `/api/core/organizations/{id}/deactivate/` | Oui | Désactiver organisation |
| GET | `/api/core/categories/` | Oui | Liste catégories |
| GET | `/api/core/categories/{id}/` | Oui | Détails catégorie |

---

## Besoin d'aide ?

- Documentation API complète : `API_DOCUMENTATION.md`
- Architecture du projet : `ARCHITECTURE.md`
- Guide pour Claude Code : `CLAUDE.md`
