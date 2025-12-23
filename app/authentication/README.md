# Authentication App - Documentation

## Vue d'ensemble

L'app `authentication` centralise toute la logique d'authentification pour les utilisateurs admin et employés. Elle fournit des endpoints unifiés pour le login, logout, rafraîchissement de tokens et récupération de l'utilisateur courant.

## Architecture

### Structure des fichiers

```
authentication/
├── __init__.py          # Configuration de l'app
├── apps.py              # Configuration Django
├── middleware.py        # Middleware pour identifier le type d'utilisateur
├── permissions.py       # Permissions personnalisées
├── serializers.py       # Serializers pour login
├── urls.py              # Routes d'API
├── utils.py             # Utilitaires (génération de tokens, etc.)
├── views.py             # Vues d'authentification
└── README.md            # Cette documentation
```

## API Endpoints

### 1. Login Admin
**Endpoint:** `POST /api/auth/admin/login/`

**Permissions:** AllowAny

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "organizations_count": 2
  },
  "message": "Connexion reussie",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errors:**
- `400 Bad Request`: Email ou mot de passe incorrect
- `400 Bad Request`: Compte désactivé

---

### 2. Login Employé
**Endpoint:** `POST /api/auth/employee/login/`

**Permissions:** AllowAny

**Request Body:**
```json
{
  "email": "employee@company.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "employee": {
    "id": "uuid",
    "email": "employee@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "organization": "uuid",
    "organization_subdomain": "company",
    "is_active": true,
    "last_login": "2024-01-01T00:00:00Z"
  },
  "message": "Connexion reussie",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Errors:**
- `400 Bad Request`: Identifiants invalides
- `400 Bad Request`: Organisation désactivée

---

### 3. Logout
**Endpoint:** `POST /api/auth/logout/`

**Permissions:** IsAuthenticated

**Request Body (optionnel):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "message": "Deconnexion reussie"
}
```

**Notes:**
- Le refresh token peut être fourni dans le body ou sera lu depuis les cookies
- Les cookies JWT sont automatiquement supprimés

---

### 4. Rafraîchir le Token
**Endpoint:** `POST /api/auth/refresh/`

**Permissions:** AllowAny

**Request Body (optionnel):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Token rafraichi avec succes"
}
```

**Errors:**
- `400 Bad Request`: Refresh token manquant
- `401 Unauthorized`: Token invalide ou expiré
- `401 Unauthorized`: Compte désactivé
- `404 Not Found`: Utilisateur introuvable

**Notes:**
- Supporte à la fois les tokens admin et employé
- Détecte automatiquement le type d'utilisateur depuis le token
- Le refresh token peut être fourni dans le body ou sera lu depuis les cookies

---

### 5. Utilisateur Courant
**Endpoint:** `GET /api/auth/me/`

**Permissions:** IsAuthenticated

**Response pour Admin (200 OK):**
```json
{
  "user_type": "admin",
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "organizations_count": 2
  }
}
```

**Response pour Employé (200 OK):**
```json
{
  "user_type": "employee",
  "employee": {
    "id": "uuid",
    "email": "employee@company.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "organization": "uuid",
    "organization_subdomain": "company",
    "is_active": true,
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

---

## Utilitaires

### `generate_tokens_for_user(user, user_type='admin')`
Génère des tokens JWT pour un utilisateur.

**Paramètres:**
- `user`: Instance de AdminUser ou Employee
- `user_type`: 'admin' ou 'employee'

**Retour:**
```python
{
    'access': 'token_string',
    'refresh': 'token_string'
}
```

### `get_user_from_token(token_string)`
Extrait les informations utilisateur d'un token JWT.

**Paramètres:**
- `token_string`: Le token JWT

**Retour:**
```python
{
    'user_id': 'uuid',
    'email': 'user@example.com',
    'user_type': 'admin' | 'employee'
}
```

### `convert_uuids_to_strings(data)`
Convertit récursivement les UUID en strings.

**Paramètres:**
- `data`: dict, list, ou autre type

**Retour:**
- data avec les UUID convertis en strings

### `set_jwt_cookies(response, access_token, refresh_token)`
Définit les tokens JWT dans des cookies HTTP-only.

**Paramètres:**
- `response`: Objet Response Django/DRF
- `access_token`: Token d'accès JWT
- `refresh_token`: Token de rafraîchissement JWT

**Usage:**
```python
from authentication.utils import set_jwt_cookies

response = Response({'message': 'Success'})
set_jwt_cookies(response, access_token, refresh_token)
return response
```

### `clear_jwt_cookies(response)`
Supprime les cookies JWT de la réponse.

**Paramètres:**
- `response`: Objet Response Django/DRF

**Usage:**
```python
from authentication.utils import clear_jwt_cookies

response = Response({'message': 'Logged out'})
clear_jwt_cookies(response)
return response
```

---

## Permissions Personnalisées

### `IsAdminUser`
Vérifie que l'utilisateur est un admin.

### `IsEmployee`
Vérifie que l'utilisateur est un employé.

### `IsAdminOrEmployee`
Vérifie que l'utilisateur est soit un admin soit un employé.

### `IsActiveUser`
Vérifie que l'utilisateur est actif.

### `HasValidOrganization`
Vérifie que l'employé a une organisation valide et active.

---

## Gestion des Tokens

### Format des tokens Admin
Les tokens admin utilisent le format standard de `rest_framework_simplejwt`:
```json
{
  "token_type": "access",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "uuid",
  "user_id": 123
}
```

### Format des tokens Employé
Les tokens employé incluent des informations supplémentaires:
```json
{
  "exp": 1234567890,
  "iat": 1234567890,
  "user_id": "uuid",
  "email": "employee@company.com",
  "user_type": "employee",
  "token_type": "refresh"  // ou omis pour access token
}
```

---

## Cookies HTTP-Only

Les tokens sont automatiquement stockés dans des cookies HTTP-only:
- **access_token**: Expire après 15 minutes
- **refresh_token**: Expire après 7 jours

Configuration dans `settings.py`:
```python
SIMPLE_JWT = {
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'AUTH_COOKIE_SECURE': True,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SAMESITE': 'Lax',
    'AUTH_COOKIE_PATH': '/',
}
```

---

## Middleware

### `UserTypeMiddleware`
Ajoute automatiquement le type d'utilisateur (`admin`, `employee`, ou `unknown`) à chaque requête authentifiée via `request.user_type`.

---

## Intégration

### Backend
Les endpoints sont automatiquement disponibles via `/api/auth/`.

### Frontend
Les endpoints frontend ont été mis à jour dans `lib/api/config.ts`:

```typescript
CORE: {
  AUTH: {
    REGISTER: '/core/auth/register/',
    LOGIN: '/auth/admin/login/',
    LOGOUT: '/auth/logout/',
    REFRESH: '/auth/refresh/',
    ME: '/auth/me/',
  }
}

HR: {
  AUTH: {
    LOGIN: '/auth/employee/login/',
    REFRESH: '/auth/refresh/',
    LOGOUT: '/auth/logout/',
    ME: '/auth/me/',
    CHANGE_PASSWORD: '/hr/auth/change-password/',
  }
}
```

---

## Sécurité

### Best Practices
1. Les tokens sont stockés dans des cookies HTTP-only pour prévenir les attaques XSS
2. Les tokens admin utilisent le blacklist de `rest_framework_simplejwt`
3. Les tokens employé sont validés à chaque refresh
4. Les organisations inactives bloquent le login des employés
5. Les comptes désactivés ne peuvent pas se connecter

### Durée de vie des tokens
- **Access token**: 15 minutes
- **Refresh token**: 7 jours

---

## Tests

Pour tester l'API, vous pouvez utiliser curl:

```bash
# Login Admin
curl -X POST http://localhost:8000/api/auth/admin/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Login Employé
curl -X POST http://localhost:8000/api/auth/employee/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "employee@company.com", "password": "password123"}'

# Récupérer l'utilisateur courant
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Rafraîchir le token
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'

# Logout
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
