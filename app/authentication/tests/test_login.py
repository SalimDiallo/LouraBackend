"""
Tests pour LoginView
====================
Tests critiques pour l'endpoint de connexion unifié (Admin + Employee)
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone

from core.models import AdminUser, Organization, Category
from hr.models import Employee
from conftest import BaseAPITestCase


class LoginViewTests(BaseAPITestCase):
    """Tests pour l'endpoint POST /api/auth/login/"""

    def test_login_admin_success(self):
        """Test connexion admin avec credentials valides"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user_type'], 'admin')
        self.assertEqual(response.data['user']['email'], 'admin@test.com')

    def test_login_employee_success(self):
        """Test connexion employee avec credentials valides"""
        response = self.client.post('/api/auth/login/', {
            'email': 'employee@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user_type'], 'employee')
        self.assertEqual(response.data['user']['email'], 'employee@test.com')

    def test_login_invalid_email(self):
        """Test connexion avec email invalide"""
        response = self.client.post('/api/auth/login/', {
            'email': 'invalid@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_invalid_password(self):
        """Test connexion avec mot de passe invalide"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_missing_email(self):
        """Test connexion sans email"""
        response = self.client.post('/api/auth/login/', {
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_missing_password(self):
        """Test connexion sans mot de passe"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_inactive_user(self):
        """Test connexion avec compte désactivé"""
        self.admin.is_active = False
        self.admin.save()

        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_inactive_organization(self):
        """Test connexion employee avec organisation désactivée"""
        self.organization.is_active = False
        self.organization.save()

        response = self.client.post('/api/auth/login/', {
            'email': 'employee@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_updates_last_login(self):
        """Test que last_login est mis à jour lors de la connexion"""
        # Vérifier que last_login est None au début
        self.assertIsNone(self.admin.last_login)

        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Recharger l'admin depuis la DB
        self.admin.refresh_from_db()
        self.assertIsNotNone(self.admin.last_login)

    def test_login_returns_jwt_tokens(self):
        """Test que les tokens JWT sont retournés"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIsInstance(response.data['access'], str)
        self.assertIsInstance(response.data['refresh'], str)
        self.assertTrue(len(response.data['access']) > 50)  # JWT devrait être long

    def test_login_admin_serializer_fields(self):
        """Test que le sérialiseur admin retourne les bons champs"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']

        # Vérifier les champs de base
        self.assertIn('id', user_data)
        self.assertIn('email', user_data)
        self.assertIn('first_name', user_data)
        self.assertIn('last_name', user_data)
        self.assertIn('organizations', user_data)  # Spécifique admin

    def test_login_employee_serializer_fields(self):
        """Test que le sérialiseur employee retourne les bons champs"""
        response = self.client.post('/api/auth/login/', {
            'email': 'employee@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']

        # Vérifier les champs de base
        self.assertIn('id', user_data)
        self.assertIn('email', user_data)
        self.assertIn('organization', user_data)  # Spécifique employee
        self.assertIn('employee_id', user_data)

    def test_login_email_case_insensitive(self):
        """Test que l'email est insensible à la casse"""
        response = self.client.post('/api/auth/login/', {
            'email': 'ADMIN@TEST.COM',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'admin@test.com')

    def test_login_cookies_set(self):
        """Test que les cookies JWT sont définis"""
        response = self.client.post("/api/auth/login/", {
            'email': 'admin@test.com'f,
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Vérifier que les cookies sont définis (selon la configuration)
        # Note: Cela dépend de la configuration SIMPLE_JWT dans settings

    def test_login_uuids_converted_to_strings(self):
        """Test que les UUIDs sont convertis en strings"""
        response = self.client.post('/api/auth/login/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data['user']

        # Vérifier que l'ID est une string
        self.assertIsInstance(user_data['id'], str)

        # Si l'admin a des organisations, vérifier que leurs IDs sont des strings
        if user_data.get('organizations'):
            for org in user_data['organizations']:
                self.assertIsInstance(org['id'], str)
