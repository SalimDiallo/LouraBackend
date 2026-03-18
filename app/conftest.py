"""
Configuration commune pour tous les tests
==========================================
Fixtures partagees et classe de base pour les tests API
"""

from rest_framework.test import APIClient, APITestCase
from core.models import AdminUser, Organization, Category
from hr.models import Employee


class BaseAPITestCase(APITestCase):
    """
    Classe de base pour tous les tests API.
    Contient les fixtures communes : organization, admin, employee, client
    """

    @classmethod
    def setUpTestData(cls):
        """Données partagées pour tous les tests de la classe"""
        # Créer une catégorie
        cls.category = Category.objects.create(
            name="Commerce",
            description="Catégorie commerce de détail"
        )

    def setUp(self):
        """Configuration avant chaque test"""
        # Client API
        self.client = APIClient()

        # Admin de test
        self.admin = AdminUser.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            first_name="Admin",
            last_name="Test",
            phone="+224620000000"
        )

        # Organisation de test
        self.organization = Organization.objects.create(
            name="Test Organization",
            subdomain="testorg",
            admin=self.admin,
            category=self.category
        )

        # Employee de test
        self.employee = Employee.objects.create_user(
            email="employee@test.com",
            password="testpass123",
            organization=self.organization,
            first_name="Employee",
            last_name="Test",
            phone="+224620000001",
            employee_id="EMP001"
        )

        # Données de test réutilisables
        self.admin_credentials = {
            'email': 'admin@test.com',
            'password': 'testpass123'
        }

        self.employee_credentials = {
            'email': 'employee@test.com',
            'password': 'testpass123'
        }

    def authenticate_as_admin(self):
        """Authentifie le client comme admin et retourne les tokens"""
        response = self.client.post('/api/auth/login/', self.admin_credentials)
        if response.status_code == 200:
            token = response.data.get('access')
            self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            return response.data
        return None

    def authenticate_as_employee(self):
        """Authentifie le client comme employee et retourne les tokens"""
        response = self.client.post('/api/auth/login/', self.employee_credentials)
        if response.status_code == 200:
            token = response.data.get('access')
            self.client.credentials(
                HTTP_AUTHORIZATION=f'Bearer {token}',
                HTTP_X_ORGANIZATION_SUBDOMAIN=self.organization.subdomain
            )
            return response.data
        return None

    def set_organization_header(self, subdomain=None):
        """Définit le header X-Organization-Subdomain"""
        subdomain = subdomain or self.organization.subdomain
        # Récupérer les credentials actuels
        current_auth = self.client._credentials.get('HTTP_AUTHORIZATION', '')
        self.client.credentials(
            HTTP_AUTHORIZATION=current_auth,
            HTTP_X_ORGANIZATION_SUBDOMAIN=subdomain
        )

    def clear_credentials(self):
        """Supprime toutes les credentials du client"""
        self.client.credentials()

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.clear_credentials()
        super().tearDown()
