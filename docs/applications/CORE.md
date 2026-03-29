# CORE - Documentation

## Vue d'ensemble

L'application **core** est le module central du système Loura. Elle gère l'authentification de base, les utilisateurs (AdminUser et Employee via BaseUser), les organisations multi-tenant, les permissions et rôles personnalisés, ainsi que les catégories d'organisation et la gestion des modules activés par organisation.

## Architecture

- **Emplacement** : `/home/salim/Projets/loura/stack/backend/app/core/`
- **Modèles** : 9 (BaseUser, AdminUser, Organization, OrganizationSettings, Category, Permission, Role, Module, OrganizationModule)
- **ViewSets** : 4 (OrganizationViewSet, CategoryViewSet, ModuleViewSet, OrganizationModuleViewSet)
- **Endpoints** : ~25 endpoints
- **Dépendances** : Aucune (module racine)

## Modèles de données

### BaseUser

**Description** : Modèle utilisateur parent abstrait dont héritent AdminUser et Employee (via multi-table inheritance). Permet l'utilisation de ForeignKey(BaseUser) pour référencer les deux types d'utilisateurs.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `email` (EmailField, unique) : Email de connexion
- `first_name` (CharField) : Prénom
- `last_name` (CharField) : Nom
- `phone` (CharField) : Téléphone
- `avatar_url` (URLField) : URL de l'avatar
- `user_type` (CharField) : Type d'utilisateur ('admin' ou 'employee')
- `language` (CharField) : Langue de l'interface (défaut: 'fr')
- `timezone` (CharField) : Fuseau horaire (défaut: 'Africa/Conakry')
- `is_active` (BooleanField) : Compte actif
- `is_staff` (BooleanField) : Accès admin Django
- `email_verified` (BooleanField) : Email vérifié
- `last_login` (DateTimeField) : Dernière connexion
- `password` (CharField) : Hash du mot de passe

**Relations** :
- ManyToMany avec `Group` (Django)
- ManyToMany avec `DjangoPermission` (Django)

**Méthodes importantes** :
- `get_full_name()` : Retourne prénom + nom
- `get_short_name()` : Retourne le prénom ou début de l'email
- `is_admin_user` (property) : Vérifie si admin
- `is_employee_user` (property) : Vérifie si employé
- `get_concrete_user()` : Retourne l'objet AdminUser ou Employee selon le type
- `has_org_permission(permission_code)` : Vérifie les permissions organisationnelles
- `get_organization()` : Retourne l'organisation de l'utilisateur

### AdminUser

**Description** : Administrateur d'une ou plusieurs organisations. Hérite de BaseUser. Possède tous les droits sur ses organisations.

**Champs principaux** :
- Hérite de tous les champs de BaseUser
- `user_type` : Toujours 'admin'

**Relations** :
- OneToMany avec `Organization` via `admin` (un admin peut avoir plusieurs organisations)

**Méthodes importantes** :
- `get_organizations_for_admin()` : Retourne toutes les organisations de l'admin
- `has_permission(permission_code)` : Retourne toujours `True` (admin a tous les droits)

### Organization

**Description** : Organisation multi-tenant. Chaque organisation est isolée des autres. Point central de l'architecture multi-tenant.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `name` (CharField) : Nom de l'organisation
- `subdomain` (SlugField, unique) : Sous-domaine unique
- `logo_url` (URLField) : URL du logo
- `logo` (ImageField) : Fichier logo uploadé
- `category` (ForeignKey) : Catégorie de l'organisation
- `admin` (ForeignKey to AdminUser) : Propriétaire/administrateur
- `is_active` (BooleanField) : Organisation active

**Relations** :
- ForeignKey vers `Category` (catégorie d'organisation)
- ForeignKey vers `AdminUser` (propriétaire)
- OneToOne avec `OrganizationSettings` (paramètres)
- OneToMany avec `Module` via `OrganizationModule` (modules activés)

**Méthodes importantes** :
- `settings` (property) : Retourne ou crée les paramètres de l'organisation

### OrganizationSettings

**Description** : Paramètres de configuration d'une organisation.

**Champs principaux** :
- `organization` (OneToOneField) : Organisation liée
- `country` (CharField) : Pays
- `currency` (CharField) : Devise (défaut: 'MAD')
- `theme` (CharField) : Thème de l'interface
- `contact_email` (EmailField) : Email de contact

**Relations** :
- OneToOne avec `Organization`

### Category

**Description** : Catégorie d'organisation (ex: Restaurant, Commerce, BTP). Permet de pré-configurer les modules par défaut.

**Champs principaux** :
- `id` (AutoField) : Identifiant unique
- `name` (CharField, unique) : Nom de la catégorie
- `description` (TextField) : Description

**Relations** :
- OneToMany avec `Organization` (organisations de cette catégorie)

### Permission

**Description** : Permission granulaire personnalisée pour le système de permissions. Indépendant des permissions Django.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `code` (CharField, unique) : Code unique (ex: 'hr.view_employees')
- `name` (CharField) : Nom d'affichage
- `category` (CharField) : Catégorie de la permission
- `description` (TextField) : Description

**Relations** :
- ManyToMany avec `Role` (permissions associées à des rôles)
- ManyToMany avec `Employee` via `custom_permissions`

**Méthodes importantes** :
- Utilise le système de catégories pour organiser les permissions par module

### Role

**Description** : Rôle regroupant des permissions. Peut être système (global) ou spécifique à une organisation.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `organization` (ForeignKey, nullable) : Organisation (null = rôle système)
- `code` (CharField) : Code unique dans l'organisation
- `name` (CharField) : Nom du rôle
- `description` (TextField) : Description
- `permissions` (ManyToMany) : Permissions du rôle
- `is_system_role` (BooleanField) : Rôle système global
- `is_active` (BooleanField) : Rôle actif

**Relations** :
- ForeignKey vers `Organization` (nullable pour rôles système)
- ManyToMany avec `Permission`

**Méthodes importantes** :
- `get_all_permissions()` : Retourne la liste des codes de permissions

### Module

**Description** : Module de l'application (fonctionnalité activable/désactivable par organisation). Ex: hr.employees, hr.payroll, inventory.products.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `code` (CharField, unique) : Code unique du module
- `name` (CharField) : Nom d'affichage
- `description` (TextField) : Description
- `app_name` (CharField) : Nom de l'app Django associée
- `icon` (CharField) : Icône pour l'UI
- `category` (CharField) : Catégorie du module
- `default_for_all` (BooleanField) : Activé par défaut pour toutes les orgs
- `default_categories` (JSONField) : Liste des catégories pour lesquelles ce module est activé par défaut
- `requires_subscription_tier` (CharField) : Niveau d'abonnement requis
- `depends_on` (JSONField) : Liste des codes de modules requis
- `is_core` (BooleanField) : Module core (ne peut pas être désactivé)
- `is_active` (BooleanField) : Module actif et disponible
- `order` (IntegerField) : Ordre d'affichage

**Relations** :
- ManyToMany avec `Organization` via `OrganizationModule`

**Méthodes importantes** :
- `is_default_for_category(category_name)` : Vérifie si activé par défaut pour une catégorie
- `get_dependencies()` : Retourne les modules dont celui-ci dépend

### OrganizationModule

**Description** : Table de liaison entre Organization et Module. Gère l'activation des modules par organisation.

**Champs principaux** :
- `id` (UUID) : Identifiant unique
- `organization` (ForeignKey) : Organisation
- `module` (ForeignKey) : Module
- `is_enabled` (BooleanField) : Module activé
- `settings` (JSONField) : Paramètres spécifiques du module pour cette org
- `enabled_at` (DateTimeField) : Date d'activation
- `enabled_by` (ForeignKey to BaseUser) : Utilisateur ayant activé

**Relations** :
- ForeignKey vers `Organization`
- ForeignKey vers `Module`
- ForeignKey vers `BaseUser` (qui a activé)

## API Endpoints

### OrganizationViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/core/organizations/ | Liste des organisations accessibles | IsAuthenticated |
| POST | /api/core/organizations/ | Créer une organisation | IsAuthenticated |
| GET | /api/core/organizations/{id}/ | Détails d'une organisation | IsAuthenticated |
| PUT/PATCH | /api/core/organizations/{id}/ | Modifier une organisation | IsAuthenticated |
| DELETE | /api/core/organizations/{id}/ | Supprimer une organisation | IsAuthenticated |
| POST | /api/core/organizations/{id}/activate/ | Activer une organisation | IsAuthenticated |
| POST | /api/core/organizations/{id}/deactivate/ | Désactiver une organisation | IsAuthenticated |
| POST/DELETE | /api/core/organizations/{id}/logo/ | Upload/supprimer logo | IsAuthenticated |

### CategoryViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/core/categories/ | Liste des catégories | Public |
| GET | /api/core/categories/{id}/ | Détails d'une catégorie | Public |

### ModuleViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/core/modules/ | Liste des modules actifs | IsAuthenticated |
| GET | /api/core/modules/{id}/ | Détails d'un module | IsAuthenticated |
| GET | /api/core/modules/defaults/ | Modules par défaut pour une catégorie | IsAuthenticated |
| GET | /api/core/modules/by_category/ | Modules groupés par catégorie | IsAuthenticated |
| GET | /api/core/modules/active_for_user/ | Modules actifs pour l'utilisateur | IsAuthenticated |

### OrganizationModuleViewSet

| Méthode | URL | Description | Permission |
|---------|-----|-------------|------------|
| GET | /api/core/organization-modules/ | Liste des modules d'organisation | IsAuthenticated |
| POST | /api/core/organization-modules/ | Créer un lien module-org | IsAuthenticated |
| GET | /api/core/organization-modules/{id}/ | Détails | IsAuthenticated |
| PUT/PATCH | /api/core/organization-modules/{id}/ | Modifier | IsAuthenticated |
| DELETE | /api/core/organization-modules/{id}/ | Supprimer | IsAuthenticated |
| POST | /api/core/organization-modules/{id}/enable/ | Activer un module | IsAuthenticated |
| POST | /api/core/organization-modules/{id}/disable/ | Désactiver un module | IsAuthenticated |

## Exemples de requêtes

### Créer une organisation

**Request:**
```json
POST /api/core/organizations/
{
  "name": "Ma Boutique",
  "subdomain": "ma-boutique",
  "category": 1,
  "logo_url": "https://example.com/logo.png",
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "contact_email": "contact@ma-boutique.com"
  }
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Ma Boutique",
  "subdomain": "ma-boutique",
  "logo_url": "https://example.com/logo.png",
  "logo": null,
  "category": 1,
  "category_details": {
    "id": 1,
    "name": "Commerce",
    "description": "Commerce de détail"
  },
  "admin": "123e4567-e89b-12d3-a456-426614174001",
  "admin_email": "admin@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "settings": {
    "country": "GN",
    "currency": "GNF",
    "contact_email": "contact@ma-boutique.com"
  },
  "modules": []
}
```

### Obtenir les modules actifs pour l'utilisateur

**Request:**
```json
GET /api/core/modules/active_for_user/?organization_subdomain=ma-boutique
```

**Response:**
```json
{
  "active_modules": [
    "hr.employees",
    "hr.attendance",
    "inventory.products",
    "inventory.sales"
  ],
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "organization_name": "Ma Boutique"
}
```

### Activer un module pour une organisation

**Request:**
```json
POST /api/core/organization-modules/{id}/enable/
```

**Response:**
```json
{
  "message": "Module \"Gestion des employés\" activé",
  "organization_module": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "module": "123e4567-e89b-12d3-a456-426614174003",
    "module_details": {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "code": "hr.employees",
      "name": "Gestion des employés",
      "description": "Module de gestion des employés",
      "app_name": "hr",
      "icon": "Users",
      "category": "hr",
      "is_core": false,
      "is_active": true
    },
    "is_enabled": true,
    "settings": {},
    "enabled_at": "2024-01-15T10:30:00Z",
    "enabled_by": "123e4567-e89b-12d3-a456-426614174001"
  }
}
```

## Serializers

- **CategorySerializer** : Sérialisation des catégories d'organisation
- **OrganizationSettingsSerializer** : Sérialisation des paramètres d'organisation
- **OrganizationSerializer** : Sérialisation complète des organisations (inclut settings et modules)
- **OrganizationCreateSerializer** : Création d'organisation avec settings et modules
- **ModuleSerializer** : Sérialisation des modules
- **OrganizationModuleSerializer** : Sérialisation des liens organisation-module
- **OrganizationModuleCreateSerializer** : Création de liens module-organisation

## Permissions

### Système de permissions

Le module core fournit un système de permissions personnalisé basé sur des codes de permissions (ex: 'hr.view_employees').

**AdminUser** : A toujours toutes les permissions
**Employee** : Les permissions sont vérifiées via :
1. Le rôle assigné (`assigned_role`)
2. Les permissions personnalisées (`custom_permissions`)

Les permissions sont organisées par catégories (hr, inventory, etc.) et suivent une convention de nommage : `app.action_resource`.

### Vérification des permissions

```python
# Pour un Employee
employee.has_permission('hr.view_employees')  # True/False

# Pour un AdminUser
admin.has_permission('hr.view_employees')  # Toujours True
```

## Services/Utilities

- **core/modules.py** : Registry des modules (ModuleRegistry) avec définition des modules par défaut
- **core/permission_dependencies.py** : Gestion des dépendances entre permissions

## Tests

État : Tests partiels
Coverage : Non mesuré

## Utilisation

### Cas d'usage principaux

1. **Inscription d'un administrateur** : Création d'AdminUser + Organisation automatique
2. **Connexion unifiée** : AdminUser et Employee se connectent avec le même endpoint
3. **Gestion multi-organisation** : Un AdminUser peut avoir plusieurs organisations
4. **Activation de modules** : Chaque organisation peut activer/désactiver des modules selon ses besoins
5. **Permissions granulaires** : Système de permissions personnalisé pour contrôler l'accès aux fonctionnalités

### Architecture multi-tenant

Le système utilise une architecture multi-tenant basée sur l'organisation :
- Chaque entité métier (Employee, Product, Sale, etc.) appartient à une Organisation
- Le filtrage par organisation est fait au niveau du QuerySet
- Le subdomain de l'organisation peut être utilisé pour le routing frontend

## Points d'attention

### Multi-table Inheritance
- BaseUser utilise l'héritage multi-table Django
- Permet le polymorphisme : ForeignKey(BaseUser) peut référencer AdminUser ou Employee
- Utiliser `get_concrete_user()` pour obtenir l'objet enfant

### Permissions vs Django Permissions
- Le système custom de permissions (Permission model) est indépendant des permissions Django
- Les permissions Django (via PermissionsMixin) sont toujours disponibles mais peu utilisées
- Privilégier le système custom pour la logique métier

### Activation des modules
- Les modules core (is_core=True) ne peuvent pas être désactivés
- Vérifier les dépendances avant d'activer un module (depends_on)
- Les modules par défaut sont activés automatiquement à la création d'une organisation selon sa catégorie

### Logo d'organisation
- Deux champs : `logo_url` (URL externe) et `logo` (fichier uploadé)
- L'endpoint `/api/core/organizations/{id}/logo/` gère l'upload et la suppression
- Formats acceptés : JPG, PNG, GIF, WebP, SVG
- Taille max : 10 Mo
