# Documentation des Applications Django - Loura Backend

Cette documentation détaille les 7 applications Django du projet Loura avec une approche exhaustive et structurée.

## 📁 Fichiers disponibles

| Fichier | Taille | Description |
|---------|--------|-------------|
| [INDEX.md](./INDEX.md) | 9.1K | Vue d'ensemble et navigation rapide |
| [CORE.md](./CORE.md) | 15.6K | Module central (users, organizations, permissions) |
| [AUTHENTICATION.md](./AUTHENTICATION.md) | 11.5K | Authentification JWT unifiée |
| [HR.md](./HR.md) | 23.1K | Ressources Humaines (employés, congés, paie, pointages) |
| [INVENTORY.md](./INVENTORY.md) | 12.8K | Gestion stocks et ventes |
| [AI.md](./AI.md) | 7.5K | Assistant IA conversationnel |
| [NOTIFICATIONS.md](./NOTIFICATIONS.md) | 10.9K | Système de notifications |
| [SERVICES.md](./SERVICES.md) | 16.4K | Module générique de services |

**Total** : 8 fichiers, ~124 Ko de documentation

## 🚀 Par où commencer ?

1. **Vue d'ensemble** : Commencez par [INDEX.md](./INDEX.md) pour une vue d'ensemble du système
2. **Architecture de base** : Lisez [CORE.md](./CORE.md) pour comprendre l'architecture multi-tenant et les permissions
3. **Authentification** : [AUTHENTICATION.md](./AUTHENTICATION.md) pour le système JWT
4. **Modules métier** : Consultez les documentations spécifiques selon vos besoins (HR, INVENTORY, SERVICES, etc.)

## 📊 Contenu de chaque fichier

Chaque fichier de documentation suit la même structure :

### Vue d'ensemble
- Description du rôle de l'application
- Architecture et dépendances

### Modèles de données
- Description détaillée de TOUS les modèles
- TOUS les champs avec types et descriptions
- Relations (ForeignKey, ManyToMany, etc.)
- Méthodes importantes

### API Endpoints
- Tableau complet des endpoints avec méthodes HTTP, URLs, descriptions et permissions
- Filtres disponibles

### Exemples de requêtes
- Exemples JSON réels de requêtes et réponses
- Cas d'usage principaux

### Serializers
- Liste des serializers utilisés

### Permissions
- Système de permissions de l'application

### Services/Utilities
- Fichiers auxiliaires et utilitaires

### Tests
- État actuel des tests

### Utilisation
- Cas d'usage principaux
- Exemples concrets

### Points d'attention
- Particularités techniques
- Best practices
- Limitations
- Pièges à éviter

## 🔍 Statistiques globales

- **55 modèles** au total
- **44 ViewSets** pour l'API REST
- **~297 endpoints** API
- **7 applications** Django

## 🛠️ Technologies utilisées

- **Django 5.1+** : Framework web
- **Django REST Framework** : API REST
- **djangorestframework-simplejwt** : Authentification JWT
- **PostgreSQL** : Base de données
- **UUID** : Clés primaires
- **JSONField** : Données flexibles

## 📝 Conventions

### Modèles
- Héritage de `TimeStampedModel` (created_at, updated_at)
- UUID comme clé primaire (sauf exceptions)
- ForeignKey vers Organization pour multi-tenant
- Meta : db_table, verbose_name, ordering, indexes

### API
- REST avec Django REST Framework
- Authentification JWT Bearer token
- Pagination automatique
- Filtres et recherche standards

### Permissions
- Système custom (Permission/Role) indépendant de Django
- Format : `app.action_resource` (ex: `hr.view_employees`)
- AdminUser : toutes les permissions
- Employee : permissions via rôle + custom

## 🔗 Liens utiles

- [README principal](../../README.md)
- Backend : `/home/salim/Projets/loura/stack/backend/`
- Apps : `/home/salim/Projets/loura/stack/backend/app/`

## 📅 Informations

- **Date de création** : 2024-01-15
- **Version** : 1.0.0
- **Auteur** : Documentation générée par Claude Code
- **Projet** : Loura ERP Multi-tenant

## 💡 Comment contribuer ?

Pour mettre à jour cette documentation :

1. Lire le code source de l'application
2. Mettre à jour le fichier .md correspondant
3. Respecter la structure existante
4. Inclure des exemples concrets
5. Vérifier la cohérence avec le code

---

**Note** : Cette documentation est exhaustive et basée sur le code source réel du projet. Tous les modèles, champs, endpoints et exemples sont authentiques et à jour au moment de la génération.
