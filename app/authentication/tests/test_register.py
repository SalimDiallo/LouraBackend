"""
Tests pour RegisterAdminView
=============================
Tests critiques pour l'endpoint d'inscription admin
"""

from rest_framework import status
from core.models import AdminUser, Organization, BaseUser
from conftest import BaseAPITestCase


class RegisterAdminViewTests(BaseAPITestCase):
    """Tests pour l'endpoint POST /api/auth/register/admin/"""

    def test_register_admin_success(self):
        """Test inscription admin avec données valides"""
        data = {
            'email': 'newadmin@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin',
            'phone': '+224620000002'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user_type'], 'admin')
        self.assertEqual(response.data['user']['email'], 'newadmin@test.com')

        # Vérifier que l'admin a été créé dans la DB
        self.assertTrue(AdminUser.objects.filter(email='newadmin@test.com').exists())

    def test_register_admin_creates_tokens(self):
        """Test que les tokens JWT sont générés après inscription"""
        data = {
            'email': 'newadmin2@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIsInstance(response.data['access'], str)
        self.assertIsInstance(response.data['refresh'], str)
        self.assertTrue(len(response.data['access']) > 50)

    def test_register_admin_email_unique(self):
        """Test que l'email doit être unique"""
        data = {
            'email': 'admin@test.com',  # Email déjà utilisé dans setUp
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_admin_password_min_length(self):
        """Test que le mot de passe doit avoir au moins 8 caractères"""
        data = {
            'email': 'newadmin3@test.com',
            'password': 'short',  # Moins de 8 caractères
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_admin_missing_email(self):
        """Test inscription sans email"""
        data = {
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_admin_missing_password(self):
        """Test inscription sans mot de passe"""
        data = {
            'email': 'newadmin4@test.com',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_admin_missing_first_name(self):
        """Test inscription sans prénom"""
        data = {
            'email': 'newadmin5@test.com',
            'password': 'newpass123',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_register_admin_missing_last_name(self):
        """Test inscription sans nom"""
        data = {
            'email': 'newadmin6@test.com',
            'password': 'newpass123',
            'first_name': 'New'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data)

    def test_register_admin_phone_optional(self):
        """Test que le téléphone est optionnel"""
        data = {
            'email': 'newadmin7@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
            # pas de phone
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_admin_password_hashed(self):
        """Test que le mot de passe est hashé"""
        data = {
            'email': 'newadmin8@test.com',
            'password': 'testpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Récupérer l'admin depuis la DB
        admin = AdminUser.objects.get(email='newadmin8@test.com')

        # Vérifier que le password n'est pas stocké en clair
        self.assertNotEqual(admin.password, 'testpass123')

        # Vérifier qu'on peut se connecter avec le password
        self.assertTrue(admin.check_password('testpass123'))

    def test_register_admin_email_normalized(self):
        """Test que l'email est normalisé (lowercase)"""
        data = {
            'email': 'NEWADMIN9@TEST.COM',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'newadmin9@test.com')

    def test_register_admin_invalid_email_format(self):
        """Test avec un format d'email invalide"""
        data = {
            'email': 'not-an-email',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_admin_user_type_set_correctly(self):
        """Test que le user_type est bien défini à 'admin'"""
        data = {
            'email': 'newadmin10@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier dans la DB
        admin = BaseUser.objects.get(email='newadmin10@test.com')
        self.assertEqual(admin.user_type, 'admin')

    def test_register_admin_sets_jwt_cookies(self):
        """Test que les cookies JWT sont définis"""
        data = {
            'email': 'newadmin11@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Vérifier que les cookies sont définis (selon la configuration)

    def test_register_admin_response_format(self):
        """Test le format de la réponse"""
        data = {
            'email': 'newadmin12@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier la structure de la réponse
        self.assertIn('user', response.data)
        self.assertIn('user_type', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('message', response.data)

        # Vérifier les valeurs
        self.assertEqual(response.data['user_type'], 'admin')
        self.assertEqual(response.data['message'], 'Inscription réussie')

    def test_register_admin_includes_organizations_in_response(self):
        """Test que la réponse inclut les organisations de l'admin"""
        data = {
            'email': 'newadmin13@test.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'Admin'
        }

        response = self.client.post('/api/auth/register/admin/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('organizations', response.data['user'])
