# 🏢 Guide de Gestion des Organisations

## 📋 Résumé

La gestion des organisations est **déjà entièrement implémentée** dans le module `core`. Ce guide vous montre comment l'utiliser.

## ✅ Fonctionnalités disponibles

### 1. Gestion via l'API REST

- ✅ **Créer une organisation** avec sélection de catégorie
- ✅ **Modifier une organisation** (PUT/PATCH)
- ✅ **Afficher les organisations** (liste et détails)
- ✅ **Supprimer une organisation**
- ✅ **Activer/Désactiver une organisation**
- ✅ **Lister les catégories** disponibles

### 2. Gestion via Django Admin

- ✅ Interface d'administration complète
- ✅ Gestion des AdminUser
- ✅ Gestion des catégories
- ✅ Gestion des organisations
- ✅ Édition des settings inline

---

## 🚀 Démarrage rapide

### Étape 1: Créer les catégories (si nécessaire)

```bash
python manage.py create_sample_categories
```

Cela créera 8 catégories par défaut:
- Technologie
- Santé
- Éducation
- Commerce
- Services
- Finance
- Industrie
- Restauration

### Étape 2: Démarrer le serveur

```bash
python manage.py runserver
```

### Étape 3: Accéder à l'Admin Django

```
http://localhost:8000/admin/
```

### Étape 4: Utiliser l'API

Consultez le fichier `ORGANISATION_API.md` pour la documentation complète de l'API.

---

## 📊 Structure des données

### AdminUser (UserManager)
```python
{
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "organizations_count": 2
}
```

### Category
```python
{
    "id": 1,
    "name": "Technologie",
    "description": "Entreprises du secteur technologique..."
}
```

### Organization
```python
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
    "settings": {
        "country": "GN",
        "currency": "GNF",
        "theme": "dark",
        "contact_email": "contact@example.com"
    }
}
```

---

## 🔗 Endpoints principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/core/categories/` | Lister les catégories |
| `GET` | `/api/core/categories/{id}/` | Détails d'une catégorie |
| `GET` | `/api/core/organizations/` | Lister mes organisations |
| `POST` | `/api/core/organizations/` | Créer une organisation |
| `GET` | `/api/core/organizations/{id}/` | Détails d'une organisation |
| `PUT` | `/api/core/organizations/{id}/` | Modifier (complète) |
| `PATCH` | `/api/core/organizations/{id}/` | Modifier (partielle) |
| `DELETE` | `/api/core/organizations/{id}/` | Supprimer |
| `POST` | `/api/core/organizations/{id}/activate/` | Activer |
| `POST` | `/api/core/organizations/{id}/deactivate/` | Désactiver |

---

## 💡 Exemples d'utilisation

### Exemple 1: Créer une organisation

```bash
curl -X POST http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions",
    "subdomain": "tech-solutions",
    "category": 1,
    "logo_url": "https://example.com/logo.png",
    "settings": {
      "country": "GN",
      "currency": "GNF",
      "theme": "light",
      "contact_email": "contact@tech-solutions.com"
    }
  }'
```

### Exemple 2: Modifier le nom et la catégorie

```bash
curl -X PATCH http://localhost:8000/api/core/organizations/{id}/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Solutions Pro",
    "category": 2
  }'
```

### Exemple 3: Lister toutes mes organisations

```bash
curl -X GET http://localhost:8000/api/core/organizations/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Tests

### Test automatique

```bash
python test_organization_api.py
```

Ce script teste:
- Création d'un AdminUser
- Affichage des catégories
- Création d'une organisation
- Modification d'une organisation
- Affichage des organisations
- Gestion des settings

### Test manuel via Django Shell

```bash
python manage.py shell
```

```python
from core.models import AdminUser, Organization, Category

# Créer un admin
admin = AdminUser.objects.create_user(
    email="test@example.com",
    password="password123",
    first_name="Test",
    last_name="User"
)

# Créer une organisation
category = Category.objects.get(name="Technologie")
org = Organization.objects.create(
    name="Ma Super Entreprise",
    subdomain="super-entreprise",
    admin=admin,
    category=category
)

# Afficher les organisations de l'admin
admin.get_organizations_for_admin()

# Modifier l'organisation
org.name = "Entreprise Modifiée"
org.save()
```

---

## 📁 Fichiers importants

| Fichier | Description |
|---------|-------------|
| `core/models.py` | Modèles: AdminUser, Organization, Category, OrganizationSettings |
| `core/serializers.py` | Serializers pour l'API REST |
| `core/views.py` | ViewSets pour CRUD des organisations |
| `core/urls.py` | Configuration des endpoints |
| `core/admin.py` | Configuration de l'interface admin Django |
| `ORGANISATION_API.md` | Documentation complète de l'API |

---

## 🔐 Sécurité

- ✅ Authentification JWT requise
- ✅ Un AdminUser ne peut voir que ses organisations
- ✅ Validation du subdomain (alphanumeric + tirets)
- ✅ Soft delete disponible via TimeStampedModel
- ✅ Tokens HTTP-only cookies pour sécurité accrue

---

## 🎯 Prochaines étapes

1. **Frontend**: Créer l'interface React/Next.js pour consommer l'API
2. **Permissions**: Ajouter des permissions plus fines (lecture, écriture, etc.)
3. **Employees**: Implémenter le module HR pour les employés
4. **Multi-langue**: Ajouter le support de plusieurs langues
5. **Upload de logo**: Implémenter l'upload de fichiers pour les logos

---

## 📞 Support

Pour toute question ou problème:
- Consulter `ORGANISATION_API.md` pour la documentation API
- Consulter `CLAUDE.md` pour les instructions du projet
- Vérifier les logs Django en cas d'erreur

---

## ✨ Conclusion

La gestion des organisations est **entièrement fonctionnelle**. Vous pouvez:
- Créer, modifier, afficher et supprimer des organisations via l'API
- Sélectionner une catégorie lors de la création
- Gérer les organisations via l'interface Django Admin
- Utiliser les catégories prédéfinies ou en créer de nouvelles

**Tout est prêt pour être intégré avec votre frontend Next.js !** 🚀
