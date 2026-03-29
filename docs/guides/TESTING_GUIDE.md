# Testing Guide - Loura Backend

## Structure des tests

```
app/
├── inventory/
│   └── tests/
│       ├── __init__.py
│       ├── test_products.py
│       ├── test_stock.py
│       ├── test_movements.py
│       ├── test_orders.py
│       ├── test_sales.py
│       └── test_stats.py
├── hr/
│   └── tests.py
└── core/
    └── tests.py
```

**Total** : ~34 fichiers de tests

---

## Tests existants

### Inventory Tests

**Fichier** : `app/inventory/tests/`

1. **test_products.py** : Tests des produits
2. **test_stock.py** : Tests du stock
3. **test_movements.py** : Tests des mouvements
4. **test_orders.py** : Tests des commandes
5. **test_sales.py** : Tests des ventes
6. **test_stats.py** : Tests des statistiques

---

### HR Tests

**Fichier** : `app/hr/tests.py`

Tests pour :
- Employees
- Contracts
- Leave requests
- Payroll
- Attendance

---

## Coverage actuel

**Estimation** : ~20% de couverture

**Fichiers couverts** :
- ✅ Inventory (partiel)
- ✅ HR (partiel)
- ❌ Core (non testé)
- ❌ Authentication (non testé)
- ❌ Notifications (non testé)
- ❌ AI (non testé)

---

## Lancer les tests

### Tous les tests

```bash
cd app
python manage.py test
```

---

### Tests d'une application

```bash
python manage.py test inventory
python manage.py test hr
```

---

### Tests d'un fichier

```bash
python manage.py test inventory.tests.test_products
```

---

### Test spécifique

```bash
python manage.py test inventory.tests.test_products.ProductTestCase.test_create_product
```

---

### Avec verbosity

```bash
python manage.py test --verbosity=2
```

---

## Écrire de nouveaux tests

### Structure de base

```python
# app/myapp/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Organization
from .models import MyModel

User = get_user_model()

class MyModelTestCase(TestCase):
    def setUp(self):
        """Exécuté avant chaque test."""
        # Créer organisation
        self.organization = Organization.objects.create(
            name="Test Org",
            subdomain="testorg"
        )

        # Créer utilisateur admin
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="password123"
        )
        self.organization.admin = self.admin
        self.organization.save()

    def test_create_model(self):
        """Test de création."""
        obj = MyModel.objects.create(
            organization=self.organization,
            name="Test"
        )
        self.assertEqual(obj.name, "Test")
        self.assertEqual(obj.organization, self.organization)

    def test_model_str(self):
        """Test __str__."""
        obj = MyModel.objects.create(
            organization=self.organization,
            name="Test"
        )
        self.assertEqual(str(obj), "Test")

    def tearDown(self):
        """Exécuté après chaque test (optionnel)."""
        pass
```

---

### Tests d'API (ViewSet)

```python
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class MyModelAPITestCase(APITestCase):
    def setUp(self):
        # Créer organisation et user
        self.organization = Organization.objects.create(...)
        self.admin = User.objects.create_user(...)

        # Authentifier
        self.client.force_authenticate(user=self.admin)

    def test_list_models(self):
        """Test GET /api/myapp/models/"""
        url = reverse('mymodel-list')  # Nom de la route DRF
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_model(self):
        """Test POST /api/myapp/models/"""
        url = reverse('mymodel-list')
        data = {
            'organization': str(self.organization.id),
            'name': 'Test',
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test')

    def test_update_model(self):
        """Test PUT /api/myapp/models/{id}/"""
        obj = MyModel.objects.create(...)
        url = reverse('mymodel-detail', args=[obj.id])
        data = {'name': 'Updated'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj.refresh_from_db()
        self.assertEqual(obj.name, 'Updated')

    def test_delete_model(self):
        """Test DELETE /api/myapp/models/{id}/"""
        obj = MyModel.objects.create(...)
        url = reverse('mymodel-detail', args=[obj.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MyModel.objects.filter(id=obj.id).exists())
```

---

### Tests de permissions

```python
def test_unauthorized_access(self):
    """Test accès sans authentification."""
    self.client.force_authenticate(user=None)
    url = reverse('mymodel-list')
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

def test_permission_denied(self):
    """Test accès avec mauvaises permissions."""
    # Créer employee sans permission
    employee = Employee.objects.create(...)
    self.client.force_authenticate(user=employee)

    url = reverse('mymodel-list')
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

---

### Factories (à implémenter)

```python
# app/myapp/factories.py

import factory
from .models import MyModel

class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Organization {n}")
    subdomain = factory.Sequence(lambda n: f"org{n}")

class MyModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MyModel

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('name')

# Usage dans tests
def test_with_factory(self):
    obj = MyModelFactory.create()
    self.assertIsNotNone(obj.organization)
```

---

## Best Practices

### 1. Isolation des tests

✅ **Chaque test doit être indépendant**
✅ **Utiliser setUp() pour données de test**
✅ **Utiliser tearDown() pour cleanup (si nécessaire)**
❌ **Ne pas dépendre de l'ordre d'exécution**

---

### 2. Nommage

✅ **test_action_expected_result**
  - `test_create_product_success`
  - `test_update_product_unauthorized`
  - `test_delete_product_not_found`

---

### 3. Assertions claires

```python
# ✅ Bon
self.assertEqual(product.name, "Laptop")
self.assertTrue(product.is_active)
self.assertIn('results', response.data)

# ❌ Mauvais
self.assertTrue(product.name == "Laptop")  # Moins lisible
```

---

### 4. Tests de cas limites

```python
def test_create_product_negative_price(self):
    """Test avec prix négatif (invalide)."""
    data = {'purchase_price': -100}
    response = self.client.post(url, data)
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

def test_create_product_empty_name(self):
    """Test avec nom vide."""
    data = {'name': ''}
    response = self.client.post(url, data)
    self.assertIn('name', response.data)
```

---

## CI/CD (à configurer)

### GitHub Actions

**Fichier** : `.github/workflows/django-tests.yml`

```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        env:
          DB_ENGINE: django.db.backends.postgresql
          DB_NAME: test_db
          DB_USER: test_user
          DB_PASSWORD: test_pass
          DB_HOST: localhost
          DB_PORT: 5432
        run: |
          python app/manage.py test --verbosity=2
```

---

## Coverage Report

### Installation

```bash
pip install coverage
```

---

### Lancer avec coverage

```bash
# Run tests avec coverage
coverage run --source='app' app/manage.py test

# Générer rapport console
coverage report

# Générer rapport HTML
coverage html
```

**Voir** : `htmlcov/index.html`

---

## Références

- **Django Testing** : https://docs.djangoproject.com/en/5.2/topics/testing/
- **DRF Testing** : https://www.django-rest-framework.org/api-guide/testing/
- **Factory Boy** : https://factoryboy.readthedocs.io/

---

**Objectif** : Atteindre 80%+ de couverture avant production.
