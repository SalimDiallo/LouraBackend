# Documentation des Applications Loura

Documentation complète des 7 applications Django du backend Loura.

## Vue d'ensemble du système

Loura est une plateforme multi-tenant de gestion d'entreprise avec architecture modulaire. Chaque organisation peut activer/désactiver les modules selon ses besoins.

## Applications documentées

### 1. [CORE](./CORE.md) - Module Central
**Rôle** : Gestion des utilisateurs, organisations multi-tenant, permissions, rôles et modules activables.

**Modèles principaux** :
- BaseUser (modèle parent polymorphe)
- AdminUser (administrateur d'organisations)
- Organization (tenant multi-tenant)
- Module, OrganizationModule (système de modules activables)
- Permission, Role (système de permissions personnalisé)

**Points clés** :
- Multi-table inheritance pour BaseUser → AdminUser/Employee
- Architecture multi-tenant basée sur Organization
- Système de permissions granulaires indépendant de Django
- Modules activables/désactivables par organisation

---

### 2. [AUTHENTICATION](./AUTHENTICATION.md) - Authentification
**Rôle** : Authentification unifiée JWT pour AdminUser et Employee.

**Endpoints principaux** :
- `/api/auth/login/` - Connexion unifiée
- `/api/auth/register/` - Inscription administrateur
- `/api/auth/refresh/` - Rafraîchissement token
- `/api/auth/me/` - Utilisateur connecté

**Points clés** :
- JWT avec djangorestframework-simplejwt
- Custom claims (user_type, organization_id)
- Blacklist des refresh tokens
- Gestion du profil et changement de mot de passe

---

### 3. [HR](./HR.md) - Ressources Humaines
**Rôle** : Gestion complète des RH : employés, départements, contrats, congés, paie, pointages.

**Modules** :
- **Employés** : CRUD, départements, postes, contrats
- **Congés** : Types, demandes, soldes (global par employé/année)
- **Paie** : Périodes, fiches de paie, primes/déductions, avances
- **Pointages** : Check-in/out, pauses multiples, QR code multi-employés
- **Permissions** : Rôles et permissions personnalisés

**Modèles principaux** : 16 modèles (Employee, Department, Position, Contract, LeaveType, LeaveRequest, LeaveBalance, PayrollPeriod, Payslip, PayrollAdvance, Attendance, Break, QRCodeSession, etc.)

**Points clés** :
- Employee hérite de BaseUser (polymorphisme)
- Règle : Un seul contrat actif par employé
- Solde de congés global (tous types confondus)
- Pauses multiples par jour (modèle Break)
- QR code sessions multi-employés

---

### 4. [INVENTORY](./INVENTORY.md) - Gestion des Stocks et Ventes
**Rôle** : Gestion complète des stocks, approvisionnement, ventes et clients.

**Modules** :
- **Produits** : Catalogue, catégories, SKU, prix, niveaux de stock
- **Stocks** : Multi-entrepôts, mouvements tracés, inventaires physiques
- **Approvisionnement** : Commandes fournisseurs, réception, transport
- **Alertes** : Stock bas, rupture, surstock, produits sans mouvement
- **Ventes** : POS avec remises, TVA, paiements partiels, ventes à crédit
- **Clients** : Gestion clients avec limite de crédit, suivi des dettes

**Modèles principaux** : 16 modèles (Category, Warehouse, Supplier, Product, Stock, Movement, Order, StockCount, Alert, Customer, Sale, Payment, CreditSale, etc.)

**Points clés** :
- Stock multi-entrepôts avec localisation
- Mouvements liés aux commandes et ventes
- Remises globales et par ligne
- Ventes à crédit avec échéances
- Export PDF des factures

---

### 5. [AI](./AI.md) - Assistant IA
**Rôle** : Assistant conversationnel IA pour les utilisateurs.

**Fonctionnalités** :
- Conversations avec historique
- Mode assistant (réponses textuelles)
- Mode agent (actions automatiques via outils)
- Feedback utilisateur (like/dislike)
- Métriques (tokens, temps de réponse)

**Modèles principaux** : 3 modèles (Conversation, Message, AIToolExecution)

**Points clés** :
- Support des tool calls (mode agent)
- Filtrage automatique par organisation
- Logs détaillés des exécutions d'outils
- Feedback pour amélioration continue

---

### 6. [NOTIFICATIONS](./NOTIFICATIONS.md) - Notifications
**Rôle** : Système de notifications interne pour informer les utilisateurs.

**Types de notifications** :
- **alert** : Alertes métier (stock bas, échéances, etc.)
- **system** : Messages système (mises à jour, maintenance)
- **user** : Actions utilisateur (approbations, commentaires, assignations)

**Priorités** : low, medium, high, critical

**Modèles principaux** : 2 modèles (Notification, NotificationPreference)

**Points clés** :
- Préférences personnalisables par utilisateur
- Lien générique vers les entités (entity_type + entity_id)
- Filtrage par priorité minimale
- Statut lu/non lu avec date de lecture

---

### 7. [SERVICES](./SERVICES.md) - Gestion de Services Générique
**Rôle** : Module générique et configurable pour gérer tout type de service (location, projets, dossiers, etc.).

**Architecture data-driven** :
```
BusinessProfile → ServiceType → ServiceField/ServiceStatus → Service
```

**Fonctionnalités** :
- **Profils métier** : Secteurs d'activité (BTP, Voyage, Auto, etc.)
- **Types de services** : Configurables avec champs dynamiques
- **Champs dynamiques** : 17 types de champs (text, number, date, select, etc.)
- **Statuts personnalisables** : Workflow avec transitions autorisées
- **Services imbriqués** : Hiérarchie de services (projet → sous-tâches)
- **Templates** : Création rapide avec valeurs pré-remplies
- **Historique complet** : Statuts, activités, commentaires

**Modèles principaux** : 9 modèles (BusinessProfile, ServiceType, ServiceField, ServiceStatus, Service, ServiceStatusHistory, ServiceActivity, ServiceComment, ServiceTemplate)

**Points clés** :
- Configuration 100% data-driven (pas de code pour nouveaux services)
- Champs stockés dans JSONField field_values
- Workflow de statuts avec validation des transitions
- Références auto-générées (format: PREFIX-YEAR-NUMBER)
- Support multi-devise et pricing flexible

---

## Architecture globale

### Multi-tenant
- Chaque entité métier appartient à une **Organization**
- Filtrage automatique par organisation dans les ViewSets
- Isolation complète des données entre organisations

### Permissions
- Système personnalisé (Permission/Role) indépendant de Django
- AdminUser : toutes les permissions
- Employee : permissions via rôle assigné + permissions custom
- Format : `app.action_resource` (ex: `hr.view_employees`)

### Modules activables
- Chaque organisation active ses propres modules
- Modules core (is_core=True) : toujours activés
- Dépendances entre modules gérées automatiquement

### API RESTful
- Django REST Framework avec ViewSets
- Authentification JWT (djangorestframework-simplejwt)
- Pagination, filtres, recherche standards
- Format de réponse uniforme

### Base de données
- PostgreSQL
- UUID pour la plupart des modèles
- JSONField pour données flexibles
- TimeStampedModel (created_at, updated_at) hérité partout

---

## Statistiques

| Application | Modèles | ViewSets | Endpoints (approx.) |
|-------------|---------|----------|---------------------|
| CORE | 9 | 4 | 25 |
| AUTHENTICATION | 0 | 0 | 7 |
| HR | 16 | 12 | 80 |
| INVENTORY | 16 | 15 | 100 |
| AI | 3 | 2 | 10 |
| NOTIFICATIONS | 2 | 2 | 15 |
| SERVICES | 9 | 9 | 60 |
| **TOTAL** | **55** | **44** | **~297** |

---

## Conventions de code

### Modèles
- Tous héritent de `TimeStampedModel` (sauf BaseUser)
- UUID comme clé primaire (sauf quelques exceptions)
- ForeignKey vers Organization pour multi-tenant
- Meta : `db_table`, `verbose_name`, `ordering`, `indexes`

### ViewSets
- Héritent souvent de `BaseOrganizationViewSetMixin` (filtrage auto)
- Serializers différents par action (list, create, update)
- Actions custom : `@action(detail=True/False, methods=['post'])`
- Permissions : Classes personnalisées dans `app/permissions.py`

### Serializers
- Validation dans `validate()` et `validate_field()`
- Création/update custom dans `create()` et `update()`
- Représentation nested pour les relations

### URLs
- Router DRF pour les ViewSets
- Format : `/api/{app}/{resource}/`
- Actions custom : `/api/{app}/{resource}/{id}/{action}/`

---

## Points d'attention globaux

### Performance
- Utiliser `select_related()` et `prefetch_related()` pour les relations
- Indexes sur les champs fréquemment filtrés
- Pagination obligatoire sur les listes

### Sécurité
- Validation des permissions à chaque action
- Filtrage par organisation systématique
- Validation des données d'entrée (serializers)
- Protection CSRF, CORS configurés

### Maintenance
- Tests unitaires et d'intégration (en cours)
- Logs structurés (module logging)
- Migrations Django versionnées
- Documentation des modèles et API

---

## Prochaines étapes

1. **Tests** : Augmenter la couverture de tests
2. **Documentation API** : Swagger/OpenAPI auto-généré
3. **WebSockets** : Notifications temps réel
4. **Exports** : PDF/Excel pour tous les modules
5. **Analytics** : Tableaux de bord et KPIs
6. **Mobile** : API optimisées pour mobile

---

## Liens utiles

- [README principal](../../README.md)
- [Configuration](../CONFIGURATION.md)
- [Déploiement](../DEPLOYMENT.md)
- [API Reference](../API.md)

---

**Date de dernière mise à jour** : 2024-01-15
**Version** : 1.0.0
