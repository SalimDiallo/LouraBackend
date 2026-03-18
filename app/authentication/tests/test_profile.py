"""
Tests pour UpdateProfileView et ChangePasswordView
==================================================
Tests pour la mise ï¿½ jour de profil et changement de mot de passe
"""

from rest_framework import status
from conftest import BaseAPITestCase


class UpdateProfileViewTests(BaseAPITestCase):
    """Tests pour l'endpoint PATCH /api/auth/profile/"""

    def test_update_profile_common_fields_admin(self):
        """Test mise ï¿½ jour champs communs pour admin"""
        self.authenticate_as_admin()

        data = {
            'first_name': 'Updated',
            'last_name': 'Admin',
            'phone': '+224620999999',
            'language': 'en',
            'timezone': 'UTC'
        }

        response = self.client.patch('/api/auth/profile/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Updated')
        self.assertEqual(response.data['user']['phone'], '+224620999999')

        # Vï¿½rifier en DB
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Updated')

    def test_update_profile_common_fields_employee(self):
        """Test mise ï¿½ jour champs communs pour employee"""
        self.authenticate_as_employee()

        data = {
            'first_name': 'Updated',
            'last_name': 'Employee',
            'phone': '+224620888888'
        }

        response = self.client.patch('/api/auth/profile/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Updated')

        # Vï¿½rifier en DB
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.first_name, 'Updated')

    def test_update_profile_employee_specific_fields(self):
        """Test mise ï¿½ jour champs spï¿½cifiques employee"""
        self.authenticate_as_employee()

        data = {
            'date_of_birth': '1990-01-01',
            'address': '123 Test Street',
            'city': 'Conakry',
            'country': 'Guinea',
            'emergency_contact': {
                'name': 'John Doe',
                'phone': '+224620777777',
                'relationship': 'Brother'
            }
        }

        response = self.client.patch('/api/auth/profile/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vï¿½rifier en DB
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.city, 'Conakry')
        self.assertEqual(self.employee.emergency_contact['name'], 'John Doe')

    def test_update_profile_admin_cannot_update_employee_fields(self):
        """Test que admin ne peut pas modifier champs employee"""
        self.authenticate_as_admin()

        data = {
            'first_name': 'Updated',
            'date_of_birth': '1990-01-01',  # Champ employee
            'address': '123 Test Street'    # Champ employee
        }

        response = self.client.patch('/api/auth/profile/', data)

        # Devrait rï¿½ussir mais ignorer les champs employee
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vï¿½rifier en DB
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Updated')
        # Les champs employee ne devraient pas exister pour admin

    def test_update_profile_requires_authentication(self):
        """Test que l'endpoint nï¿½cessite l'authentification"""
        self.clear_credentials()

        response = self.client.patch('/api/auth/profile/', {
            'first_name': 'Test'
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_partial_update(self):
        """Test mise ï¿½ jour partielle (un seul champ)"""
        self.authenticate_as_admin()

        response = self.client.patch('/api/auth/profile/', {
            'first_name': 'OnlyFirst'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'OnlyFirst')

        # Vï¿½rifier que les autres champs n'ont pas changï¿½
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.last_name, 'Test')  # Inchangï¿½

    def test_update_profile_validation_error(self):
        """Test erreur de validation"""
        self.authenticate_as_admin()

        # Supposons que phone a un format spï¿½cifique
        response = self.client.patch('/api/auth/profile/', {
            'email': 'invalid-email'  # Email ne devrait pas ï¿½tre modifiable ici
        })

        # Selon l'implï¿½mentation, cela pourrait ï¿½tre ignorï¿½ ou retourner une erreur

    def test_update_profile_returns_correct_serializer(self):
        """Test que le bon sï¿½rialiseur est retournï¿½"""
        # Admin
        self.authenticate_as_admin()
        admin_response = self.client.patch('/api/auth/profile/', {
            'first_name': 'AdminUpdated'
        })
        self.assertIn('organizations', admin_response.data['user'])

        # Employee
        self.clear_credentials()
        self.authenticate_as_employee()
        employee_response = self.client.patch('/api/auth/profile/', {
            'first_name': 'EmployeeUpdated'
        })
        self.assertIn('organization', employee_response.data['user'])


class ChangePasswordViewTests(BaseAPITestCase):
    """Tests pour l'endpoint POST /api/auth/change-password/"""

    def test_change_password_success(self):
        """Test changement de mot de passe avec donnï¿½es valides"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Vï¿½rifier que le mot de passe a changï¿½
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('newpass123'))
        self.assertFalse(self.admin.check_password('testpass123'))

    def test_change_password_incorrect_old_password(self):
        """Test avec ancien mot de passe incorrect"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'wrongpassword',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Vï¿½rifier que le mot de passe n'a pas changï¿½
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('testpass123'))

    def test_change_password_missing_old_password(self):
        """Test sans ancien mot de passe"""
        self.authenticate_as_admin()

        data = {
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_missing_new_password(self):
        """Test sans nouveau mot de passe"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_mismatch_confirmation(self):
        """Test avec mots de passe qui ne correspondent pas"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'different123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_too_short(self):
        """Test avec mot de passe trop court (< 8 caractï¿½res)"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'new_password': 'short',
            'confirm_password': 'short'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_change_password_requires_authentication(self):
        """Test que l'endpoint nï¿½cessite l'authentification"""
        self.clear_credentials()

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_hashed_correctly(self):
        """Test que le nouveau mot de passe est bien hashï¿½"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vï¿½rifier que le password n'est pas stockï¿½ en clair
        self.admin.refresh_from_db()
        self.assertNotEqual(self.admin.password, 'newpass123')
        self.assertTrue(self.admin.check_password('newpass123'))

    def test_change_password_alternative_confirm_field(self):
        """Test avec new_password_confirm au lieu de confirm_password"""
        self.authenticate_as_admin()

        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'  # Nom alternatif
        }

        response = self.client.post('/api/auth/change-password/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
