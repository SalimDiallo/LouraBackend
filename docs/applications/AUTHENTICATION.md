# AUTHENTICATION - Documentation

## Vue d'ensemble

L'application **authentication** gère l'authentification unifiée pour AdminUser et Employee. Elle fournit des endpoints JWT pour la connexion, l'inscription (admin), la déconnexion, le rafraîchissement de token, et la gestion du profil utilisateur. Elle utilise `djangorestframework-simplejwt` pour la gestion des tokens.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/authentication/`
- **Modèles** : 0 (utilise les modèles de `core`)
- **Views** : 6 (LoginView, RegisterAdminView, LogoutView, RefreshTokenView, CurrentUserView, UpdateProfileView, ChangePasswordView)
- **Endpoints** : 7 endpoints
- **Dépendances** :
  - `core` (BaseUser, AdminUser)
  - `hr` (Employee)
  - `djangorestframework-simplejwt`

## Modèles de données

Aucun modèle propre. Utilise :
- `core.models.BaseUser`
- `core.models.AdminUser`
- `hr.models.Employee`

## API Endpoints

### Authentification

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| POST | /api/auth/login/ | Connexion unifiée (Admin + Employee) | AllowAny |
| POST | /api/auth/register/ | Inscription d'un administrateur | AllowAny |
| POST | /api/auth/logout/ | Déconnexion avec blacklist du refresh token | IsAuthenticated |
| POST | /api/auth/refresh/ | Rafraîchir l'access token | AllowAny |
| GET | /api/auth/me/ | Obtenir l'utilisateur connecté | IsAuthenticated |

### Gestion du profil

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| PATCH | /api/auth/profile/update/ | Mettre à jour le profil | IsAuthenticated |
| POST | /api/auth/profile/change-password/ | Changer le mot de passe | IsAuthenticated |

## Exemples de requêtes

### Connexion unifiée

**Request:**
```json
POST /api/auth/login/
{
  "email": "admin@example.com",
  "password": "SecurePassword123"
}
```

**Response (Admin):**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+224622000000",
    "avatar_url": "",
    "user_type": "admin",
    "language": "fr",
    "timezone": "Africa/Conakry",
    "is_active": true,
    "email_verified": false,
    "last_login": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-01T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "organizations": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Ma Boutique",
        "subdomain": "ma-boutique",
        "logo_url": "",
        "is_active": true
      }
    ]
  },
  "user_type": "admin",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Connexion réussie"
}
```

**Response (Employee):**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "email": "employee@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+224623000000",
    "avatar_url": "",
    "user_type": "employee",
    "language": "fr",
    "timezone": "Africa/Conakry",
    "is_active": true,
    "email_verified": false,
    "last_login": "2024-01-15T10:35:00Z",
    "created_at": "2024-01-05T09:00:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "employee_id": "EMP001",
    "organization": {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "name": "Ma Boutique",
      "subdomain": "ma-boutique",
      "logo_url": ""
    },
    "department": {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "Ventes"
    },
    "position": {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "title": "Vendeur"
    },
    "employment_status": "active",
    "permissions": ["hr.view_employees", "inventory.view_products"],
    "date_of_birth": "1990-05-15",
    "address": "123 Rue Principale",
    "city": "Conakry",
    "country": "Guinée",
    "emergency_contact": {
      "name": "John Smith",
      "phone": "+224625000000",
      "relationship": "Frère"
    },
    "contract": "123e4567-e89b-12d3-a456-426614174005",
    "hire_date": "2024-01-05",
    "termination_date": null,
    "manager": "123e4567-e89b-12d3-a456-426614174000"
  },
  "user_type": "employee",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Connexion réussie"
}
```

### Inscription d'un administrateur

**Request:**
```json
POST /api/auth/register/
{
  "email": "newadmin@example.com",
  "password": "SecurePassword123",
  "first_name": "Alice",
  "last_name": "Johnson",
  "phone": "+224624000000"
}
```

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174006",
    "email": "newadmin@example.com",
    "first_name": "Alice",
    "last_name": "Johnson",
    "phone": "+224624000000",
    "avatar_url": "",
    "user_type": "admin",
    "language": "fr",
    "timezone": "Africa/Conakry",
    "is_active": true,
    "email_verified": false,
    "last_login": null,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "organizations": []
  },
  "user_type": "admin",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Inscription réussie"
}
```

### Déconnexion

**Request:**
```json
POST /api/auth/logout/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "message": "Déconnexion réussie"
}
```

### Rafraîchissement du token

**Request:**
```json
POST /api/auth/refresh/
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Token rafraîchi"
}
```

### Obtenir l'utilisateur connecté

**Request:**
```json
GET /api/auth/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "email": "employee@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+224623000000",
  "avatar_url": "",
  "user_type": "employee",
  "language": "fr",
  "timezone": "Africa/Conakry",
  "is_active": true,
  "email_verified": false,
  "last_login": "2024-01-15T10:35:00Z",
  "created_at": "2024-01-05T09:00:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "employee_id": "EMP001",
  "organization": {
    "id": "123e4567-e89b-12d3-a456-426614174001",
    "name": "Ma Boutique",
    "subdomain": "ma-boutique",
    "logo_url": ""
  },
  "department": {
    "id": "123e4567-e89b-12d3-a456-426614174003",
    "name": "Ventes"
  },
  "position": {
    "id": "123e4567-e89b-12d3-a456-426614174004",
    "title": "Vendeur"
  },
  "employment_status": "active",
  "permissions": ["hr.view_employees", "inventory.view_products"]
}
```

### Mettre à jour le profil

**Request:**
```json
PATCH /api/auth/profile/update/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
{
  "first_name": "Jane Updated",
  "phone": "+224623111111",
  "address": "456 New Street",
  "city": "Conakry",
  "language": "en"
}
```

**Response:**
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "email": "employee@example.com",
    "first_name": "Jane Updated",
    "last_name": "Smith",
    "phone": "+224623111111",
    "address": "456 New Street",
    "city": "Conakry",
    "language": "en"
  },
  "message": "Profil mis à jour"
}
```

### Changer le mot de passe

**Request:**
```json
POST /api/auth/profile/change-password/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
{
  "old_password": "OldPassword123",
  "new_password": "NewSecurePassword456",
  "confirm_password": "NewSecurePassword456"
}
```

**Response:**
```json
{
  "message": "Mot de passe modifié avec succès"
}
```

## Serializers

- **UnifiedLoginSerializer** : Connexion unifiée AdminUser/Employee avec validation des credentials
- **AdminRegistrationSerializer** : Inscription d'un administrateur
- **UserResponseSerializer** : Réponse de base pour tout utilisateur
- **AdminUserResponseSerializer** : Réponse spécifique Admin (inclut organizations)
- **EmployeeUserResponseSerializer** : Réponse spécifique Employee (inclut organization, department, position, permissions)

## Permissions

- **AllowAny** : Login, Register, Refresh
- **IsAuthenticated** : Logout, Me, Profile Update, Change Password

## Services/Utilities

### authentication/utils.py

Fonctions utilitaires pour la gestion des tokens :

- **generate_tokens_for_user(user, user_type)** : Génère access et refresh tokens avec custom claims (user_type, organization_id)
- **convert_uuids_to_strings(data)** : Convertit récursivement les UUIDs en strings dans les dictionnaires
- **get_user_from_token(token)** : Extrait les informations utilisateur d'un token JWT
- **set_jwt_cookies(response, access, refresh)** : Configure les cookies JWT dans la réponse HTTP
- **clear_jwt_cookies(response)** : Supprime les cookies JWT de la réponse HTTP

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Connexion unifiée** : Un seul endpoint pour AdminUser et Employee
2. **Inscription Admin** : Création automatique d'un AdminUser (organisation créée séparément)
3. **Gestion de session JWT** : Tokens access/refresh avec blacklist sur logout
4. **Profil utilisateur** : Mise à jour des informations personnelles
5. **Sécurité** : Changement de mot de passe avec validation de l'ancien

### Flow d'authentification

```
1. User submits email + password to /api/auth/login/
2. Backend validates credentials
3. Backend determines user_type (admin or employee)
4. Backend generates JWT tokens with custom claims
5. Backend returns user data + tokens
6. Frontend stores tokens (localStorage or cookies)
7. Frontend includes access token in Authorization header for subsequent requests
8. When access token expires, frontend uses refresh token at /api/auth/refresh/
9. On logout, refresh token is blacklisted at /api/auth/logout/
```

## Points d'attention

### Cookies JWT
- Les tokens JWT sont également configurés en cookies HTTP-only pour sécurité accrue
- Les cookies sont nommés selon `settings.SIMPLE_JWT['AUTH_COOKIE']` et `AUTH_COOKIE_REFRESH`
- En production, utiliser `Secure` et `SameSite` appropriés

### Custom Claims JWT
- Les tokens incluent des claims personnalisés : `user_type`, `organization_id`
- Ces claims permettent d'identifier rapidement le type d'utilisateur et son organisation
- Utiliser `get_user_from_token()` pour extraire ces informations

### Blacklist des tokens
- Le module `rest_framework_simplejwt.token_blacklist` gère la blacklist
- À la déconnexion, le refresh token est ajouté à la blacklist
- Les tokens blacklistés ne peuvent plus être utilisés pour générer de nouveaux access tokens

### Validation du mot de passe
- Longueur minimale : 8 caractères
- Validation Django : `django.contrib.auth.password_validation.validate_password`
- Lors du changement de mot de passe, l'ancien mot de passe doit être vérifié

### Organisation inactive
- Si un Employee tente de se connecter avec une organisation désactivée (`is_active=False`), la connexion est refusée
- Les AdminUser peuvent se connecter même si leurs organisations sont désactivées

### Conversion UUID vers String
- Les UUIDs sont automatiquement convertis en strings dans les réponses JSON via `convert_uuids_to_strings()`
- Nécessaire pour la compatibilité JavaScript/JSON

### Mise à jour du profil
- Champs modifiables pour tous : `first_name`, `last_name`, `phone`, `avatar_url`, `language`, `timezone`
- Champs supplémentaires pour Employee : `date_of_birth`, `address`, `city`, `country`, `emergency_contact`
- Le champ `email` n'est pas modifiable (identifiant unique)
