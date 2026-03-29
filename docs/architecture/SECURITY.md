# Security - Loura Backend

## Table des matières
1. [Authentification JWT](#authentification-jwt)
2. [Système de permissions](#système-de-permissions)
3. [Multi-tenancy et isolation](#multi-tenancy-et-isolation)
4. [CORS configuration](#cors-configuration)
5. [Variables d'environnement](#variables-denvironnement)
6. [Best practices](#best-practices)
7. [Points d'attention](#points-dattention)

---

## Authentification JWT

### Principe

Loura utilise **JWT (JSON Web Tokens)** avec des **cookies HttpOnly** pour l'authentification.

**Voir** : `app/authentication/views.py` (LoginView, lignes 38-80)

---

### Flow complet

```
1. Login (POST /api/auth/login/)
   ├─ Vérification email/password
   ├─ Génération Access Token (15 min)
   ├─ Génération Refresh Token (7 jours)
   └─ Set cookies HttpOnly

2. Requêtes suivantes
   ├─ Cookie "access_token" envoyé automatiquement
   ├─ JWT Middleware extrait et valide le token
   └─ request.user = User authentifié

3. Refresh (POST /api/auth/refresh/)
   ├─ Cookie "refresh_token"
   ├─ Génération nouveau Access Token
   ├─ Rotation Refresh Token (optionnel)
   └─ Blacklist ancien Refresh Token

4. Logout (POST /api/auth/logout/)
   ├─ Blacklist Refresh Token
   └─ Clear cookies
```

---

### Configuration JWT

```python
# app/lourabackend/settings.py (lignes 341-380)

SIMPLE_JWT = {
    # Durée de vie des tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),   # Court
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Long

    # Rotation et sécurité
    'ROTATE_REFRESH_TOKENS': True,        # Nouveau token à chaque refresh
    'BLACKLIST_AFTER_ROTATION': True,     # Blacklist ancien token
    'UPDATE_LAST_LOGIN': True,

    # Cookies HttpOnly
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'AUTH_COOKIE_HTTP_ONLY': True,        # Pas d'accès JavaScript
    'AUTH_COOKIE_SAMESITE': 'Lax',        # Protection CSRF
    'AUTH_COOKIE_SECURE': False,          # True en production (HTTPS)
    'AUTH_COOKIE_PATH': '/',

    # Algorithme
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

---

### Middleware JWT personnalisé

```python
# app/core/middleware.py

class JWTAuthCookieMiddleware:
    """Extrait le JWT du cookie HttpOnly"""

    def __call__(self, request):
        # 1. Récupérer token du cookie
        access_token = request.COOKIES.get('access_token')

        # 2. Injecter dans Authorization header
        if access_token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

        # 3. Django REST Framework authentifie automatiquement
        return self.get_response(request)
```

**Configuration** : `app/lourabackend/settings.py` (ligne 186)

---

### Authentication backend personnalisé

```python
# app/lourabackend/authentication.py

class MultiUserJWTAuthentication(JWTAuthentication):
    """
    Support BaseUser polymorphe (AdminUser / Employee).
    """

    def get_user(self, validated_token):
        user_id = validated_token['user_id']
        user = BaseUser.objects.get(id=user_id)
        return user.get_concrete_user()  # AdminUser ou Employee
```

**Configuration** : `app/lourabackend/settings.py` (ligne 294)

---

### Blacklist des tokens

La blacklist est gérée par `djangorestframework-simplejwt.token_blacklist` :

```python
# Au logout
from rest_framework_simplejwt.tokens import RefreshToken

token = RefreshToken(refresh_token)
token.blacklist()  # Ajouté à la table de blacklist
```

**Table DB** : `token_blacklist_outstandingtoken`, `token_blacklist_blacklistedtoken`

---

### Sécurité des cookies

| Attribut         | Valeur    | Protection contre         |
|------------------|-----------|---------------------------|
| `HttpOnly`       | `True`    | XSS (pas d'accès JS)      |
| `SameSite`       | `Lax`     | CSRF (requêtes cross-site)|
| `Secure`         | `True`*   | Man-in-the-middle (HTTPS) |
| `Path`           | `/`       | Scope global              |

*En production uniquement (HTTPS)

---

## Système de permissions

### Architecture des permissions

Loura utilise un **système de permissions granulaires** avec :
1. **Permissions Django** (système)
2. **Permissions custom** (modèle `Permission`)
3. **Rôles** (groupement de permissions)

**Voir** : `app/core/models.py` (lignes 155-205)

---

### Classes de permission DRF

#### 1. IsAuthenticated

```python
class IsAuthenticated(BasePermission):
    """Vérifie que l'utilisateur est authentifié."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
```

---

#### 2. IsAdminUser / IsEmployeeUser

```python
class IsAdminUser(BasePermission):
    """Vérifie que l'utilisateur est un AdminUser."""

    def has_permission(self, request, view):
        return getattr(request.user, 'user_type', None) == 'admin'

class IsEmployeeUser(BasePermission):
    """Vérifie que l'utilisateur est un Employee."""

    def has_permission(self, request, view):
        return getattr(request.user, 'user_type', None) == 'employee'
```

---

#### 3. BaseHasPermission

```python
class BaseHasPermission(BasePermission):
    """
    Vérifie une permission spécifique.

    - AdminUser : TOUJOURS autorisé
    - Employee : Vérifie via assigned_role + custom_permissions
    """

    required_permission = 'app.permission_code'

    def has_permission(self, request, view):
        # Admin bypass
        if request.user.user_type == 'admin':
            return True

        # Employee check
        return request.user.has_permission(self.required_permission)
```

**Voir** : `app/core/permissions.py` (lignes 65-106)

---

#### 4. BaseCRUDPermission

```python
class BaseCRUDPermission(BasePermission):
    """
    Permissions CRUD automatiques.

    list/retrieve  → app.view_resource
    create         → app.create_resource
    update         → app.update_resource
    destroy        → app.delete_resource
    """

    permission_prefix = 'app'
    permission_resource = 'resource'

    def has_permission(self, request, view):
        # Admin bypass
        if request.user.user_type == 'admin':
            return True

        # Générer permission_code selon action
        action = view.action
        permission_code = f"{self.permission_prefix}.{action}_{self.permission_resource}"

        return request.user.has_permission(permission_code)
```

**Voir** : `app/core/permissions.py` (lignes 150-228)

---

#### 5. IsOrganizationMember

```python
class IsOrganizationMember(BasePermission):
    """
    Vérifie que l'utilisateur appartient à l'organisation.

    - AdminUser : Admin de l'organisation
    - Employee : Membre de l'organisation
    """

    def has_permission(self, request, view):
        org_id = request.query_params.get('organization')
        org_subdomain = request.headers.get('X-Organization-Subdomain')

        if request.user.user_type == 'admin':
            return request.user.organizations.filter(id=org_id).exists()

        if request.user.user_type == 'employee':
            return str(request.user.organization_id) == str(org_id)

        return False
```

**Voir** : `app/core/permissions.py` (lignes 234-273)

---

### Usage dans les ViewSets

```python
from core.permissions import BaseCRUDPermission

class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [BaseCRUDPermission]
    permission_prefix = 'hr'
    permission_resource = 'employees'

    # Permissions générées automatiquement :
    # - hr.view_employees
    # - hr.create_employees
    # - hr.update_employees
    # - hr.delete_employees
```

---

### Décorateur pour actions custom

```python
from core.permissions import require_permission

class EmployeeViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    @require_permission('hr.activate_employee')
    def activate(self, request, pk=None):
        # Action nécessitant permission spécifique
        pass
```

**Voir** : `app/core/permissions.py` (lignes 280-293)

---

### Vérification de permission (Employee)

```python
class Employee(BaseUser):
    def has_permission(self, permission_code):
        """
        Vérifie via :
        1. Custom permissions (M2M)
        2. Assigned role permissions
        """
        # Custom permissions
        if self.custom_permissions.filter(code=permission_code).exists():
            return True

        # Role permissions
        if self.assigned_role:
            return self.assigned_role.permissions.filter(code=permission_code).exists()

        return False
```

**Voir** : `app/hr/models.py` (lignes 170-231)

---

## Multi-tenancy et isolation

### Principe

Chaque `Organization` est un **tenant isolé**. Les données d'une organisation NE DOIVENT JAMAIS être accessibles depuis une autre.

---

### Isolation au niveau modèle

**Tous les modèles métier ont** :
```python
organization = models.ForeignKey(
    Organization,
    on_delete=models.CASCADE,
    related_name='related_name'
)
```

---

### Isolation au niveau QuerySet

```python
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Filtrer par organisation de l'utilisateur
        if self.request.user.user_type == 'admin':
            # Admin peut voir plusieurs organisations
            org_ids = self.request.user.organizations.values_list('id', flat=True)
            return Employee.objects.filter(organization_id__in=org_ids)

        if self.request.user.user_type == 'employee':
            # Employee ne voit que son organisation
            return Employee.objects.filter(organization=self.request.user.organization)

        return Employee.objects.none()
```

---

### Isolation au niveau permissions

```python
class IsOrganizationMember(BasePermission):
    """Empêche l'accès aux données d'autres organisations."""

    def has_permission(self, request, view):
        org_id = request.query_params.get('organization')

        # Vérifier appartenance
        if request.user.user_type == 'employee':
            return str(request.user.organization_id) == str(org_id)

        return False
```

---

### Bonnes pratiques

✅ **Toujours filtrer par organization dans les QuerySets**
✅ **Utiliser IsOrganizationMember sur les ViewSets sensibles**
✅ **Vérifier organization_id dans les actions custom**
❌ **Ne JAMAIS exposer d'endpoint sans filtre organization**

---

## CORS configuration

### Origins autorisés

```python
# app/lourabackend/settings.py (lignes 306-323)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",         # Next.js dev
    "http://127.0.0.1:3000",
    "https://frontend-loura.vercel.app",  # Production
]

CORS_ALLOW_CREDENTIALS = True  # Pour JWT cookies
```

---

### Headers personnalisés

```python
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'x-csrftoken',
    'x-organization-slug',          # Custom
    'x-organization-subdomain',     # Custom
]
```

---

### CSRF Trusted Origins

```python
CSRF_TRUSTED_ORIGINS = [
    'https://frontend-loura.vercel.app',
    'http://127.0.0.1:3000',
    'http://localhost:3000',
]
```

---

### Développement vs Production

```python
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True  # Développement seulement
else:
    CORS_ALLOW_ALL_ORIGINS = False
    # Utiliser CORS_ALLOWED_ORIGINS strict
```

---

## Variables d'environnement

### Fichier .env

**Localisation** : `/home/salim/Projets/loura/stack/backend/.env`

---

### Variables essentielles

```bash
# Django
SECRET_KEY=your-secret-key-here-min-50-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=loura_db
DB_USER=loura_user
DB_PASSWORD=strong-password-here
DB_HOST=localhost
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db
CHANNEL_LAYERS_BACKEND=channels_redis.core.RedisChannelLayer
CHANNEL_LAYERS_HOST=redis://localhost:6379/2

# JWT Cookies
AUTH_COOKIE_SECURE=True  # HTTPS uniquement en production

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend.com
CSRF_TRUSTED_ORIGINS=https://your-frontend.com

# AI (Optionnel)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
```

---

### Variables sensibles

**⚠️ NE JAMAIS committer** :
- `SECRET_KEY`
- `DB_PASSWORD`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- Toute clé API ou mot de passe

**Utiliser .gitignore** :
```gitignore
.env
.env.local
.env.production
*.pem
*.key
credentials.json
```

---

### Générer SECRET_KEY

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Ou :
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Best practices

### 1. Authentification

✅ **Utiliser JWT avec cookies HttpOnly**
✅ **Access token court (15 min), Refresh token long (7 jours)**
✅ **Blacklist après logout**
✅ **Rotation des refresh tokens**
❌ **Stocker les tokens dans localStorage (XSS)**
❌ **Tokens trop longs (> 1 jour pour access)**

---

### 2. Permissions

✅ **AdminUser bypass toutes les permissions (propriétaire)**
✅ **Employee vérifié via Role + Custom permissions**
✅ **Permissions granulaires par action (view, create, update, delete)**
✅ **Utiliser IsOrganizationMember pour isolation**
❌ **Donner AllowAny sur endpoints sensibles**

---

### 3. Multi-tenancy

✅ **Filtrer TOUS les QuerySets par organization**
✅ **Vérifier organization dans les actions custom**
✅ **Utiliser IsOrganizationMember sur ViewSets**
❌ **Exposer des données cross-organization**

---

### 4. CORS

✅ **Lister explicitement les origins autorisées en production**
✅ **CORS_ALLOW_CREDENTIALS=True pour cookies**
❌ **CORS_ALLOW_ALL_ORIGINS=True en production**

---

### 5. Variables d'environnement

✅ **Utiliser .env pour toutes les variables sensibles**
✅ **SECRET_KEY > 50 caractères aléatoires**
✅ **.env dans .gitignore**
❌ **Hardcoder les secrets dans le code**

---

### 6. HTTPS en production

✅ **AUTH_COOKIE_SECURE=True**
✅ **Certificat SSL/TLS valide**
✅ **Redirection HTTP → HTTPS**
❌ **Utiliser HTTP en production**

---

### 7. Rate limiting (à implémenter)

```python
# Utiliser django-ratelimit ou DRF throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## Points d'attention

### 1. Pas de validation d'email

⚠️ **Actuellement, il n'y a pas de validation d'email après inscription.**

**Risque** : Comptes créés avec emails invalides.

**Solution** :
```python
# Ajouter dans AdminRegistrationSerializer
def validate_email(self, value):
    if User.objects.filter(email=value).exists():
        raise ValidationError("Email déjà utilisé")
    # Ajouter vérification format email
    return value
```

---

### 2. Pas de rate limiting

⚠️ **Pas de limite de requêtes par IP/utilisateur.**

**Risque** : Attaques par force brute sur login, spam API.

**Solution** :
```python
pip install django-ratelimit
# ou utiliser DRF throttling (voir ci-dessus)
```

---

### 3. Pas de 2FA

⚠️ **Pas d'authentification à deux facteurs.**

**Risque** : Accès si mot de passe compromis.

**Solution** : Implémenter TOTP avec `django-otp`.

---

### 4. Pas de logging des accès

⚠️ **Pas de log des tentatives de connexion échouées.**

**Risque** : Difficile de détecter les attaques.

**Solution** :
```python
# Utiliser django-axes pour bloquer après X échecs
pip install django-axes
```

---

### 5. Secrets en clair dans .env

⚠️ **Les secrets sont stockés en clair dans .env.**

**Risque** : Si le serveur est compromis, tous les secrets sont exposés.

**Solution** :
- Utiliser **AWS Secrets Manager** ou **HashiCorp Vault**
- Chiffrer .env avec `ansible-vault`

---

### 6. Pas de CSP headers

⚠️ **Pas de Content Security Policy.**

**Risque** : XSS, injection de scripts.

**Solution** :
```python
# Utiliser django-csp
pip install django-csp

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
]

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
```

---

### 7. Backup et disaster recovery

⚠️ **Pas de stratégie de backup automatique.**

**Risque** : Perte de données en cas de crash.

**Solution** :
- Backups PostgreSQL quotidiens
- Réplication master-slave
- Sauvegardes offsite (S3, Google Cloud Storage)

---

## Checklist sécurité production

Avant de mettre en production :

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` unique et > 50 caractères
- [ ] `ALLOWED_HOSTS` configuré
- [ ] `AUTH_COOKIE_SECURE=True` (HTTPS)
- [ ] CORS origins restreintes
- [ ] CSRF trusted origins configurés
- [ ] PostgreSQL avec mot de passe fort
- [ ] Redis protégé par mot de passe
- [ ] Certificat SSL/TLS valide
- [ ] Firewall configuré (port 8000 fermé, nginx/gunicorn en proxy)
- [ ] Rate limiting activé
- [ ] Logging configuré (sentry, file logs)
- [ ] Backups automatiques configurés
- [ ] Variables d'environnement dans gestionnaire de secrets
- [ ] CSP headers configurés
- [ ] Tests de pénétration effectués

---

## Références

- **OWASP Top 10** : https://owasp.org/www-project-top-ten/
- **Django Security** : https://docs.djangoproject.com/en/5.2/topics/security/
- **JWT Best Practices** : https://datatracker.ietf.org/doc/html/rfc8725
- **CORS Guide** : https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS

---

**Dernière mise à jour** : 2025-01-15
**Version** : 1.0.0
