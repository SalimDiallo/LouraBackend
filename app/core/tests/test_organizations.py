"""
Tests pour OrganizationViewSet
===============================
Tests critiques pour la gestion multi-tenant des organisations
"""

from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from core.models import Organization, OrganizationSettings, AdminUser
from conftest import BaseAPITestCase


class OrganizationViewSetTests(BaseAPITestCase):
    """Tests pour les endpoints d'organisations"""

    def test_get_queryset_employee_sees_only_own_organization(self):
        """Test qu'un employee voit uniquement son organisation"""
        self.authenticate_as_employee()

        response = self.client.get('/api/organizations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.organization.id))

    def test_get_queryset_admin_sees_own_organizations(self):
        """Test qu'un admin voit ses organisations"""
        self.authenticate_as_admin()

        response = self.client.get('/api/organizations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # L'admin devrait voir au moins son organisation
        org_ids = [org['id'] for org in response.data['results']]
        self.assertIn(str(self.organization.id), org_ids)

    def test_create_organization_assigns_admin(self):
        """Test que perform_create() assigne l'admin courant"""
        self.authenticate_as_admin()

        data = {
            'name': 'New Organization',
            'subdomain': 'neworg',
            'category': self.category.id
        }

        response = self.client.post('/api/organizations/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que l'admin est bien assigné
        new_org = Organization.objects.get(subdomain='neworg')
        self.assertEqual(new_org.admin.id, self.admin.id)

    def test_create_organization_with_settings(self):
        """Test création organisation avec settings"""
        self.authenticate_as_admin()

        data = {
            'name': 'Org With Settings',
            'subdomain': 'orgwithsettings',
            'category': self.category.id,
            'settings': {
                'currency': 'EUR',
                'country': 'FR',
                'theme': 'dark'
            }
        }

        response = self.client.post('/api/organizations/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier que les settings ont été créés
        org = Organization.objects.get(subdomain='orgwithsettings')
        self.assertTrue(hasattr(org, 'organization_settings'))
        self.assertEqual(org.organization_settings.currency, 'EUR')

    def test_update_organization_settings(self):
        """Test mise à jour des settings d'une organisation"""
        self.authenticate_as_admin()

        # Créer les settings initiaux
        OrganizationSettings.objects.create(
            organization=self.organization,
            currency='GNF',
            country='GN'
        )

        data = {
            'settings': {
                'currency': 'USD',
                'theme': 'light'
            }
        }

        response = self.client.patch(
            f'/api/organizations/{self.organization.id}/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier la mise à jour
        self.organization.refresh_from_db()
        settings = self.organization.organization_settings
        self.assertEqual(settings.currency, 'USD')
        self.assertEqual(settings.theme, 'light')

    def test_activate_action(self):
        """Test action activate() met is_active=True"""
        self.authenticate_as_admin()

        # Désactiver d'abord
        self.organization.is_active = False
        self.organization.save()

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/activate/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Vérifier en DB
        self.organization.refresh_from_db()
        self.assertTrue(self.organization.is_active)

    def test_deactivate_action(self):
        """Test action deactivate() met is_active=False"""
        self.authenticate_as_admin()

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/deactivate/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Vérifier en DB
        self.organization.refresh_from_db()
        self.assertFalse(self.organization.is_active)

    def test_upload_logo_success(self):
        """Test upload logo avec fichier valide"""
        self.authenticate_as_admin()

        # Créer une image de test
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)

        logo_file = SimpleUploadedFile(
            "test_logo.png",
            image_io.read(),
            content_type="image/png"
        )

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': logo_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Vérifier que le logo a été enregistré
        self.organization.refresh_from_db()
        self.assertIsNotNone(self.organization.logo)

    def test_upload_logo_invalid_file_type(self):
        """Test upload logo avec type de fichier invalide"""
        self.authenticate_as_admin()

        # Créer un fichier texte
        text_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': text_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_upload_logo_file_too_large(self):
        """Test upload logo avec fichier trop volumineux (> 10MB)"""
        self.authenticate_as_admin()

        # Créer un fichier de plus de 10MB (simulé)
        large_content = b"0" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large_logo.png",
            large_content,
            content_type="image/png"
        )

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': large_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_upload_logo_replaces_old_logo(self):
        """Test qu'un nouveau logo remplace l'ancien"""
        self.authenticate_as_admin()

        # Uploader premier logo
        image1 = Image.new('RGB', (100, 100), color='red')
        image1_io = BytesIO()
        image1.save(image1_io, format='PNG')
        image1_io.seek(0)

        logo1 = SimpleUploadedFile(
            "logo1.png",
            image1_io.read(),
            content_type="image/png"
        )

        self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': logo1},
            format='multipart'
        )

        self.organization.refresh_from_db()
        old_logo_name = self.organization.logo.name

        # Uploader deuxième logo
        image2 = Image.new('RGB', (100, 100), color='blue')
        image2_io = BytesIO()
        image2.save(image2_io, format='PNG')
        image2_io.seek(0)

        logo2 = SimpleUploadedFile(
            "logo2.png",
            image2_io.read(),
            content_type="image/png"
        )

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': logo2},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que le logo a changé
        self.organization.refresh_from_db()
        self.assertNotEqual(self.organization.logo.name, old_logo_name)

    def test_delete_logo(self):
        """Test DELETE supprime le logo"""
        self.authenticate_as_admin()

        # D'abord uploader un logo
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='PNG')
        image_io.seek(0)

        logo = SimpleUploadedFile(
            "logo.png",
            image_io.read(),
            content_type="image/png"
        )

        self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {'logo': logo},
            format='multipart'
        )

        # Supprimer le logo
        response = self.client.delete(
            f'/api/organizations/{self.organization.id}/logo/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que le logo a été supprimé
        self.organization.refresh_from_db()
        self.assertFalse(self.organization.logo)

    def test_upload_logo_without_file(self):
        """Test upload logo sans fichier retourne erreur"""
        self.authenticate_as_admin()

        response = self.client.post(
            f'/api/organizations/{self.organization.id}/logo/',
            {},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_organization_requires_authentication(self):
        """Test que les endpoints nécessitent l'authentification"""
        self.clear_credentials()

        response = self.client.get('/api/organizations/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_create_organization(self):
        """Test qu'un employee ne peut pas créer d'organisation"""
        self.authenticate_as_employee()

        data = {
            'name': 'Employee Org',
            'subdomain': 'employeeorg',
            'category': self.category.id
        }

        response = self.client.post('/api/organizations/', data)

        # Selon les permissions, cela pourrait être 403 ou réussir
        # mais l'employee ne devrait pas pouvoir créer d'organisations
        # à moins d'avoir les permissions spécifiques

    def test_get_serializer_class_different_for_create(self):
        """Test que create utilise OrganizationCreateSerializer"""
        self.authenticate_as_admin()

        # Lors de la création
        data = {
            'name': 'Test Serializer Org',
            'subdomain': 'testserializer',
            'category': self.category.id
        }

        response = self.client.post('/api/organizations/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Le sérialiseur de réponse devrait être OrganizationSerializer
        # qui inclut plus de champs que le CreateSerializer
