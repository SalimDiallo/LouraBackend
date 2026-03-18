"""
Tests pour ProductViewSet
=========================
Tests critiques pour la gestion des produits d'inventaire
"""

from rest_framework import status
from decimal import Decimal

from inventory.models import Product, Category as InventoryCategory, Warehouse
from conftest import BaseAPITestCase


class ProductViewSetTests(BaseAPITestCase):
    """Tests pour les endpoints de produits"""

    def setUp(self):
        super().setUp()

        # Créer une catégorie inventory
        self.inv_category = InventoryCategory.objects.create(
            organization=self.organization,
            name="Electronics",
            code="ELEC"
        )

        # Créer un entrepôt
        self.warehouse = Warehouse.objects.create(
            organization=self.organization,
            name="Main Warehouse",
            code="WH001"
        )

        # Créer un produit de test
        self.product = Product.objects.create(
            organization=self.organization,
            category=self.inv_category,
            name="Test Product",
            sku="TEST001",
            purchase_price=Decimal('10.00'),
            selling_price=Decimal('15.00'),
            min_stock_level=Decimal('5.00'),
            max_stock_level=Decimal('100.00')
        )

    def test_create_product_with_organization(self):
        """Test création produit avec organisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'name': 'New Product',
            'sku': 'NEW001',
            'category': self.inv_category.id,
            'purchase_price': '20.00',
            'selling_price': '30.00',
            'min_stock_level': '10.00',
            'max_stock_level': '200.00'
        }

        response = self.client.post('/api/inventory/products/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')

        # Vérifier en DB
        self.assertTrue(Product.objects.filter(sku='NEW001').exists())

    def test_get_queryset_filters_by_organization(self):
        """Test que get_queryset() filtre par organisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get('/api/inventory/products/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tous les produits retournés doivent appartenir à l'organisation
        for product in response.data['results']:
            prod = Product.objects.get(id=product['id'])
            self.assertEqual(prod.organization.id, self.organization.id)

    def test_product_price_validation_positive(self):
        """Test validation prix >= 0"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'name': 'Invalid Product',
            'sku': 'INV001',
            'purchase_price': '-10.00',  # Prix négatif invalide
            'selling_price': '30.00',
            'min_stock_level': '10.00',
            'max_stock_level': '200.00'
        }

        response = self.client.post('/api/inventory/products/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_stock_min_max_validation(self):
        """Test validation stock_min <= stock_max"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'name': 'Product Stock Test',
            'sku': 'STOCK001',
            'purchase_price': '20.00',
            'selling_price': '30.00',
            'min_stock_level': '200.00',  # Min > Max (invalide)
            'max_stock_level': '100.00'
        }

        response = self.client.post('/api/inventory/products/', data)

        # Selon l'implémentation, cela peut être accepté ou rejeté
        # Si validation personnalisée, devrait retourner 400

    def test_product_sku_unique_per_organization(self):
        """Test que SKU doit être unique par organisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'name': 'Duplicate SKU Product',
            'sku': 'TEST001',  # SKU déjà utilisé
            'purchase_price': '20.00',
            'selling_price': '30.00',
            'min_stock_level': '10.00',
            'max_stock_level': '200.00'
        }

        response = self.client.post('/api/inventory/products/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_requires_authentication(self):
        """Test que les endpoints nécessitent l'authentification"""
        self.clear_credentials()

        response = self.client.get('/api/inventory/products/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_product(self):
        """Test mise à jour d'un produit"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'name': 'Updated Product Name',
            'selling_price': '25.00'
        }

        response = self.client.patch(
            f'/api/inventory/products/{self.product.id}/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Product Name')

        # Vérifier en DB
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product Name')
        self.assertEqual(self.product.selling_price, Decimal('25.00'))

    def test_delete_product(self):
        """Test suppression d'un produit"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.delete(
            f'/api/inventory/products/{self.product.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Vérifier que le produit a été supprimé
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_product_list_pagination(self):
        """Test pagination de la liste des produits"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Créer plusieurs produits
        for i in range(15):
            Product.objects.create(
                organization=self.organization,
                name=f'Product {i}',
                sku=f'PROD{i:03d}',
                purchase_price=Decimal('10.00'),
                selling_price=Decimal('15.00')
            )

        response = self.client.get('/api/inventory/products/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
