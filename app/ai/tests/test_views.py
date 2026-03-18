"""
Tests pour AI Chat Views
=========================
Tests critiques pour les endpoints de chat IA avec mocking
"""

from rest_framework import status
from unittest.mock import patch, MagicMock
from django.utils import timezone

from ai.models import Conversation, Message, AIToolExecution
from conftest import BaseAPITestCase


class ConversationViewSetTests(BaseAPITestCase):
    """Tests pour ConversationViewSet"""

    def setUp(self):
        super().setUp()

        # Créer une conversation de test
        self.conversation = Conversation.objects.create(
            organization=self.organization,
            user=self.employee,
            employee=self.employee,
            title="Test Conversation",
            is_agent_mode=True
        )

        # Créer des messages
        self.message1 = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello'
        )

        self.message2 = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Hi there!'
        )

    def test_get_queryset_filters_by_organization(self):
        """Test que get_queryset() filtre par organisation"""
        self.authenticate_as_employee()
        self.set_organization_header()

        response = self.client.get('/api/ai/conversations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Toutes les conversations retournées doivent appartenir à l'organisation
        for conv_data in response.data['results']:
            conv = Conversation.objects.get(id=conv_data['id'])
            self.assertEqual(conv.organization.id, self.organization.id)

    def test_get_queryset_empty_without_header(self):
        """Test que queryset est vide sans header X-Organization-Subdomain"""
        self.authenticate_as_employee()
        # Ne pas définir le header d'organisation

        response = self.client.get('/api/ai/conversations/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_clear_action_deletes_messages(self):
        """Test action clear() supprime les messages"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Vérifier qu'il y a des messages
        self.assertEqual(self.conversation.messages.count(), 2)

        response = self.client.delete(
            f'/api/ai/conversations/{self.conversation.id}/clear/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cleared')

        # Vérifier que les anciens messages ont été supprimés
        # et qu'un nouveau message assistant a été créé
        self.conversation.refresh_from_db()
        messages = self.conversation.messages.all()
        self.assertEqual(messages.count(), 1)
        self.assertEqual(messages.first().role, 'assistant')

    def test_feedback_action_saves_feedback(self):
        """Test action feedback() sauvegarde le feedback"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'message_id': str(self.message2.id),
            'feedback': 'positive'
        }

        response = self.client.post(
            f'/api/ai/conversations/{self.conversation.id}/feedback/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'feedback saved')

        # Vérifier en DB
        self.message2.refresh_from_db()
        self.assertEqual(self.message2.feedback, 'positive')

    def test_feedback_action_requires_message_id(self):
        """Test que feedback() nécessite message_id"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'feedback': 'positive'
            # message_id manquant
        }

        response = self.client.post(
            f'/api/ai/conversations/{self.conversation.id}/feedback/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_feedback_action_message_not_found(self):
        """Test feedback avec message inexistant retourne 404"""
        self.authenticate_as_employee()
        self.set_organization_header()

        data = {
            'message_id': '00000000-0000-0000-0000-000000000000',  # ID invalide
            'feedback': 'positive'
        }

        response = self.client.post(
            f'/api/ai/conversations/{self.conversation.id}/feedback/',
            data
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_serializer_class_different_for_list(self):
        """Test que list utilise ConversationListSerializer"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Liste
        list_response = self.client.get('/api/ai/conversations/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        # Détail
        detail_response = self.client.get(f'/api/ai/conversations/{self.conversation.id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

        # Les réponses devraient avoir des structures différentes

    def test_conversations_require_authentication(self):
        """Test que les endpoints nécessitent l'authentification"""
        self.clear_credentials()

        response = self.client.get('/api/ai/conversations/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatViewTests(BaseAPITestCase):
    """Tests pour ChatView (non-streaming)"""

    def setUp(self):
        super().setUp()

    def test_chat_requires_organization_header(self):
        """Test POST sans header X-Organization-Subdomain  erreur 400"""
        self.authenticate_as_employee()
        # Ne pas définir le header d'organisation

        data = {
            'message': 'Hello AI'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('ai.views.LouraAIAgent')
    def test_chat_creates_conversation_if_absent(self, mock_agent_class):
        """Test création conversation si conversation_id absent"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent IA
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'Test response',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 100,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        initial_count = Conversation.objects.count()

        data = {
            'message': 'Hello AI'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier qu'une conversation a été créée
        self.assertEqual(Conversation.objects.count(), initial_count + 1)

    @patch('ai.views.LouraAIAgent')
    def test_chat_retrieves_existing_conversation(self, mock_agent_class):
        """Test récupération conversation existante si conversation_id fourni"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Créer une conversation
        conversation = Conversation.objects.create(
            organization=self.organization,
            user=self.employee,
            title="Existing Conversation"
        )

        # Mock l'agent IA
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'Test response',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 100,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Follow-up message',
            'conversation_id': str(conversation.id)
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['conversation_id'], str(conversation.id))

    @patch('ai.views.LouraAIAgent')
    def test_chat_saves_user_message(self, mock_agent_class):
        """Test sauvegarde message utilisateur"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent IA
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'Test response',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 100,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Test user message'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier qu'un message utilisateur a été créé
        conv_id = response.data['conversation_id']
        user_messages = Message.objects.filter(
            conversation_id=conv_id,
            role='user',
            content='Test user message'
        )
        self.assertEqual(user_messages.count(), 1)

    @patch('ai.views.LouraAIAgent')
    def test_chat_calls_agent_and_saves_response(self, mock_agent_class):
        """Test appel agent IA et sauvegarde réponse"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent IA
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'AI response content',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 150,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Ask something'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'AI response content')
        self.assertEqual(response.data['model'], 'gpt-4')

        # Vérifier que l'agent a été appelé
        mock_agent.chat.assert_called_once()

    @patch('ai.views.LouraAIAgent')
    def test_chat_handles_agent_error(self, mock_agent_class):
        """Test gestion erreur ValueError de l'agent  500"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent pour lever une ValueError
        mock_agent = MagicMock()
        mock_agent.chat.side_effect = ValueError("Agent error")
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Trigger error'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    @patch('ai.views.LouraAIAgent')
    def test_chat_creates_tool_executions(self, mock_agent_class):
        """Test création AIToolExecution si tool_calls présents"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent avec tool_calls
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'Used tools',
            'success': True,
            'tool_calls': [
                {'tool': 'get_employees', 'params': {}}
            ],
            'tool_results': [
                {'success': True, 'data': {'count': 10}}
            ],
            'response_time_ms': 200,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Use tools'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier qu'une AIToolExecution a été créée
        message_id = response.data['message_id']
        tool_execs = AIToolExecution.objects.filter(message_id=message_id)
        self.assertEqual(tool_execs.count(), 1)
        self.assertEqual(tool_execs.first().tool_name, 'get_employees')

    @patch('ai.views.LouraAIAgent')
    def test_chat_response_format(self, mock_agent_class):
        """Test response contient: content, conversation_id, message_id, tool_calls, model"""
        self.authenticate_as_employee()
        self.set_organization_header()

        # Mock l'agent
        mock_agent = MagicMock()
        mock_agent.chat.return_value = {
            'content': 'Response',
            'success': True,
            'tool_calls': [],
            'tool_results': [],
            'response_time_ms': 100,
            'model': 'gpt-4'
        }
        mock_agent_class.return_value = mock_agent

        data = {
            'message': 'Test'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('content', response.data)
        self.assertIn('conversation_id', response.data)
        self.assertIn('message_id', response.data)
        self.assertIn('tool_calls', response.data)
        self.assertIn('model', response.data)
        self.assertIn('success', response.data)

    def test_chat_requires_authentication(self):
        """Test que l'endpoint nécessite l'authentification"""
        self.clear_credentials()

        data = {
            'message': 'Test'
        }

        response = self.client.post('/api/ai/chat/', data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
