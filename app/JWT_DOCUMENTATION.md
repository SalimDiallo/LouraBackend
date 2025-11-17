# Documentation JWT - API Loura Backend

## Vue d'ensemble

L'API utilise **JWT (JSON Web Tokens)** avec des **HTTP-only cookies** pour l'authentification. C'est une approche sécurisée qui combine :

- **Access tokens** : Tokens de courte durée (15 minutes) pour l'authentification
- **Refresh tokens** : Tokens de longue durée (7 jours) pour renouveler les access tokens
- **HTTP-only cookies** : Les tokens sont stockés dans des cookies inaccessibles par JavaScript
- **Token blacklist** : Les refresh tokens sont invalidés lors de la déconnexion

## Pourquoi JWT avec HTTP-only cookies ?

### Avantages de sécurité

1. **Protection XSS** : Les cookies HTTP-only ne peuvent pas être lus par JavaScript, protégeant contre les attaques XSS
2. **Tokens auto-destructeurs** : Les access tokens expirent rapidement (15 min)
3. **Rotation des tokens** : Chaque refresh génère un nouveau refresh token
4. **Blacklist** : Les refresh tokens peuvent être révoqués immédiatement
5. **SameSite protection** : Protection contre les attaques CSRF

### Comparaison avec Token simple

| Aspect | Token simple | JWT + HTTP-only cookies |
|--------|--------------|------------------------|
| Stockage | localStorage/sessionStorage | HTTP-only cookies |
| Vulnérabilité XSS | ⚠️ Élevée | ✅ Protégé |
| Expiration | Manuelle | ✅ Automatique |
| Refresh | ❌ Non | ✅ Oui |
| Blacklist | ❌ Non | ✅ Oui |

---

## Configuration JWT

### Settings (lourabackend/settings.py)

```python
SIMPLE_JWT = {
    # Durée de vie des tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),   # Access token court
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),       # Refresh token long

    # Configuration des cookies
    'AUTH_COOKIE': 'access_token',          # Nom du cookie access
    'AUTH_COOKIE_REFRESH': 'refresh_token', # Nom du cookie refresh
    'AUTH_COOKIE_SECURE': False,            # True en production (HTTPS only)
    'AUTH_COOKIE_HTTP_ONLY': True,          # Inaccessible par JavaScript
    'AUTH_COOKIE_SAMESITE': 'Lax',          # Protection CSRF

    # Comportement des tokens
    'ROTATE_REFRESH_TOKENS': True,          # Nouveau refresh à chaque refresh
    'BLACKLIST_AFTER_ROTATION': True,       # Blacklist ancien refresh
    'UPDATE_LAST_LOGIN': True,              # Met à jour last_login

    # Algorithme
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

### Middleware personnalisé

Le middleware `JWTAuthCookieMiddleware` extrait automatiquement le JWT depuis les cookies HTTP-only et l'ajoute au header `Authorization`.

---

## Endpoints d'authentification

### 1. Inscription - `POST /api/core/auth/core/register/`

Crée un nouveau compte et retourne les tokens JWT.

**Request:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T...",
    "organizations_count": 0
  },
  "message": "Inscription reussie",
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci..."
}
```

**Cookies reçus:**
- `access_token` (HttpOnly, Max-Age=900s, SameSite=Lax)
- `refresh_token` (HttpOnly, Max-Age=604800s, SameSite=Lax)

---

### 2. Connexion - `POST /api/core/auth/core/login/`

Authentifie un utilisateur existant.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2025-11-17T...",
    "organizations_count": 1
  },
  "message": "Connexion reussie",
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci..."
}
```

---

### 3. Rafraîchir le token - `POST /api/core/auth/core/refresh/`

Renouvelle l'access token en utilisant le refresh token.

**Request:** Aucun body nécessaire (le refresh token est dans les cookies)

Ou optionnellement:
```json
{
  "refresh": "eyJhbGci..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGci...",
  "refresh": "eyJhbGci...",
  "message": "Token rafraichi avec succes"
}
```

**Note:** Les nouveaux tokens sont automatiquement mis dans les cookies.

---

### 4. Déconnexion - `POST /api/core/auth/core/logout/`

Déconnecte l'utilisateur et blacklist le refresh token.

**Request:** Aucun body nécessaire

**Response (200 OK):**
```json
{
  "message": "Deconnexion reussie"
}
```

**Effet:** Les cookies sont supprimés et le refresh token est blacklisté.

---

### 5. Profil utilisateur - `GET /api/core/auth/me/`

Récupère les informations de l'utilisateur connecté.

**Request:** Aucun body nécessaire (authentifié par cookies)

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "created_at": "2025-11-17T...",
  "organizations_count": 1
}
```

---

## Utilisation avec Next.js / Frontend

### Configuration Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/core',
  withCredentials: true,  // IMPORTANT: Envoie les cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

### Exemple d'utilisation

```javascript
// Inscription
const register = async (userData) => {
  const response = await api.post('/auth/core/register/', userData);
  // Les cookies sont automatiquement stockés par le navigateur
  return response.data;
};

// Connexion
const login = async (credentials) => {
  const response = await api.post('/auth/core/login/', credentials);
  return response.data;
};

// Accès à une ressource protégée
const getOrganizations = async () => {
  // Les cookies sont automatiquement envoyés
  const response = await api.get('/organizations/');
  return response.data;
};

// Rafraîchir le token (appeler avant expiration)
const refreshToken = async () => {
  const response = await api.post('/auth/core/refresh/');
  return response.data;
};

// Déconnexion
const logout = async () => {
  const response = await api.post('/auth/core/logout/');
  return response.data;
};
```

### Intercepteur pour gérer l'expiration

```javascript
// Intercepteur pour rafraîchir automatiquement le token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si erreur 401 et pas déjà tenté de refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Tenter de rafraîchir le token
        await api.post('/auth/core/refresh/');

        // Réessayer la requête originale
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh échoué, rediriger vers login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

## Tests avec cURL

### 1. Inscription
```bash
curl -c cookies.txt -X POST http://localhost:8000/api/core/auth/core/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "Pass1234",
    "password_confirm": "Pass1234"
  }'
```

### 2. Requête authentifiée (avec cookies)
```bash
curl -b cookies.txt http://localhost:8000/api/core/auth/me/
```

### 3. Créer une organisation
```bash
curl -b cookies.txt -X POST http://localhost:8000/api/core/organizations/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Ma Société", "subdomain": "ma-societe"}'
```

### 4. Rafraîchir le token
```bash
curl -b cookies.txt -c cookies.txt -X POST \
  http://localhost:8000/api/core/auth/core/refresh/
```

### 5. Déconnexion
```bash
curl -b cookies.txt -X POST http://localhost:8000/api/core/auth/core/logout/
```

---

## Tests avec Python

Utilisez le script fourni :

```bash
python test_jwt.py
```

Ce script teste :
1. Inscription avec génération de tokens
2. Authentification par cookies
3. Création d'organisation
4. Rafraîchissement de token
5. Déconnexion et blacklist
6. Vérifications de sécurité

---

## Sécurité en production

### Configuration pour la production

Dans `settings.py`, modifiez :

```python
SIMPLE_JWT = {
    'AUTH_COOKIE_SECURE': True,  # HTTPS uniquement
    'AUTH_COOKIE_SAMESITE': 'Strict',  # Plus strict en prod
    # ...
}

# CORS strict
CORS_ALLOWED_ORIGINS = [
    "https://votre-domaine.com",  # Uniquement votre domaine
]
```

### Bonnes pratiques

1. **HTTPS obligatoire** : En production, utilisez HTTPS
2. **Domaines stricts** : Configurez CORS_ALLOWED_ORIGINS avec vos vrais domaines
3. **SECRET_KEY fort** : Utilisez une clé secrète forte et unique
4. **Monitoring** : Surveillez les tentatives de connexion suspectes
5. **Rate limiting** : Limitez les tentatives de connexion

---

## Dépannage

### "Authentication credentials were not provided"

- Vérifiez que `withCredentials: true` est configuré dans votre client HTTP
- Vérifiez que les cookies sont bien envoyés dans la requête

### "Token invalide ou expire"

- Le refresh token a expiré (7 jours) → l'utilisateur doit se reconnecter
- Le token a été blacklisté → l'utilisateur doit se reconnecter

### CORS errors

- Vérifiez `CORS_ALLOWED_ORIGINS` dans settings.py
- Vérifiez `CORS_ALLOW_CREDENTIALS = True`
- Vérifiez que le frontend utilise `withCredentials: true`

### Cookies non reçus

- Vérifiez que le backend et frontend sont sur des domaines compatibles
- En développement local, utilisez `localhost` (pas `127.0.0.1`)
- Vérifiez les paramètres `SameSite` des cookies

---

## Structure des tokens JWT

### Access Token (décodé)

```json
{
  "token_type": "access",
  "exp": 1763402116,      // Expiration (timestamp)
  "iat": 1763401216,      // Émis à (timestamp)
  "jti": "uuid",          // ID unique du token
  "user_id": "uuid"       // ID de l'utilisateur
}
```

### Refresh Token (décodé)

```json
{
  "token_type": "refresh",
  "exp": 1764006016,      // Expiration (timestamp)
  "iat": 1763401216,      // Émis à (timestamp)
  "jti": "uuid",          // ID unique du token
  "user_id": "uuid"       // ID de l'utilisateur
}
```

---

## Résumé des avantages

✅ **Sécurité renforcée** : HTTP-only cookies protègent contre XSS
✅ **Tokens courts** : Access token de 15 min limite l'exposition
✅ **Refresh automatique** : Expérience utilisateur fluide
✅ **Blacklist** : Déconnexion instantanée et sécurisée
✅ **Token rotation** : Nouveau refresh token à chaque refresh
✅ **Compatible mobile** : Fonctionne aussi bien sur web que mobile
✅ **Stateless** : Le serveur ne stocke pas les sessions (scalable)

---

## Migration depuis Token simple

Si vous aviez l'ancien système Token, les changements nécessaires :

1. **Frontend** : Ajoutez `withCredentials: true` à vos requêtes
2. **Frontend** : Les tokens sont maintenant dans les cookies (pas besoin de localStorage)
3. **Frontend** : Implémentez la logique de refresh token
4. **Backend** : Les migrations JWT ont été appliquées automatiquement

Le système retourne toujours les tokens dans la réponse JSON pour compatibilité, mais recommande l'utilisation des cookies.
