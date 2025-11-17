# API de Gestion des Organisations

Ce document décrit comment utiliser l'API pour gérer les organisations dans le module `core`.

## 🔐 Authentification

Tous les endpoints nécessitent une authentification JWT. Vous devez d'abord vous inscrire ou vous connecter pour obtenir un token.

### 1. Inscription d'un AdminUser

```bash
POST /api/core/auth/register/
```

**Body (JSON):**
```json
{
  "email": "admin@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "motdepasse123",
  "password_confirm": "motdepasse123"
}
```

**Réponse:**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T10:00:00Z",
    "organizations_count": 0
  },
  "message": "Inscription reussie",
  "access": "eyJ0eXAiOiJKV1...",
  "refresh": "eyJ0eXAiOiJKV1..."
}
```

### 2. Connexion

```bash
POST /api/core/auth/login/
```

**Body (JSON):**
```json
{
  "email": "admin@example.com",
  "password": "motdepasse123"
}
```

---

## 📂 Gestion des Catégories

### Lister toutes les catégories

```bash
GET /api/core/categories/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Réponse:**
```json
[
  {
    "id": 1,
    "name": "Technologie",
    "description": "Entreprises du secteur technologique et informatique"
  },
  {
    "id": 2,
    "name": "Santé",
    "description": "Établissements de santé, cliniques, hôpitaux"
  },
  ...
]
```

### Détails d'une catégorie

```bash
GET /api/core/categories/{id}/
```

---

## 🏢 Gestion des Organisations

### 1. Créer une organisation

```bash
POST /api/core/organizations/
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "name": "Ma Première Entreprise",
  "subdomain": "premiere-entreprise",
  "logo_url": "https://example.com/logo.png",
  "category": 1,
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "theme": "dark",
    "contact_email": "contact@premiere-entreprise.com"
  }
}
```

**Champs obligatoires:**
- `name`: Nom de l'organisation
- `subdomain`: Sous-domaine unique (lettres, chiffres, tirets uniquement)

**Champs optionnels:**
- `logo_url`: URL du logo
- `category`: ID de la catégorie
- `settings`: Paramètres de l'organisation (tous optionnels)

**Réponse:**
```json
{
  "id": "uuid",
  "name": "Ma Première Entreprise",
  "subdomain": "premiere-entreprise",
  "logo_url": "https://example.com/logo.png",
  "category": 1,
  "category_details": {
    "id": 1,
    "name": "Technologie",
    "description": "Entreprises du secteur technologique et informatique"
  },
  "admin": "uuid-admin",
  "admin_email": "admin@example.com",
  "is_active": true,
  "created_at": "2025-11-17T10:00:00Z",
  "updated_at": "2025-11-17T10:00:00Z",
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "theme": "dark",
    "contact_email": "contact@premiere-entreprise.com"
  }
}
```

### 2. Lister toutes mes organisations

```bash
GET /api/core/organizations/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Note:** Retourne uniquement les organisations créées par l'utilisateur connecté.

**Réponse:**
```json
[
  {
    "id": "uuid",
    "name": "Ma Première Entreprise",
    "subdomain": "premiere-entreprise",
    "logo_url": "https://example.com/logo.png",
    "category": 1,
    "category_details": {
      "id": 1,
      "name": "Technologie",
      "description": "..."
    },
    "admin": "uuid-admin",
    "admin_email": "admin@example.com",
    "is_active": true,
    "created_at": "2025-11-17T10:00:00Z",
    "updated_at": "2025-11-17T10:00:00Z",
    "settings": {...}
  },
  ...
]
```

### 3. Afficher les détails d'une organisation

```bash
GET /api/core/organizations/{id}/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

### 4. Modifier une organisation

```bash
PUT /api/core/organizations/{id}/
```

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body (JSON) - Modification complète:**
```json
{
  "name": "Entreprise Modifiée",
  "subdomain": "entreprise-modifiee",
  "logo_url": "https://example.com/new-logo.png",
  "category": 2,
  "is_active": true
}
```

**OU**

```bash
PATCH /api/core/organizations/{id}/
```

**Body (JSON) - Modification partielle:**
```json
{
  "name": "Nouveau Nom"
}
```

### 5. Supprimer une organisation

```bash
DELETE /api/core/organizations/{id}/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Réponse:** 204 No Content

### 6. Activer une organisation

```bash
POST /api/core/organizations/{id}/activate/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

**Réponse:**
```json
{
  "message": "Organisation \"Ma Première Entreprise\" activee",
  "organization": {...}
}
```

### 7. Désactiver une organisation

```bash
POST /api/core/organizations/{id}/deactivate/
```

**Headers:**
```
Authorization: Bearer {access_token}
```

---

## 📋 Exemples avec cURL

### Créer une organisation

```bash
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions",
    "subdomain": "tech-solutions",
    "category": 1,
    "settings": {
      "country": "GN",
      "currency": "GNF"
    }
  }'
```

### Modifier une organisation

```bash
curl -X PATCH http://localhost:8000/api/core/organizations/{id}/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions Pro",
    "category": 2
  }'
```

### Lister les organisations

```bash
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1..."
```

---

## 📋 Exemples avec Python (requests)

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api/core"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1..."
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Lister les catégories
response = requests.get(f"{BASE_URL}/categories/", headers=headers)
categories = response.json()
print("Catégories:", categories)

# 2. Créer une organisation
organization_data = {
    "name": "Ma Super Entreprise",
    "subdomain": "super-entreprise",
    "category": 1,
    "settings": {
        "country": "GN",
        "currency": "GNF",
        "contact_email": "contact@super-entreprise.com"
    }
}
response = requests.post(
    f"{BASE_URL}/organizations/",
    json=organization_data,
    headers=headers
)
new_org = response.json()
print("Organisation créée:", new_org)

# 3. Lister mes organisations
response = requests.get(f"{BASE_URL}/organizations/", headers=headers)
organizations = response.json()
print("Mes organisations:", organizations)

# 4. Modifier une organisation
org_id = new_org["id"]
update_data = {
    "name": "Ma Super Entreprise - Mise à jour",
    "category": 2
}
response = requests.patch(
    f"{BASE_URL}/organizations/{org_id}/",
    json=update_data,
    headers=headers
)
updated_org = response.json()
print("Organisation modifiée:", updated_org)

# 5. Désactiver une organisation
response = requests.post(
    f"{BASE_URL}/organizations/{org_id}/deactivate/",
    headers=headers
)
result = response.json()
print("Organisation désactivée:", result)
```

---

## ⚠️ Codes d'erreur

- **400 Bad Request**: Données invalides
- **401 Unauthorized**: Token manquant ou invalide
- **403 Forbidden**: Vous n'avez pas les permissions nécessaires
- **404 Not Found**: Organisation non trouvée
- **409 Conflict**: Subdomain déjà utilisé

---

## 🎯 Catégories disponibles

Les catégories suivantes sont disponibles par défaut :

1. **Technologie** - Entreprises du secteur technologique et informatique
2. **Santé** - Établissements de santé, cliniques, hôpitaux
3. **Éducation** - Écoles, universités, centres de formation
4. **Commerce** - Commerces de détail et distribution
5. **Services** - Entreprises de services professionnels
6. **Finance** - Banques, assurances, institutions financières
7. **Industrie** - Entreprises industrielles et manufacturières
8. **Restauration** - Restaurants, hôtels, services de restauration

Pour créer de nouvelles catégories, vous pouvez utiliser l'admin Django ou créer un script de gestion.
