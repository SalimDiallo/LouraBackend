# 🧪 GUIDE DES TESTS API - LOURA BACKEND

**Date de mise à jour:** 2025-11-28
**Fichiers de test:** `test_core_endpoints.http`, `test_hr_endpoints.http`

---

## 📋 MODIFICATIONS RÉCENTES

### ✅ Corrections appliquées

Les fichiers de test ont été mis à jour pour refléter les corrections suivantes :

#### 1. **Types de contrats (Contract)**
**Anciens codes (INVALIDES):**
- ❌ `cdi`
- ❌ `cdd`
- ❌ `stage`
- ❌ `apprenticeship`

**Nouveaux codes (VALIDES):**
- ✅ `permanent` - CDI - Contrat à Durée Indéterminée
- ✅ `temporary` - CDD - Contrat à Durée Déterminée
- ✅ `contract` - Contractuel
- ✅ `internship` - Stage
- ✅ `freelance` - Freelance/Consultant

#### 2. **Système de rôles (Employee)**
**Ancien système (INVALIDE):**
```json
{
  "role": "admin"  // ❌ Champ string direct (n'existe plus)
}
```

**Nouveau système (VALIDE):**
```json
{
  "role_id": "{role_id}",  // ✅ ID du rôle assigné
  "custom_permission_codes": [  // ✅ Permissions supplémentaires optionnelles
    "hr.view_payslip",
    "hr.view_contract"
  ]
}
```

#### 3. **Nouveaux champs Employee**
Les champs suivants ont été ajoutés au modèle Employee :

```json
{
  "phone": "+224620123456",
  "date_of_birth": "1990-05-15",
  "gender": "male",  // Valeurs: male, female, other
  "address": "123 Avenue de la République",
  "city": "Conakry",
  "country": "GN",  // Code pays ISO 3166-1 alpha-2
  "avatar_url": "https://example.com/avatars/employee.jpg"
}
```

---

## 📖 GUIDE D'UTILISATION

### Prérequis

1. **Backend démarré:**
   ```bash
   cd backend/app
   source ../venv/bin/activate
   python manage.py runserver
   ```

2. **Extension HTTP client:**
   - VS Code: REST Client extension
   - JetBrains: HTTP Client intégré
   - Postman: Importer les fichiers .http

### Variables d'environnement

Configurez ces variables en haut de chaque fichier `.http` :

```http
@baseUrl = http://localhost:8000/api/hr
@coreUrl = http://localhost:8000/api/core
@employeeEmail = employee@loura.com
@employeePassword = Employee123!
@subdomain = louradesing
@accessToken = YOUR_ACCESS_TOKEN
@refreshToken = YOUR_REFRESH_TOKEN
@employeeId = YOUR_EMPLOYEE_ID
@organizationId = YOUR_ORGANIZATION_ID
```

---

## 🔐 SYSTÈME D'AUTHENTIFICATION

### Deux systèmes séparés

#### 1. **AdminUser (Core App)**
- **Endpoints:** `/api/core/auth/`
- **Login:** `POST /api/core/auth/login/`
- **Utilisé pour:** Créer et gérer les organisations, employés, départements

#### 2. **Employee (HR App)**
- **Endpoints:** `/api/hr/auth/`
- **Login:** `POST /api/hr/auth/login/`
- **Requiert:** email + password + subdomain organisation
- **Utilisé pour:** Accès employé aux fonctionnalités RH

### Workflow d'authentification

```http
### 1. Se connecter en tant qu'AdminUser
POST {{coreUrl}}/auth/login/
Content-Type: application/json

{
  "email": "admin@loura.com",
  "password": "Admin123!"
}

### 2. Créer une organisation
POST {{coreUrl}}/organizations/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "name": "Ma Société",
  "subdomain": "masociete"
}

### 3. Créer un employé
POST {{baseUrl}}/employees/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "email": "employee@company.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Jean",
  "last_name": "Dupont",
  "organization": "{{organizationId}}"
}

### 4. Se connecter en tant qu'Employee
POST {{baseUrl}}/auth/login/
Content-Type: application/json

{
  "email": "employee@company.com",
  "password": "SecurePass123!",
  "organization_subdomain": "masociete"
}
```

---

## 🎭 SYSTÈME DE RÔLES & PERMISSIONS

### Architecture

```
Permission (granulaire)
    ↓
Role (groupe de permissions)
    ↓
Employee (assigned_role + custom_permissions)
```

### Rôles système prédéfinis

| Code | Nom | Description |
|------|-----|-------------|
| `super_admin` | Super Administrateur | Accès total au système |
| `hr_admin` | Administrateur RH | Gestion complète du module HR |
| `manager` | Manager | Gestion d'équipe + approbation congés |

### Créer un rôle personnalisé

```http
POST {{baseUrl}}/roles/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "code": "hr_specialist",
  "name": "Spécialiste RH",
  "description": "Accès RH sans administration",
  "permission_codes": [
    "hr.view_employee",
    "hr.add_employee",
    "hr.change_employee",
    "hr.view_department",
    "hr.view_leaverequest",
    "hr.approve_leaverequest"
  ],
  "is_active": true
}
```

### Attribuer un rôle

```http
PATCH {{baseUrl}}/employees/{{employeeId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "role_id": "{role_id}"
}
```

### Ajouter des permissions personnalisées

```http
PATCH {{baseUrl}}/employees/{{employeeId}}/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "custom_permission_codes": [
    "hr.view_payslip",
    "hr.delete_contract"
  ]
}
```

### Vérifier les permissions (backend)

```python
# Dans le code backend
if employee.has_permission('hr.view_employee'):
    # Autoriser l'action
    pass

# Obtenir toutes les permissions
permissions = employee.get_all_permissions()

# Vérifier si HR Admin
if employee.is_hr_admin():
    # Actions administrateur RH
    pass
```

---

## 📝 TESTS COURANTS

### 1. Workflow Onboarding Complet

```http
### Étape 1: AdminUser crée un département
POST {{baseUrl}}/departments/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "name": "Développement",
  "code": "DEV",
  "organization": "{{organizationId}}"
}

### Étape 2: Créer un poste
POST {{baseUrl}}/positions/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "title": "Développeur Full Stack",
  "code": "DEV-FS",
  "min_salary": 50000,
  "max_salary": 80000,
  "organization": "{{organizationId}}"
}

### Étape 3: Créer l'employé avec tous les champs
POST {{baseUrl}}/employees/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "email": "dev@company.com",
  "password": "DevPass123!",
  "password_confirm": "DevPass123!",
  "first_name": "Marie",
  "last_name": "Durand",
  "phone": "+224620123456",
  "date_of_birth": "1995-03-20",
  "gender": "female",
  "employee_id": "DEV001",
  "department": "{department_id}",
  "position": "{position_id}",
  "hire_date": "2025-01-15",
  "employment_status": "active"
}

### Étape 4: Créer le contrat
POST {{baseUrl}}/contracts/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "employee": "{{employeeId}}",
  "contract_type": "permanent",
  "start_date": "2025-01-15",
  "base_salary": 65000,
  "currency": "GNF",
  "salary_period": "monthly",
  "hours_per_week": 40
}
```

### 2. Workflow Demande de Congé

```http
### Étape 1: Employee consulte ses soldes
GET {{baseUrl}}/leave-balances/
Authorization: Bearer {{accessToken}}

### Étape 2: Employee crée une demande
POST {{baseUrl}}/leave-requests/
Authorization: Bearer {{accessToken}}
Content-Type: application/json

{
  "leave_type": "{leave_type_id}",
  "start_date": "2025-12-20",
  "end_date": "2025-12-31",
  "total_days": 10,
  "reason": "Congés de fin d'année"
}

### Étape 3: Manager approuve
POST {{baseUrl}}/leave-requests/{id}/approve/
Authorization: Bearer {{managerAccessToken}}
Content-Type: application/json

{
  "approval_notes": "Approuvé"
}
```

### 3. Test des Permissions

```http
### Employé standard essaie de créer un département (DEVRAIT ÉCHOUER)
POST {{baseUrl}}/departments/
Authorization: Bearer {{employeeAccessToken}}
Content-Type: application/json

{
  "name": "Test",
  "code": "TST"
}
# Attendu: 403 Forbidden

### HR Admin crée un département (DEVRAIT RÉUSSIR)
POST {{baseUrl}}/departments/
Authorization: Bearer {{hrAdminAccessToken}}
Content-Type: application/json

{
  "name": "Marketing",
  "code": "MKT"
}
# Attendu: 201 Created
```

---

## ⚠️ ERREURS COURANTES

### 1. Token expiré
**Erreur:** `401 Unauthorized`
**Solution:** Utiliser l'endpoint refresh pour obtenir un nouveau token

```http
POST {{coreUrl}}/auth/refresh/
Content-Type: application/json

{
  "refresh": "{{refreshToken}}"
}
```

### 2. Mauvais type de contrat
**Erreur:** `400 Bad Request - Invalid contract_type`
**Solution:** Utiliser les nouveaux codes: `permanent`, `temporary`, `contract`, `internship`, `freelance`

### 3. Tentative d'utilisation du champ `role`
**Erreur:** `400 Bad Request - Unknown field: role`
**Solution:** Utiliser `role_id` au lieu de `role`

### 4. Permission refusée
**Erreur:** `403 Forbidden`
**Causes possibles:**
- Employé sans le rôle approprié
- Tentative d'accès à une ressource d'une autre organisation
- Permission spécifique manquante

**Solution:** Vérifier le rôle et les permissions de l'employé

---

## 🔍 DÉBOGAGE

### Afficher les permissions d'un employé

```http
GET {{baseUrl}}/employees/{{employeeId}}/
Authorization: Bearer {{accessToken}}
```

Réponse incluant:
```json
{
  "role": {
    "code": "hr_admin",
    "name": "Administrateur RH",
    "permissions": [...]
  },
  "all_permissions": [...],  // Role + custom
  "custom_permissions": [...]  // Seulement custom
}
```

### Lister toutes les permissions disponibles

```http
GET {{baseUrl}}/permissions/
Authorization: Bearer {{accessToken}}
```

### Vérifier l'isolation multi-tenant

Connectez-vous avec deux employés de différentes organisations et vérifiez qu'ils ne voient que leurs propres données :

```http
### Employee Org A
GET {{baseUrl}}/employees/
Authorization: Bearer {{orgAToken}}

### Employee Org B
GET {{baseUrl}}/employees/
Authorization: Bearer {{orgBToken}}
```

Les résultats doivent être différents et limités à chaque organisation.

---

## 📚 RESSOURCES

- **Documentation backend:** `/backend/app/CLAUDE.md`
- **Architecture:** `/backend/app/ARCHITECTURE.md`
- **Corrections appliquées:** `/CORRECTIONS_APPLIED.md`
- **Code source permissions:** `/backend/app/hr/permissions.py`
- **Code source modèles:** `/backend/app/hr/models.py`

---

## 🎯 CHECKLIST AVANT TESTS

- [ ] Backend démarré (`python manage.py runserver`)
- [ ] Base de données migrée (`python manage.py migrate`)
- [ ] Variables configurées dans le fichier .http
- [ ] AdminUser créé (via shell ou API)
- [ ] Organisation créée
- [ ] Tokens valides (non expirés)
- [ ] Rôles système initialisés (via `python manage.py init_permissions`)

---

**Dernière mise à jour:** 2025-11-28
**Version:** 2.0 (après corrections de sécurité)
