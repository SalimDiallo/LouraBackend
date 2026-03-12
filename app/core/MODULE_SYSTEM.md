# Système de gestion des modules

## Vue d'ensemble

Le système de modules permet d'activer/désactiver des fonctionnalités spécifiques pour chaque organisation. Les modules sont définis de manière centralisée et peuvent être activés automatiquement selon la catégorie de l'organisation.

## Architecture

### 1. Modèles de données

#### Module

- **code** : Identifiant unique (ex: `hr.employees`, `hr.payroll`)
- **name** : Nom d'affichage
- **description** : Description détaillée
- **app_name** : Application Django associée
- **category** : Catégorie du module (hr, finance, inventory, etc.)
- **default_for_all** : Activé par défaut pour toutes les organisations
- **default_categories** : Liste des catégories pour lesquelles le module est activé par défaut
- **is_core** : Module core qui ne peut pas être désactivé
- **depends_on** : Liste des modules requis

#### OrganizationModule

- **organization** : Organisation concernée
- **module** : Module activé
- **is_enabled** : Statut d'activation
- **settings** : Paramètres spécifiques du module pour cette organisation
- **enabled_by** : Utilisateur ayant activé le module

### 2. Registry des modules (`core/modules.py`)

Le système utilise un registry centralisé qui définit tous les modules disponibles :

```python
from core.modules import ModuleDefinition, ModuleRegistry

# Définir un nouveau module
NEW_MODULE = ModuleDefinition(
    code='hr.new_feature',
    name='Nouvelle fonctionnalité',
    description='Description de la fonctionnalité',
    app_name='hr',
    icon='Icon',
    category='hr',
    default_categories=['Technologie', 'Services'],
    depends_on=['hr.employees'],
    order=10
)

# L'enregistrement se fait automatiquement dans register_all_modules()
```

## Modules RH disponibles

### Modules core (obligatoires)

1. **hr.employees** - Gestion des employés
   - Inclut départements et postes
   - Activé pour toutes les catégories
   - Ne peut pas être désactivé

2. **hr.permissions** - Permissions et rôles
   - Gestion des rôles et permissions
   - Activé pour toutes les catégories
   - Ne peut pas être désactivé

### Modules optionnels

3. **hr.payroll** - Module de paie
   - Fiches de paie, périodes, avances
   - Par défaut : Technologie, Finance, Services, Commerce, Industrie, BTP, Transports, Santé, Éducation

4. **hr.leave** - Module de congés
   - Demandes, types de congés, soldes
   - Par défaut : Toutes sauf Agriculture, Energie, Agence de voyage, Art & Culture

5. **hr.attendance** - Module de pointage
   - Présences, pointage QR Code
   - Par défaut : Commerce, Industrie, BTP, Transports, Restauration, Santé, Agriculture, Energie

6. **hr.contracts** - Gestion des contrats
   - CDI, CDD, Stage, Freelance
   - Par défaut : Technologie, Finance, Services, Commerce, Industrie, BTP, Santé, Éducation

## Commandes de gestion

### Initialiser les modules

```bash
python manage.py initialize_modules

# Options :
--dry-run   # Prévisualiser sans modifier la base de données
--force     # Forcer la mise à jour des modules existants
```

### Créer les catégories

```bash
python manage.py create_sample_categories

# Options :
--with-modules  # Afficher les modules par défaut pour chaque catégorie
```

## API Endpoints

### Modules

#### Lister tous les modules

```
GET /api/core/modules/
```

#### Obtenir les modules par défaut pour une catégorie

```
GET /api/core/modules/defaults/?category_id=1
GET /api/core/modules/defaults/?category_name=Technologie
```

#### Obtenir les modules groupés par catégorie

```
GET /api/core/modules/by_category/
```

### Modules d'organisation

#### Lister les modules d'une organisation

```
GET /api/core/organization-modules/
```

#### Activer un module

```
POST /api/core/organization-modules/{id}/enable/
```

#### Désactiver un module

```
POST /api/core/organization-modules/{id}/disable/
```

## Création d'organisation avec modules

### Activation automatique (recommandé)

Lors de la création d'une organisation, les modules par défaut sont automatiquement activés selon la catégorie :

```json
{
  "name": "Mon Entreprise",
  "subdomain": "mon-entreprise",
  "category": 1,
  "settings": {
    "currency": "GNF",
    "country": "GN"
  }
}
```

### Activation manuelle

Vous pouvez spécifier manuellement les modules à activer :

```json
{
  "name": "Mon Entreprise",
  "subdomain": "mon-entreprise",
  "category": 1,
  "modules": [
    {
      "module_code": "hr.employees",
      "is_enabled": true
    },
    {
      "module_code": "hr.payroll",
      "is_enabled": true,
      "settings": {
        "auto_calculate": true
      }
    },
    {
      "module_code": "hr.leave",
      "is_enabled": true
    }
  ]
}
```

## Ajouter un nouveau module

### 1. Définir le module dans `core/modules.py`

```python
# Définition du module
NEW_MODULE = ModuleDefinition(
    code='hr.performance',
    name='Évaluation des performances',
    description='Système d\'évaluation des performances des employés',
    app_name='hr',
    icon='TrendingUp',
    category='hr',
    default_categories=['Technologie', 'Services', 'Finance'],
    depends_on=['hr.employees'],
    order=7
)

# Ajouter dans register_all_modules()
def register_all_modules():
    modules = [
        EMPLOYEES_MODULE,
        PAYROLL_MODULE,
        LEAVE_MODULE,
        ATTENDANCE_MODULE,
        CONTRACTS_MODULE,
        PERMISSIONS_MODULE,
        NEW_MODULE,  # ← Ajouter ici
    ]
    # ...
```

### 2. Initialiser dans la base de données

```bash
python manage.py initialize_modules
```

### 3. Le module est maintenant disponible via l'API

## Gestion des dépendances

Les modules peuvent dépendre d'autres modules. Par exemple, tous les modules RH dépendent de `hr.employees`.

Lors de l'activation d'un module :

- Les dépendances ne sont PAS automatiquement activées
- Le frontend/backend doit vérifier les dépendances avant activation
- Lors de la désactivation, vérifier qu'aucun autre module ne dépend du module à désactiver

```python
module = Module.objects.get(code='hr.payroll')
dependencies = module.get_dependencies()  # Retourne QuerySet de Module
# [<Module: Gestion des employés (hr.employees)>]
```

## Migration d'organisations existantes

Pour ajouter les modules par défaut aux organisations existantes :

```python
from core.models import Organization, Module, OrganizationModule
from core.modules import ModuleRegistry

for org in Organization.objects.all():
    if org.category:
        default_modules = ModuleRegistry.get_default_modules_for_category(org.category.name)
        for module_def in default_modules:
            try:
                module = Module.objects.get(code=module_def.code)
                OrganizationModule.objects.get_or_create(
                    organization=org,
                    module=module,
                    defaults={'is_enabled': True}
                )
            except Module.DoesNotExist:
                pass
```

## Bonnes pratiques

1. **Modules core** : Marquer comme `is_core=True` les modules essentiels qui ne peuvent pas être désactivés
2. **Dépendances** : Toujours spécifier les dépendances pour éviter les incohérences
3. **Catégories par défaut** : Être conservateur avec `default_for_all`, préférer `default_categories`
4. **Ordre d'affichage** : Utiliser `order` pour contrôler l'ordre d'affichage dans le frontend
5. **Initialisation** : Toujours exécuter `initialize_modules` après avoir ajouté de nouveaux modules
6. **Testing** : Tester l'activation/désactivation des modules et leurs dépendances

## Frontend Integration

### Récupérer les modules disponibles

```typescript
const response = await fetch("/api/core/modules/");
const modules = await response.json();
```

### Récupérer les modules par défaut pour une catégorie

```typescript
const response = await fetch(
  `/api/core/modules/defaults/?category_id=${categoryId}`,
);
const data = await response.json();
// data.default_modules contient les modules pré-sélectionnés
```

### Créer une organisation avec modules

```typescript
const payload = {
  name: "Mon Entreprise",
  subdomain: "mon-entreprise",
  category: categoryId,
  modules: selectedModules.map((moduleCode) => ({
    module_code: moduleCode,
    is_enabled: true,
  })),
};

const response = await fetch("/api/core/organizations/", {
  method: "POST",
  body: JSON.stringify(payload),
});
```
