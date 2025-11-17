# API Documentation - Loura Backend

## Base URL
```
http://localhost:8000/api/core/
```

## Authentication

L'API utilise l'authentification par token. Après inscription ou connexion, vous recevez un token à inclure dans toutes les requêtes authentifiées.

**Header d'authentification :**
```
Authorization: Token <votre_token>
```

---

## Endpoints d'authentification

### 1. Inscription (Register)

Créer un nouveau compte AdminUser.

**Endpoint :** `POST /api/core/auth/core/register/`

**Permissions :** Aucune (public)

**Corps de la requête :**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**Réponse (201 Created) :**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T17:14:48.618835Z",
    "organizations_count": 0
  },
  "token": "e65f29ad8b9b4b0293ca25282d707b982265605a",
  "message": "Inscription réussie"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
  }'
```

---

### 2. Connexion (Login)

Se connecter avec un compte existant.

**Endpoint :** `POST /api/core/auth/core/login/`

**Permissions :** Aucune (public)

**Corps de la requête :**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Réponse (200 OK) :**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T17:14:48.618835Z",
    "organizations_count": 1
  },
  "token": "e65f29ad8b9b4b0293ca25282d707b982265605a",
  "message": "Connexion réussie"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/auth/core/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123"}'
```

---

### 3. Déconnexion (Logout)

Se déconnecter (supprime le token).

**Endpoint :** `POST /api/core/auth/core/logout/`

**Permissions :** Authentification requise

**Corps de la requête :** Aucun

**Réponse (200 OK) :**
```json
{
  "message": "Déconnexion réussie"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/auth/core/logout/ \
  -H "Authorization: Token <votre_token>"
```

---

### 4. Utilisateur actuel (Me)

Obtenir les informations de l'utilisateur connecté.

**Endpoint :** `GET /api/core/auth/me/`

**Permissions :** Authentification requise

**Réponse (200 OK) :**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-11-17T17:14:48.618835Z",
  "organizations_count": 1
}
```

**Exemple cURL :**
```bash
curl -X GET http://localhost:8000/api/core/auth/me/ \
  -H "Authorization: Token <votre_token>"
```

---

## Endpoints des organisations

### 5. Lister mes organisations

Récupérer toutes les organisations de l'utilisateur connecté.

**Endpoint :** `GET /api/core/organizations/`

**Permissions :** Authentification requise

**Réponse (200 OK) :**
```json
[
  {
    "id": "uuid",
    "name": "Mon Entreprise",
    "subdomain": "mon-entreprise",
    "logo_url": null,
    "category": null,
    "category_details": null,
    "admin": "admin_uuid",
    "admin_email": "user@example.com",
    "is_active": true,
    "created_at": "2025-11-17T17:14:59.999558Z",
    "updated_at": "2025-11-17T17:14:59.999588Z",
    "settings": {
      "country": null,
      "currency": "MAD",
      "theme": null,
      "contact_email": null
    }
  }
]
```

**Exemple cURL :**
```bash
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token <votre_token>"
```

---

### 6. Créer une organisation

Créer une nouvelle organisation.

**Endpoint :** `POST /api/core/organizations/`

**Permissions :** Authentification requise

**Corps de la requête :**
```json
{
  "name": "Mon Entreprise",
  "subdomain": "mon-entreprise",
  "logo_url": "https://example.com/logo.png",
  "category": 1,
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "theme": "dark",
    "contact_email": "contact@example.com"
  }
}
```

**Champs requis :**
- `name` : Nom de l'organisation
- `subdomain` : Sous-domaine unique (lettres, chiffres et tirets uniquement)

**Champs optionnels :**
- `logo_url` : URL du logo
- `category` : ID de la catégorie
- `settings` : Configuration de l'organisation

**Réponse (201 Created) :**
```json
{
  "name": "Mon Entreprise",
  "subdomain": "mon-entreprise",
  "logo_url": "https://example.com/logo.png",
  "category": 1,
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "theme": "dark",
    "contact_email": "contact@example.com"
  }
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <votre_token>" \
  -d '{
    "name": "Mon Entreprise",
    "subdomain": "mon-entreprise"
  }'
```

---

### 7. Détails d'une organisation

Récupérer les détails d'une organisation spécifique.

**Endpoint :** `GET /api/core/organizations/{id}/`

**Permissions :** Authentification requise (propriétaire uniquement)

**Exemple cURL :**
```bash
curl -X GET http://localhost:8000/api/core/organizations/{id}/ \
  -H "Authorization: Token <votre_token>"
```

---

### 8. Mettre à jour une organisation

Modifier une organisation existante.

**Endpoint :** `PUT /api/core/organizations/{id}/` (mise à jour complète)
**Endpoint :** `PATCH /api/core/organizations/{id}/` (mise à jour partielle)

**Permissions :** Authentification requise (propriétaire uniquement)

**Corps de la requête (PATCH - exemple) :**
```json
{
  "name": "Nouveau Nom",
  "logo_url": "https://example.com/new-logo.png"
}
```

**Exemple cURL :**
```bash
curl -X PATCH http://localhost:8000/api/core/organizations/{id}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <votre_token>" \
  -d '{"name": "Nouveau Nom"}'
```

---

### 9. Supprimer une organisation

Supprimer une organisation.

**Endpoint :** `DELETE /api/core/organizations/{id}/`

**Permissions :** Authentification requise (propriétaire uniquement)

**Réponse (204 No Content)**

**Exemple cURL :**
```bash
curl -X DELETE http://localhost:8000/api/core/organizations/{id}/ \
  -H "Authorization: Token <votre_token>"
```

---

### 10. Activer une organisation

Activer une organisation désactivée.

**Endpoint :** `POST /api/core/organizations/{id}/activate/`

**Permissions :** Authentification requise (propriétaire uniquement)

**Réponse (200 OK) :**
```json
{
  "message": "Organisation \"Mon Entreprise\" activée"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/organizations/{id}/activate/ \
  -H "Authorization: Token <votre_token>"
```

---

### 11. Désactiver une organisation

Désactiver une organisation.

**Endpoint :** `POST /api/core/organizations/{id}/deactivate/`

**Permissions :** Authentification requise (propriétaire uniquement)

**Réponse (200 OK) :**
```json
{
  "message": "Organisation \"Mon Entreprise\" désactivée"
}
```

**Exemple cURL :**
```bash
curl -X POST http://localhost:8000/api/core/organizations/{id}/deactivate/ \
  -H "Authorization: Token <votre_token>"
```

---

## Endpoints des catégories

### 12. Lister les catégories

Récupérer toutes les catégories disponibles.

**Endpoint :** `GET /api/core/categories/`

**Permissions :** Authentification requise

**Réponse (200 OK) :**
```json
[
  {
    "id": 1,
    "name": "E-commerce",
    "description": "Boutiques en ligne"
  },
  {
    "id": 2,
    "name": "Services",
    "description": "Entreprises de services"
  }
]
```

**Exemple cURL :**
```bash
curl -X GET http://localhost:8000/api/core/categories/ \
  -H "Authorization: Token <votre_token>"
```

---

### 13. Détails d'une catégorie

Récupérer les détails d'une catégorie spécifique.

**Endpoint :** `GET /api/core/categories/{id}/`

**Permissions :** Authentification requise

**Exemple cURL :**
```bash
curl -X GET http://localhost:8000/api/core/categories/{id}/ \
  -H "Authorization: Token <votre_token>"
```

---

## Codes d'erreur courants

| Code | Description |
|------|-------------|
| 200  | Succès |
| 201  | Créé avec succès |
| 204  | Succès sans contenu (suppression) |
| 400  | Requête invalide (erreurs de validation) |
| 401  | Non authentifié (token manquant ou invalide) |
| 403  | Interdit (pas les permissions nécessaires) |
| 404  | Ressource non trouvée |
| 500  | Erreur serveur interne |

---

## Workflow typique

### 1. Inscription d'un nouvel utilisateur
```bash
# 1. Créer un compte
curl -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","first_name":"John","last_name":"Doe","password":"SecurePass123","password_confirm":"SecurePass123"}'
```

### 2. Connexion
```bash
# 2. Se connecter (récupère le token)
curl -X POST http://localhost:8000/api/core/auth/core/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}'
```

### 3. Créer une organisation
```bash
# 3. Créer une organisation (avec le token)
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <votre_token>" \
  -d '{"name":"Mon Entreprise","subdomain":"mon-entreprise"}'
```

### 4. Gérer les organisations
```bash
# 4. Lister mes organisations
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Token <votre_token>"

# 5. Obtenir mes informations utilisateur
curl -X GET http://localhost:8000/api/core/auth/me/ \
  -H "Authorization: Token <votre_token>"
```

---

## Notes importantes

1. **Tous les mots de passe doivent avoir au moins 8 caractères**
2. **Les subdomains doivent être uniques** et ne contenir que des lettres, chiffres et tirets
3. **Le token doit être conservé côté client** (localStorage ou sessionStorage)
4. **Un utilisateur ne peut voir que ses propres organisations**
5. **La devise par défaut est MAD** (peut être modifiée via les settings de l'organisation)

---

## Interface d'administration Django

Vous pouvez également gérer les utilisateurs et organisations via l'interface admin Django :

**URL :** http://localhost:8000/admin/

Pour créer un superuser :
```bash
python manage.py createsuperuser
```
