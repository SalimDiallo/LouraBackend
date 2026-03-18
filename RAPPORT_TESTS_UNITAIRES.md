# 📊 RAPPORT D'ANALYSE - Tests Unitaires pour le Projet Loura Backend

**Date de génération** : 17 Mars 2026
**Analyste** : Claude Code
**Version** : 1.0

---

## 🔍 Vue d'ensemble du projet

Votre projet Django est une plateforme multi-tenant complète avec 7 applications principales :

- **AI** : Assistant IA avec agent, chat streaming et outils
- **Authentication** : Gestion utilisateurs (Admin/Employee) avec JWT
- **Core** : Organisations, modules, catégories
- **HR** : Gestion RH complète (employés, congés, paie, présence)
- **Inventory** : Système d'inventaire massif (19 ViewSets)
- **Services** : Gestion de services métier
- **Notifications** : Notifications temps réel avec SSE

**État actuel** : Les fichiers `tests.py` existent mais sont vides (aucun test implémenté).

---

## 🎯 Tests Unitaires Recommandés par Application

### 1️⃣ **AI Module** (app/ai/)

#### **Endpoints à tester** :
- `POST /api/ai/conversations/` - Création conversation
- `GET /api/ai/conversations/` - Liste conversations
- `DELETE /api/ai/conversations/{id}/clear/` - Effacer messages
- `POST /api/ai/conversations/{id}/feedback/` - Ajouter feedback
- `POST /api/ai/chat/` - Chat non-streaming
- `POST /api/ai/chat/stream/` - Chat streaming (SSE)
- `GET /api/ai/tools/` - Liste outils disponibles
- `GET /api/ai/config/` - Configuration IA

#### **Tests critiques** :

##### **ConversationViewSet** (app/ai/views.py:28-78)
```python
✅ Test création conversation avec organisation valide
✅ Test filtrage par subdomain organisation (header X-Organization-Subdomain)
✅ Test queryset vide sans organisation
✅ Test action clear() - suppression messages + création message assistant
✅ Test action feedback() - validation message_id requis
✅ Test feedback avec message inexistant (404)
✅ Test sérialiseur différent pour list vs detail
✅ Test permissions IsAuthenticated
```

##### **ChatView** (app/ai/views.py:80-178)
```python
✅ Test POST sans header X-Organization-Subdomain → erreur 400
✅ Test création conversation si conversation_id absent
✅ Test récupération conversation existante si conversation_id fourni
✅ Test sauvegarde message utilisateur
✅ Test appel agent IA et sauvegarde réponse
✅ Test gestion erreur ValueError de l'agent → 500
✅ Test création AIToolExecution si tool_calls présents
✅ Test response contient : content, conversation_id, message_id, tool_calls, model
✅ Mock LouraAIAgent.chat() pour éviter appels API réels
```

##### **ChatStreamView** (app/ai/views.py:181-304)
```python
✅ Test POST sans header X-Organization-Subdomain → erreur 400
✅ Test streaming SSE avec événements token, tools, done, error
✅ Test accumulation du contenu complet (full_content)
✅ Test event "clear" après exécution d'outils
✅ Test sauvegarde message final avec tool_calls/tool_results
✅ Test headers HTTP : Cache-Control, X-Accel-Buffering
✅ Mock agent.chat_stream() generator
```

##### **AIToolsView** (app/ai/views.py:307-330)
```python
✅ Test GET retourne liste outils avec name, description, category
✅ Test is_read_only correctement exposé
✅ Test params extraits de tool.parameters
✅ Test total count exact
```

##### **AIConfigView** (app/ai/views.py:333-346)
```python
✅ Test GET retourne configured, model, provider, tools_enabled
✅ Test ai_config.is_configured() appelé correctement
```

---

### 2️⃣ **Authentication Module** (app/authentication/)

#### **Endpoints à tester** :
- `POST /api/auth/login/` - Connexion unifiée
- `POST /api/auth/register/admin/` - Inscription admin
- `POST /api/auth/logout/` - Déconnexion
- `POST /api/auth/refresh/` - Rafraîchir token
- `GET /api/auth/me/` - Utilisateur courant
- `PATCH /api/auth/profile/` - Mise à jour profil
- `POST /api/auth/change-password/` - Changement mot de passe

#### **Tests critiques** :

##### **LoginView** (app/authentication/views.py:38-79)
```python
✅ Test login admin avec email/password valides
✅ Test login employee avec email/password valides
✅ Test login avec credentials invalides → 400
✅ Test user_type correct dans response (admin vs employee)
✅ Test génération tokens JWT (access + refresh)
✅ Test mise à jour last_login
✅ Test cookies JWT définis (set_jwt_cookies)
✅ Test sérialiseur différent selon user_type
✅ Test conversion UUIDs en strings
```

##### **RegisterAdminView** (app/authentication/views.py:86-118)
```python
✅ Test création admin + organisation simultanée
✅ Test email unique (ValidationError si doublon)
✅ Test password minimum 8 caractères
✅ Test génération tokens après inscription
✅ Test cookies JWT définis
✅ Test response contient user, user_type='admin', tokens
```

##### **LogoutView** (app/authentication/views.py:125-150)
```python
✅ Test blacklist refresh token depuis cookie
✅ Test blacklist refresh token depuis request.data
✅ Test logout sans token (ne crash pas, retourne 200)
✅ Test clear_jwt_cookies appelé
✅ Test permissions IsAuthenticated
```

##### **RefreshTokenView** (app/authentication/views.py:157-207)
```python
✅ Test refresh depuis cookie
✅ Test refresh depuis request.data
✅ Test refresh sans token → 400
✅ Test token expiré → 401
✅ Test user désactivé → 401
✅ Test user inexistant → 404
✅ Test nouveaux tokens générés
✅ Test cookies mis à jour
```

##### **CurrentUserView** (app/authentication/views.py:214-232)
```python
✅ Test GET retourne utilisateur connecté
✅ Test sérialiseur correct selon user_type
✅ Test get_concrete_user() appelé si disponible
✅ Test UUIDs convertis en strings
```

##### **UpdateProfileView** (app/authentication/views.py:239-288)
```python
✅ Test PATCH met à jour champs communs (first_name, last_name, phone, etc.)
✅ Test PATCH employee peut modifier champs spécifiques (date_of_birth, address, etc.)
✅ Test admin ne peut pas modifier champs employee
✅ Test validation erreur retourne 400
✅ Test response contient user mis à jour
```

##### **ChangePasswordView** (app/authentication/views.py:295-338)
```python
✅ Test changement mot de passe avec old_password correct
✅ Test old_password incorrect → 400
✅ Test new_password requis → 400
✅ Test new_password != confirm_password → 400
✅ Test new_password < 8 caractères → 400
✅ Test password hashé correctement (check_password)
```

---

### 3️⃣ **Core Module** (app/core/)

#### **Endpoints à tester** :
- `GET/POST/PUT/PATCH/DELETE /api/organizations/`
- `POST /api/organizations/{id}/activate/`
- `POST /api/organizations/{id}/deactivate/`
- `POST/DELETE /api/organizations/{id}/logo/`
- `GET /api/categories/`
- `GET /api/modules/`
- `GET /api/modules/defaults/`
- `GET /api/modules/active_for_user/`

#### **Tests critiques** :

##### **OrganizationViewSet** (app/core/views.py:26-214)
```python
✅ Test get_queryset() filtre par user_type (employee vs admin)
✅ Test employee voit uniquement son organisation
✅ Test admin voit ses organisations
✅ Test perform_create() assigne admin courant
✅ Test create() avec settings crée OrganizationSettings
✅ Test update() met à jour settings si fourni
✅ Test activate() action met is_active=True
✅ Test deactivate() action met is_active=False
✅ Test upload_logo() POST avec fichier valide
✅ Test upload_logo() validation type fichier (JPG/PNG/GIF/WebP/SVG uniquement)
✅ Test upload_logo() validation taille max 10MB
✅ Test upload_logo() DELETE supprime logo
✅ Test logo ancien supprimé lors upload nouveau
```

##### **ModuleViewSet** (app/core/views.py:231-346)
```python
✅ Test defaults action avec category_id valide
✅ Test defaults action avec category_name valide
✅ Test defaults action sans paramètre → 400
✅ Test defaults action avec category inexistante → 404
✅ Test by_category action groupe par catégorie
✅ Test active_for_user pour employee
✅ Test active_for_user pour admin avec organization_subdomain
✅ Test active_for_user sans organisation → liste vide
✅ Test filtrage modules actifs uniquement (is_active=True)
```

##### **OrganizationModuleViewSet** (app/core/views.py:349-421)
```python
✅ Test get_queryset() filtre par organisation utilisateur
✅ Test query param organization filtre correctement
✅ Test enable() action met is_enabled=True
✅ Test disable() action met is_enabled=False
✅ Test disable() sur module core → 400 (non autorisé)
```

---

### 4️⃣ **Inventory Module** (app/inventory/)

**⚠️ Module le plus complexe avec 19 ViewSets (4182 lignes !)**

#### **ViewSets identifiés** :
- CategoryViewSet, WarehouseViewSet, SupplierViewSet, ProductViewSet
- StockViewSet, MovementViewSet, OrderViewSet, StockCountViewSet
- StockCountItemViewSet, AlertViewSet, InventoryStatsViewSet
- CustomerViewSet, SaleViewSet, PaymentViewSet
- ExpenseCategoryViewSet, ExpenseViewSet
- ProformaInvoiceViewSet, PurchaseOrderViewSet, DeliveryNoteViewSet
- CreditSaleViewSet

#### **Tests prioritaires** :

##### **ProductViewSet** (app/inventory/views.py:249)
```python
✅ Test création produit avec organisation
✅ Test get_queryset() filtre par organisation (BaseOrganizationViewSetMixin)
✅ Test filtrage par catégorie, warehouse, supplier
✅ Test recherche textuelle (name, code, description)
✅ Test tri (par nom, prix, stock, etc.)
✅ Test validation prix >= 0
✅ Test validation stock_min <= stock_max
✅ Test gestion images produit
```

##### **StockViewSet** (app/inventory/views.py:363)
```python
✅ Test get_queryset() avec select_related optimisé
✅ Test filtrage par warehouse, product, organization
✅ Test validation quantity >= 0
✅ Test mise à jour stock met à jour last_updated
✅ Test alertes générées si stock < stock_min
```

##### **MovementViewSet** (app/inventory/views.py:390)
```python
✅ Test création mouvement IN (entrée)
✅ Test création mouvement OUT (sortie)
✅ Test création mouvement ADJUSTMENT
✅ Test mise à jour stock automatique selon movement_type
✅ Test validation quantity > 0
✅ Test validation stock suffisant pour OUT
✅ Test calcul automatic reference unique
```

##### **OrderViewSet** (app/inventory/views.py:670)
```python
✅ Test création commande avec items
✅ Test calcul total automatique
✅ Test transition statut (draft → confirmed → received)
✅ Test validation statut workflow
✅ Test génération PDF (PDFGeneratorMixin)
✅ Test mise à jour stock lors réception (received)
✅ Test annulation commande (cancelled)
```

##### **SaleViewSet** (app/inventory/views.py:3017)
```python
✅ Test création vente avec items
✅ Test calcul total, tax, discount
✅ Test génération invoice_number unique
✅ Test déduction stock lors vente
✅ Test validation stock disponible
✅ Test génération PDF facture
✅ Test statut paid vs pending
✅ Test liaison avec customer
```

##### **StockCountViewSet** (app/inventory/views.py:889)
```python
✅ Test création inventaire (stock count)
✅ Test ajout items inventaire
✅ Test calcul variance (counted vs system)
✅ Test statut workflow (in_progress → completed)
✅ Test apply_adjustments() met à jour stocks
✅ Test génération PDF rapport inventaire
✅ Test validation seul in_progress modifiable
```

##### **InventoryStatsViewSet** (app/inventory/views.py:1353)
```python
✅ Test statistiques globales (total products, low stock, etc.)
✅ Test stats par warehouse
✅ Test stats par catégorie
✅ Test valeur totale inventaire
✅ Test mouvements récents
✅ Test génération PDF rapport stats
✅ Test filtrage par période
```

---

### 5️⃣ **HR Module** (app/hr/)

#### **ViewSets identifiés** :
- EmployeeViewSet, DepartmentViewSet, PositionViewSet, ContractViewSet
- LeaveTypeViewSet, LeaveRequestViewSet, LeaveBalanceViewSet
- PayrollPeriodViewSet, PayslipViewSet, PayrollAdvanceViewSet
- PermissionViewSet, RoleViewSet, AttendanceViewSet
- HROverviewStatsView, PayrollStatsView, DepartmentStatsView

#### **Tests prioritaires** :

##### **EmployeeViewSet** (app/hr/views.py:123)
```python
✅ Test création employee avec organisation
✅ Test génération employee_number unique
✅ Test liaison avec department, position, contract
✅ Test filtrage par department, position, status
✅ Test recherche (first_name, last_name, email)
✅ Test validation email unique par organisation
✅ Test upload avatar
✅ Test désactivation employee (is_active=False)
```

##### **LeaveRequestViewSet** (app/hr/views.py:578)
```python
✅ Test création demande congé
✅ Test validation dates (start_date < end_date)
✅ Test calcul jours ouvrables automatique
✅ Test workflow statut (pending → approved/rejected)
✅ Test déduction leave_balance si approved
✅ Test validation solde suffisant
✅ Test notification manager lors demande
✅ Test génération PDF demande congé
✅ Test rejection avec motif obligatoire
```

##### **PayslipViewSet** (app/hr/views.py:1098)
```python
✅ Test création fiche de paie
✅ Test calcul salaire brut
✅ Test calcul déductions (taxes, cotisations)
✅ Test calcul net = brut - déductions
✅ Test génération payslip_number unique
✅ Test filtrage par employee, period, status
✅ Test génération PDF bulletin paie
✅ Test validation period_start < period_end
✅ Test statut workflow (draft → validated → paid)
```

##### **AttendanceViewSet** (app/hr/views.py:2544)
```python
✅ Test enregistrement check-in
✅ Test enregistrement check-out
✅ Test calcul durée automatique (check_out - check_in)
✅ Test validation check_out > check_in
✅ Test détection retard (late)
✅ Test détection absence
✅ Test un seul check-in par jour par employee
✅ Test filtrage par employee, date, status
```

##### **RoleViewSet** (app/hr/views.py:2418)
```python
✅ Test création rôle avec permissions
✅ Test assignation permissions multiples
✅ Test filtrage par organisation
✅ Test validation nom unique par organisation
✅ Test suppression rôle (vérifier employees assignés)
✅ Test mise à jour permissions
```

---

### 6️⃣ **Services Module** (app/services/)

#### **Tests critiques** :

##### **ServiceViewSet** (app/services/views.py:166)
```python
✅ Test création service avec organization
✅ Test génération reference unique
✅ Test filtrage par service_type, status, assigned_to
✅ Test filtrage parent_service (null vs ID)
✅ Test filtrage par période (start_date_from/to)
✅ Test action change_status() avec workflow
✅ Test action comments() GET et POST
✅ Test action archive() et restore()
✅ Test action statistics() (by_status, by_priority, by_type)
✅ Test création ServiceActivity lors changements
✅ Test sérialiseur différent (list vs create vs update)
```

##### **ServiceTypeViewSet** (app/services/views.py:72)
```python
✅ Test action fields() retourne champs actifs triés
✅ Test action statuses() retourne statuts actifs triés
✅ Test action templates() retourne templates actifs
✅ Test filtrage par business_profile
✅ Test validation allow_nested_services
```

##### **ServiceTemplateViewSet** (app/services/views.py:436)
```python
✅ Test action create_service() depuis template
✅ Test default_field_values appliqués
✅ Test default_title_template utilisé
✅ Test override avec request.data
```

---

### 7️⃣ **Notifications Module** (app/notifications/)

#### **Tests critiques** :

##### **NotificationViewSet** (app/notifications/views.py:61)
```python
✅ Test get_queryset() filtre par organization + recipient
✅ Test filtrage is_read (true/false)
✅ Test filtrage notification_type (alert/system/user)
✅ Test filtrage priority (low/medium/high/critical)
✅ Test recherche textuelle (title, message)
✅ Test tri (ordering: created_at, priority)
✅ Test action mark_as_read() marque une notif
✅ Test action mark_all_as_read() marque toutes
✅ Test action batch_delete() supprime par IDs
✅ Test action unread_count() retourne compteur
✅ Test action stats() (total, unread, by_type, by_priority)
✅ Test perform_create() envoie WebSocket
✅ Test perform_destroy() met à jour compteur SSE
```

##### **notification_stream (SSE)** (app/notifications/views.py:510)
```python
✅ Test authentification via token query param
✅ Test authentification via header Authorization
✅ Test sans token → 401
✅ Test résolution organisation pour employee
✅ Test résolution organisation pour admin (param org)
✅ Test organisation non trouvée → 400
✅ Test event unread_count initial envoyé
✅ Test event notification envoyé lors nouvelle notif
✅ Test event heartbeat périodique
✅ Test ping keepalive
✅ Test headers SSE (Cache-Control, X-Accel-Buffering)
✅ Mock asyncio.sleep pour tests rapides
```

---

## 🏗️ Structure de Tests Recommandée

### Organisation des fichiers :

```
app/
├── ai/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_serializers.py
│       └── test_agent.py
├── authentication/
│   └── tests/
│       ├── __init__.py
│       ├── test_login.py
│       ├── test_register.py
│       ├── test_jwt.py
│       └── test_profile.py
├── core/
│   └── tests/
│       ├── __init__.py
│       ├── test_organizations.py
│       ├── test_modules.py
│       └── test_permissions.py
├── hr/
│   └── tests/
│       ├── __init__.py
│       ├── test_employees.py
│       ├── test_leave.py
│       ├── test_payroll.py
│       └── test_attendance.py
├── inventory/
│   └── tests/
│       ├── __init__.py
│       ├── test_products.py
│       ├── test_stock.py
│       ├── test_movements.py
│       ├── test_orders.py
│       ├── test_sales.py
│       └── test_stats.py
├── services/
│   └── tests/
│       ├── __init__.py
│       ├── test_services.py
│       └── test_templates.py
└── notifications/
    └── tests/
        ├── __init__.py
        ├── test_notifications.py
        └── test_sse.py
```

---

## 🛠️ Outils et Patterns Recommandés

### **1. Fixtures communes** :

```python
# conftest.py ou base.py
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

class BaseAPITestCase(APITestCase):
    """Base classe pour tous les tests API"""

    def setUp(self):
        # Organisation de test
        self.organization = Organization.objects.create(
            name="Test Org",
            subdomain="testorg"
        )

        # Admin de test
        self.admin = AdminUser.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            first_name="Admin",
            last_name="Test"
        )

        # Employee de test
        self.employee = Employee.objects.create(
            email="employee@test.com",
            organization=self.organization,
            first_name="Employee",
            last_name="Test"
        )
        self.employee.set_password("testpass123")
        self.employee.save()

        self.client = APIClient()
```

### **2. Helpers pour authentification** :

```python
def authenticate_as_admin(self):
    """Authentifie comme admin"""
    response = self.client.post('/api/auth/login/', {
        'email': 'admin@test.com',
        'password': 'testpass123'
    })
    self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
    )

def authenticate_as_employee(self):
    """Authentifie comme employee"""
    response = self.client.post('/api/auth/login/', {
        'email': 'employee@test.com',
        'password': 'testpass123'
    })
    self.client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        HTTP_X_ORGANIZATION_SUBDOMAIN='testorg'
    )
```

### **3. Mocking pour services externes** :

```python
from unittest.mock import patch, MagicMock

class ChatViewTests(BaseAPITestCase):

    @patch('ai.agent.LouraAIAgent.chat')
    def test_chat_success(self, mock_chat):
        # Mock réponse agent
        mock_chat.return_value = {
            'content': 'Test response',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 100,
            'model': 'gpt-4'
        }

        response = self.client.post('/api/ai/chat/', {
            'message': 'Test message'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['content'], 'Test response')
```

### **4. Tests de validation** :

```python
def test_product_price_negative_invalid(self):
    """Prix négatif doit être rejeté"""
    data = {
        'name': 'Test Product',
        'price': -10.00  # Invalid
    }
    response = self.client.post('/api/inventory/products/', data)
    self.assertEqual(response.status_code, 400)
    self.assertIn('price', response.data)
```

### **5. Tests de permissions** :

```python
def test_employee_cannot_delete_organization(self):
    """Employee ne peut pas supprimer organisation"""
    self.authenticate_as_employee()
    response = self.client.delete(f'/api/organizations/{self.organization.id}/')
    self.assertEqual(response.status_code, 403)
```

---

## 📈 Métriques de Couverture Recommandées

### **Priorité 1 (Critique)** :
- **Authentication** : 95%+ (sécurité critique)
- **Inventory Sales/Payments** : 90%+ (transactions financières)
- **HR Payroll** : 90%+ (calculs salaires)

### **Priorité 2 (Important)** :
- **AI Chat** : 85%+ (fonctionnalité clé)
- **Inventory Stock/Movements** : 85%+ (intégrité données)
- **Services** : 80%+ (business logic)

### **Priorité 3 (Standard)** :
- **Notifications** : 75%+
- **Core Organizations** : 75%+
- **HR Leave/Attendance** : 75%+

---

## 🚀 Plan d'Implémentation Suggéré

### **Phase 1 (2-3 semaines)** :
1. Tests Authentication (login, register, JWT)
2. Tests Core Organizations + Modules
3. Tests Inventory Products + Stock

### **Phase 2 (2-3 semaines)** :
4. Tests Inventory Sales + Payments
5. Tests HR Employees + Leave
6. Tests AI Chat (non-streaming)

### **Phase 3 (2 semaines)** :
7. Tests Services
8. Tests Notifications
9. Tests HR Payroll

### **Phase 4 (1-2 semaines)** :
10. Tests avancés (SSE, streaming, PDF generation)
11. Tests d'intégration
12. Tests de performance

---

## ⚡ Commandes Utiles

```bash
# Exécuter tous les tests
python manage.py test

# Exécuter tests d'une app
python manage.py test ai
python manage.py test authentication

# Avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère rapport HTML

# Tests spécifiques
python manage.py test ai.tests.test_views.ChatViewTests
python manage.py test ai.tests.test_views.ChatViewTests.test_chat_success

# Tests en parallèle (plus rapide)
python manage.py test --parallel

# Tests avec verbose
python manage.py test --verbosity=2

# Conserver la base de données de test
python manage.py test --keepdb
```

---

## 📊 Tableau Récapitulatif des Endpoints

| Module | Nombre de ViewSets | Endpoints principaux | Priorité |
|--------|-------------------|---------------------|----------|
| **Inventory** | 19 | Products, Stock, Sales, Orders | 🔴 Critique |
| **HR** | 17 | Employees, Leave, Payroll, Attendance | 🔴 Critique |
| **Services** | 8 | Services, Types, Templates | 🟡 Moyenne |
| **AI** | 4 | Chat, Conversations, Tools | 🟢 Importante |
| **Authentication** | 7 | Login, Register, Profile | 🔴 Critique |
| **Core** | 4 | Organizations, Modules | 🟢 Importante |
| **Notifications** | 2 | Notifications, SSE Stream | 🟡 Moyenne |

---

## 🎯 Tests à Impact Maximum (Quick Wins)

Ces tests offrent le meilleur retour sur investissement :

1. **Authentication Login/Register** (2-3 jours)
   - Sécurise l'accès à toute l'application
   - Couvre ~30% du risque sécurité

2. **Inventory Sales** (3-4 jours)
   - Protège les transactions financières
   - Évite les bugs de calcul de prix/TVA

3. **HR Payroll** (3-4 jours)
   - Crucial pour conformité légale
   - Évite erreurs de calcul salaires

4. **Stock Movements** (2-3 jours)
   - Garantit intégrité des stocks
   - Évite survente/ruptures

5. **AI Chat** (2-3 jours)
   - Fonctionnalité différenciante
   - Expérience utilisateur clé

**Total Quick Wins : 12-17 jours pour 70% de couverture des risques critiques**

---

## 🔧 Configuration pytest (Optionnel mais recommandé)

```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = lourabackend.settings
python_files = tests.py test_*.py *_tests.py
addopts =
    --reuse-db
    --nomigrations
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --maxfail=5
    -v
```

```bash
# Installation
pip install pytest pytest-django pytest-cov

# Exécution
pytest
pytest app/ai/tests/
pytest -k "test_login"
```

---

## 🎓 Résumé Exécutif

**Total endpoints identifiés** : ~150+
**ViewSets identifiés** : ~61
**Applications** : 7
**Tests actuels** : 0 (fichiers vides)

**Estimation effort** : 6-8 semaines pour couverture 80%+

**Tests les plus critiques** :
1. **Authentication** (sécurité)
2. **Inventory Sales** (finances)
3. **HR Payroll** (légal)
4. **Stock Movements** (intégrité)
5. **AI Chat** (UX clé)

**ROI maximum** : Commencer par Authentication + Inventory, qui concentrent la logique business critique.

---

## 📞 Prochaines Étapes Recommandées

1. ✅ Valider ce rapport avec l'équipe
2. ✅ Prioriser les modules selon les objectifs business
3. ✅ Créer la structure de dossiers `tests/`
4. ✅ Implémenter les fixtures communes (BaseAPITestCase)
5. ✅ Commencer par Phase 1 (Authentication + Core)
6. ✅ Mettre en place CI/CD avec exécution automatique des tests
7. ✅ Définir objectifs de couverture par sprint

**Bonne chance pour l'implémentation des tests ! 🚀**
