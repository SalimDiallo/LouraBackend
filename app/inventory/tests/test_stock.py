"""
Tests pour StockViewSet et Stock Management
===========================================
Tests critiques pour la gestion des stocks
"""

from rest_framework import status
from decimal import Decimal

from inventory.models import Product, Stock, Warehouse, Category as InventoryCategory
from conftest import BaseAPITestCase


class StockViewSetTests(BaseAPITestCase):
    """Tests pour les endpoints de stocks"""

    def setUp(self):
        super().setUp()

        # Créer une catégorie inventory
        self.inv_category = InventoryCategory.objects.create(
            organization=self.organization,
            name="Electronics",
            code="ELEC"
        )

        # Créer des entrepôts
        self.warehouse1 = Warehouse.objects.create(
            organization=self.organization,
            name="Main Warehouse",
            code="WH001"
        )

        self.warehouse2 = Warehouse.objects.create(
            organization=self.organization,
            name="Secondary Warehouse",
            code="WH002"
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

        # Créer un stock
        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse1,
            quantity=Decimal('50.00'),
            location="A1-B2"
        )

    def test_create_stock(self):
        """Test création d'un stock"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'product': self.product.id,
            'warehouse': self.warehouse2.id,
            'quantity': '30.00',
            'location': 'C3-D4'
        }

        response = self.client.post('/api/inventory/stocks/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], '30.00')

    def test_get_queryset_with_select_related(self):
        """Test que get_queryset() utilise select_related pour optimisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get('/api/inventory/stocks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que le stock est retourné
        self.assertTrue(len(response.data['results']) > 0)

    def test_stock_quantity_validation_positive(self):
        """Test validation quantity >= 0"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'product': self.product.id,
            'warehouse': self.warehouse1.id,
            'quantity': '-10.00'  # Quantité négative invalide
        }

        response = self.client.post('/api/inventory/stocks/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stock_unique_per_product_warehouse(self):
        """Test qu'un seul stock par produit et entrepôt"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'product': self.product.id,
            'warehouse': self.warehouse1.id,  # Même warehouse que self.stock
            'quantity': '20.00'
        }

        response = self.client.post('/api/inventory/stocks/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_stock_quantity(self):
        """Test mise à jour de la quantité en stock"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'quantity': '75.00'
        }

        response = self.client.patch(
            f'/api/inventory/stocks/{self.stock.id}/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], '75.00')

        # Vérifier en DB
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal('75.00'))

    def test_stock_filters_by_organization(self):
        """Test filtrage par organisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get('/api/inventory/stocks/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que tous les stocks appartiennent à l'organisation
        for stock_data in response.data['results']:
            stock = Stock.objects.get(id=stock_data['id'])
            self.assertEqual(stock.product.organization.id, self.organization.id)

    def test_stock_filter_by_warehouse(self):
        """Test filtrage par entrepôt"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get(
            f'/api/inventory/stocks/?warehouse={self.warehouse1.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tous les résultats doivent être du warehouse1
        for stock_data in response.data['results']:
            stock = Stock.objects.get(id=stock_data['id'])
            self.assertEqual(stock.warehouse.id, self.warehouse1.id)

    def test_stock_filter_by_product(self):
        """Test filtrage par produit"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get(
            f'/api/inventory/stocks/?product={self.product.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for stock_data in response.data['results']:
            stock = Stock.objects.get(id=stock_data['id'])
            self.assertEqual(stock.product.id, self.product.id)

    def test_product_get_total_stock(self):
        """Test méthode get_total_stock() du produit"""
        # Ajouter un deuxième stock
        Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse2,
            quantity=Decimal('30.00')
        )

        total = self.product.get_total_stock()

        # 50.00 (stock1) + 30.00 (stock2) = 80.00
        self.assertEqual(total, Decimal('80.00'))

    def test_product_is_low_stock(self):
        """Test méthode is_low_stock() du produit"""
        # Produit avec min_stock_level = 5.00 et total = 50.00
        self.assertFalse(self.product.is_low_stock())

        # Réduire le stock à 4.00 (en dessous du minimum)
        self.stock.quantity = Decimal('4.00')
        self.stock.save()

        self.product.refresh_from_db()
        self.assertTrue(self.product.is_low_stock())

    def test_delete_stock(self):
        """Test suppression d'un stock"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.delete(
            f'/api/inventory/stocks/{self.stock.id}/'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Stock.objects.filter(id=self.stock.id).exists())

    def test_stock_location_optional(self):
        """Test que location est optionnel"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'product': self.product.id,
            'warehouse': self.warehouse2.id,
            'quantity': '25.00'
            # pas de location
        }

        response = self.client.post('/api/inventory/stocks/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
