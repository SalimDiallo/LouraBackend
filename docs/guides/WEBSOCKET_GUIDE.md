# WebSocket Guide - Loura Backend

## Introduction

Django Channels permet les communications WebSocket pour les notifications en temps réel.

**Voir** : `app/notifications/consumers.py`

---

## Configuration

### Channel Layers (Redis)

```python
# app/lourabackend/settings.py

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://localhost:6379/2"],
        },
    },
}
```

---

### ASGI Application

```python
# app/lourabackend/asgi.py

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

---

## Consumer WebSocket

### Routing

```python
# app/notifications/routing.py

from django.urls import re_path
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]
```

**URL** : `ws://localhost:8000/ws/notifications/?token=JWT&organization=slug`

---

### Consumer Implementation

```python
# app/notifications/consumers.py

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. Authentifier via JWT (query params)
        token = self.scope['query_string']...
        user = await self.get_user_from_token(token)

        # 2. Vérifier organisation
        organization = await self.get_organization(org_slug)

        # 3. Rejoindre le groupe
        self.room_group_name = f'notifications_{user.id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 4. Accepter connexion
        await self.accept()

    async def notification_message(self, event):
        """Recevoir notification du backend et envoyer au client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
```

**Voir** : `app/notifications/consumers.py` (lignes 15-178)

---

## Connexion Client (JavaScript)

### Établir connexion

```javascript
const token = 'eyJ0eXAiOiJKV1Q...'; // JWT access token
const orgSlug = 'my-organization';

const ws = new WebSocket(
  `ws://localhost:8000/ws/notifications/?token=${token}&organization=${orgSlug}`
);

ws.onopen = () => {
  console.log('WebSocket connecté');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'notification') {
    console.log('Nouvelle notification:', data.notification);
    // Afficher la notification dans l'UI
    showNotification(data.notification);
  }

  if (data.type === 'unread_count') {
    console.log('Notifications non lues:', data.count);
    updateBadge(data.count);
  }
};

ws.onerror = (error) => {
  console.error('Erreur WebSocket:', error);
};

ws.onclose = (event) => {
  console.log('WebSocket fermé:', event.code);
  // Reconnexion automatique
  setTimeout(reconnect, 5000);
};
```

---

### Envoyer des messages

```javascript
// Demander rafraîchissement du compteur
ws.send(JSON.stringify({
  action: 'refresh_count'
}));
```

---

## Envoi de notifications depuis le backend

### Méthode 1 : Depuis une vue/tâche

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification_to_user(user, notification_data):
    """Envoyer une notification via WebSocket."""

    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{user.id}'

    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )
```

---

### Méthode 2 : Helper (recommandé)

```python
# app/notifications/notification_helpers.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def send_notification(organization, recipient, title, message, **kwargs):
    """
    Créer et envoyer une notification.

    Args:
        organization: Organization instance
        recipient: BaseUser instance
        title: Titre de la notification
        message: Message de la notification
        **kwargs: Champs additionnels (notification_type, priority, etc.)
    """
    # 1. Créer en DB
    notification = Notification.objects.create(
        organization=organization,
        recipient=recipient,
        title=title,
        message=message,
        **kwargs
    )

    # 2. Envoyer via WebSocket
    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{recipient.id}'

    notification_data = {
        'id': str(notification.id),
        'title': notification.title,
        'message': notification.message,
        'notification_type': notification.notification_type,
        'priority': notification.priority,
        'created_at': notification.created_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )

    return notification
```

---

### Exemple d'utilisation

```python
# Dans une vue ou une tâche Celery
from notifications.notification_helpers import send_notification

def process_credit_sale(credit_sale):
    # Logique métier...

    # Envoyer notification
    send_notification(
        organization=credit_sale.organization,
        recipient=admin_user,
        title=f"Échéance approchante - {credit_sale.customer.name}",
        message=f"La créance #{credit_sale.sale.sale_number} arrive à échéance dans 3 jours.",
        notification_type='alert',
        priority='high',
        entity_type='credit_sale',
        entity_id=str(credit_sale.id),
        action_url=f'/inventory/credit-sales/{credit_sale.id}'
    )
```

---

## Authentification WebSocket

### Flow

1. **Client** : Récupère JWT access token (POST /api/auth/login/)
2. **Client** : Se connecte au WebSocket avec token dans query params
3. **Consumer** : Valide le token via `AccessToken(token)`
4. **Consumer** : Vérifie l'appartenance à l'organisation
5. **Consumer** : Accepte ou rejette la connexion

### Codes de fermeture

- **4001** : Paramètres manquants (token ou organization)
- **4002** : Authentification échouée
- **4003** : Organisation introuvable
- **4004** : Accès refusé (pas membre de l'organisation)

---

## Gestion de la reconnexion

```javascript
let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function connect() {
  ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}&organization=${orgSlug}`);

  ws.onopen = () => {
    console.log('Connecté');
    reconnectAttempts = 0;
  };

  ws.onclose = (event) => {
    console.log('Déconnecté:', event.code);

    // Reconnexion exponentielle
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, delay);
    }
  };

  ws.onerror = (error) => {
    console.error('Erreur:', error);
    ws.close();
  };
}

connect();
```

---

## Production

### Daphne (ASGI Server)

```bash
# Lancer Daphne
daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application

# Avec Systemd
sudo systemctl start daphne
```

**Fichier Systemd** : `/etc/systemd/system/daphne.service`

```ini
[Unit]
Description=Daphne ASGI Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app
ExecStart=/app/venv/bin/daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Nginx Proxy

```nginx
upstream daphne {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Debugging

### Logs

```python
# Dans le Consumer
import logging
logger = logging.getLogger(__name__)

async def connect(self):
    logger.info(f"Connexion WebSocket: {self.scope['client']}")
```

### Redis Monitor

```bash
redis-cli monitor
```

Voir les messages publiés dans les channels.

---

## Références

- **Django Channels** : https://channels.readthedocs.io/
- **WebSocket API** : https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
