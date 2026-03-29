# API Guide - Loura Backend

## Introduction

Ce guide couvre l'utilisation des APIs REST de Loura Backend.

**Base URL** : `http://localhost:8000/api/`
**Production** : `https://your-domain.com/api/`

---

## Authentification JWT

### 1. Login

**POST** `/api/auth/login/`

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```

**Response 200** :
```json
{
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "admin"
  },
  "user_type": "admin",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Connexion réussie"
}
```

**Cookies HttpOnly** :
- `access_token` (15 min)
- `refresh_token` (7 jours)

---

### 2. Refresh Token

**POST** `/api/auth/refresh/`

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  --cookie "refresh_token=eyJ0eXAiOiJKV1Q..."
```

**Response 200** :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Token rafraîchi"
}
```

---

### 3. Logout

**POST** `/api/auth/logout/`

```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  --cookie "refresh_token=eyJ0eXAiOiJKV1Q..."
```

---

### 4. Current User

**GET** `/api/auth/me/`

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  --cookie "access_token=eyJ0eXAiOiJKV1Q..."
```

---

## Format des requêtes

### Headers requis

```http
Content-Type: application/json
Authorization: Bearer <access_token>  # Ou cookie automatique
X-Organization-Subdomain: org-slug    # Pour filtrage multi-tenant
```

### Authentification

**Option 1 : Cookie HttpOnly (recommandé)**
```bash
curl --cookie "access_token=eyJ0eXAiOiJKV1Q..."
```

**Option 2 : Bearer Token**
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..."
```

---

## Pagination

Toutes les listes sont paginées (10 résultats par défaut).

**Response** :
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/hr/employees/?page=2",
  "previous": null,
  "results": [...]
}
```

**Query params** :
- `?page=2` : Page suivante
- `?page_size=50` : Nombre de résultats (max 100)

---

## Filtrage

Utiliser `django-filter` pour filtres avancés :

```bash
# Filtrer par statut
GET /api/hr/employees/?employment_status=active

# Filtrer par date
GET /api/inventory/sales/?sale_date__gte=2025-01-01

# Recherche
GET /api/inventory/products/?search=laptop

# Tri
GET /api/hr/employees/?ordering=-created_at
```

---

## Exemples d'endpoints

### Employees (HR)

**GET** `/api/hr/employees/`
```bash
curl http://localhost:8000/api/hr/employees/ \
  --cookie "access_token=..."
```

**POST** `/api/hr/employees/`
```json
{
  "email": "employee@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "organization": "uuid",
  "department": "uuid",
  "position": "uuid",
  "hire_date": "2025-01-15"
}
```

**PUT** `/api/hr/employees/{id}/`
**DELETE** `/api/hr/employees/{id}/`

---

### Products (Inventory)

**GET** `/api/inventory/products/`
**POST** `/api/inventory/products/`
```json
{
  "organization": "uuid",
  "category": "uuid",
  "name": "Laptop HP",
  "sku": "LAP-001",
  "purchase_price": 500.00,
  "selling_price": 750.00,
  "unit": "unit",
  "min_stock_level": 5
}
```

---

### Sales (Inventory)

**POST** `/api/inventory/sales/`
```json
{
  "organization": "uuid",
  "customer": "uuid",
  "warehouse": "uuid",
  "sale_number": "SALE-2025-001",
  "items": [
    {
      "product": "uuid",
      "quantity": 2,
      "unit_price": 750.00,
      "discount_value": 10.00,
      "discount_type": "fixed"
    }
  ],
  "payment_method": "cash",
  "paid_amount": 1490.00
}
```

---

## Gestion des erreurs

### Erreurs communes

**400 Bad Request**
```json
{
  "detail": "Invalid data",
  "errors": {
    "email": ["This field is required."],
    "password": ["Password too short."]
  }
}
```

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error"
}
```

---

## Best Practices

1. **Toujours utiliser HTTPS en production**
2. **Refresh le token avant expiration (13-14 min)**
3. **Gérer les erreurs 401 (redirect vers login)**
4. **Filtrer par organization pour isolation**
5. **Utiliser pagination pour grandes listes**
6. **Valider les données côté client avant envoi**

---

**Voir** : `/docs/api/ENDPOINTS.md` pour la liste complète des endpoints.
