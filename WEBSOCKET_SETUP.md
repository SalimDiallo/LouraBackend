# Configuration WebSocket pour Notifications en Temps Réel

Ce guide explique comment configurer Django Channels pour les notifications WebSocket.

## 📦 Installation

### 1. Installer les dépendances

```bash
cd /home/salim/Projets/loura/stack/backend
source venv/bin/activate
pip install channels channels-redis daphne
```

### 2. Mettre à jour `requirements.txt`

```txt
channels==4.0.0
channels-redis==4.2.0
daphne==4.1.0
```

## ⚙️ Configuration Django

### 1. Ajouter Channels à `INSTALLED_APPS`

Dans `/home/salim/Projets/loura/stack/backend/app/lourabackend/settings.py`:

```python
INSTALLED_APPS = [
    'daphne',  # IMPORTANT: Doit être en PREMIER
    'django.contrib.admin',
    'django.contrib.auth',
    # ... autres apps
    'channels',
    'notifications',
]
```

### 2. Configurer ASGI Application

Dans `settings.py`, ajouter:

```python
# ASGI Application
ASGI_APPLICATION = 'lourabackend.asgi.application'

# Channels Layer Configuration
CHANNEL_LAYERS = {
    'default': {
        # Pour le développement (en mémoire)
        'BACKEND': 'channels.layers.InMemoryChannelLayer'

        # Pour la production (avec Redis)
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [('127.0.0.1', 6379)],
        # },
    },
}
```

## 🚀 Fichiers créés

### 1. `notifications/consumers.py`
Consumer WebSocket qui gère:
- Authentification via JWT token
- Vérification de l'organisation
- Envoi du compteur initial
- Réception des messages en temps réel

### 2. `notifications/routing.py`
Routing WebSocket:
```python
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
```

### 3. `notifications/websocket_helpers.py`
Helpers pour envoyer des notifications:
- `send_notification_to_user(notification)` - Envoie une notification
- `send_unread_count_to_user(user_id, count)` - Met à jour le compteur

### 4. `lourabackend/asgi.py` (Modifié)
Configuration ASGI avec support WebSocket

## 🔧 Utilisation

### Démarrer le serveur avec Daphne

```bash
# Development
daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application

# Ou avec uvicorn
uvicorn lourabackend.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Connexion WebSocket depuis le frontend

```javascript
const token = localStorage.getItem('access_token');
const orgSlug = localStorage.getItem('current_organization_slug');
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}&organization=${orgSlug}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'notification') {
    console.log('Nouvelle notification:', data.notification);
  }
};
```

### Créer une notification depuis le code

```python
from notifications.models import Notification
from notifications.websocket_helpers import send_notification_to_user

# Créer la notification
notification = Notification.objects.create(
    organization=organization,
    recipient=user,
    title="Nouvelle vente",
    message="Une nouvelle vente a été créée",
    notification_type="alert",
    priority="high",
    action_url="/apps/org/inventory/sales/123"
)

# Envoyer via WebSocket
send_notification_to_user(notification)
```

## 🐛 Debugging

### Vérifier que Channels est bien installé

```bash
python manage.py shell
>>> import channels
>>> print(channels.__version__)
```

### Tester la connexion WebSocket

Depuis le frontend, ouvrir la console:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/?token=YOUR_TOKEN&organization=YOUR_ORG');
ws.onopen = () => console.log('✅ Connecté');
ws.onerror = (e) => console.error('❌ Erreur:', e);
ws.onmessage = (e) => console.log('📩 Message:', e.data);
```

### Logs Backend

Les logs apparaîtront dans le terminal Daphne/Uvicorn:
- Connexion: "WebSocket HANDSHAKING /ws/notifications/"
- Messages: "WebSocket SEND/RECEIVE"
- Déconnexion: "WebSocket DISCONNECT"

## 📝 Production

Pour la production, utiliser Redis comme channel layer:

### 1. Installer Redis

```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Configurer dans settings.py

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 3. Déployer avec Supervisor ou Systemd

```ini
[program:daphne]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application
directory=/path/to/backend/app
user=www-data
autostart=true
autorestart=true
```

## 🎯 Commandes utiles

```bash
# Tester que tout est OK
python manage.py check

# Créer les migrations si nécessaire
python manage.py makemigrations
python manage.py migrate

# Lancer le serveur ASGI
daphne lourabackend.asgi:application

# Ou avec reload automatique (dev)
daphne -b 0.0.0.0 -p 8000 --reload lourabackend.asgi:application
```

## ✅ Checklist d'installation

- [ ] Installer `channels`, `channels-redis`, `daphne`
- [ ] Ajouter `daphne` en PREMIER dans `INSTALLED_APPS`
- [ ] Ajouter `channels` dans `INSTALLED_APPS`
- [ ] Configurer `ASGI_APPLICATION` dans `settings.py`
- [ ] Configurer `CHANNEL_LAYERS` dans `settings.py`
- [ ] Vérifier que `asgi.py` est bien configuré
- [ ] Tester la connexion WebSocket depuis le frontend
- [ ] Vérifier que les notifications sont envoyées en temps réel

## 🎉 Résultat

Une fois configuré, le système fonctionne comme suit:

1. **Frontend** se connecte via WebSocket
2. **Backend** authentifie via JWT et organisation
3. **Nouvelle notification** créée → envoyée instantanément via WebSocket
4. **Frontend** affiche la notification push
5. **Badge** se met à jour automatiquement

Le système est maintenant prêt pour les notifications en temps réel! 🚀
