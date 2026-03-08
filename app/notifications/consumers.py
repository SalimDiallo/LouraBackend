"""
WebSocket Consumer pour les notifications en temps réel
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from core.models import Organization
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications en temps réel.

    URL: ws://localhost:8000/ws/notifications/?token=JWT_TOKEN&organization=ORG_SLUG
    """

    async def connect(self):
        """Gérer la connexion WebSocket"""
        # Récupérer les paramètres de la query string
        from urllib.parse import parse_qs

        raw_qs = self.scope['query_string'].decode()
        parsed = parse_qs(raw_qs)
        # parse_qs returns lists, extract first value
        token = parsed.get('token', [None])[0]
        org_slug = parsed.get('organization', [None])[0]

        if not token or not org_slug:
            await self.close(code=4001)
            return

        # Authentifier l'utilisateur via le token
        user = await self.get_user_from_token(token)
        if not user:
            await self.close(code=4002)
            return

        # Vérifier l'organisation
        organization = await self.get_organization(org_slug)
        if not organization:
            await self.close(code=4003)
            return

        # Vérifier que l'utilisateur appartient à cette organisation
        has_access = await self.user_has_org_access(user, organization)
        if not has_access:
            await self.close(code=4004)
            return

        # Stocker les informations dans le scope
        self.user = user
        self.organization = organization
        self.room_group_name = f'notifications_{user.id}'

        # Rejoindre le groupe de notifications de cet utilisateur
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Envoyer le compteur initial de notifications non lues
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        """Gérer la déconnexion"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Recevoir un message du client
        (Pour l'instant, on gère juste les demandes de rafraîchissement du compteur)
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'refresh_count':
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': unread_count
                }))
        except json.JSONDecodeError:
            pass

    async def notification_message(self, event):
        """
        Handler pour les messages de type 'notification_message'
        Envoyé depuis le code backend via channel_layer.group_send()
        """
        notification_data = event['notification']

        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification_data
        }))

    async def unread_count_update(self, event):
        """
        Handler pour la mise à jour du compteur
        """
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': event['count']
        }))

    # --- Helpers database ---

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Authentifier l'utilisateur via le token JWT
        """
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            # Valider le token
            access_token = AccessToken(token)
            user_id = access_token['user_id']

            # Récupérer l'utilisateur
            user = User.objects.filter(id=user_id, is_active=True).first()
            return user
        except (TokenError, KeyError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def get_organization(self, slug):
        """Récupérer l'organisation par slug"""
        try:
            return Organization.objects.get(subdomain=slug)
        except Organization.DoesNotExist:
            return None

    @database_sync_to_async
    def user_has_org_access(self, user, organization):
        """
        Vérifier que l'utilisateur a accès à cette organisation
        """
        # Pour BaseUser, vérifier via admin_organizations ou employee_organizations
        from core.models import AdminUser
        from hr.models import Employee

        # Vérifier si c'est un admin de cette organisation
        if hasattr(user, 'adminuser'):
            return user.adminuser.get_organizations_for_admin().filter(id=organization.id).exists()

        # Vérifier si c'est un employé de cette organisation
        if hasattr(user, 'employee'):
            return user.employee.organization_id == organization.id

        return False

    @database_sync_to_async
    def get_unread_count(self):
        """Récupérer le nombre de notifications non lues"""
        return Notification.objects.filter(
            recipient=self.user,
            organization=self.organization,
            is_read=False
        ).count()
