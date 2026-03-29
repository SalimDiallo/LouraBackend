# Celery Guide - Loura Backend

## Introduction

Celery est utilisé pour les tâches asynchrones et les tâches périodiques.

**Voir** : `app/lourabackend/celery.py`, `app/inventory/tasks.py`

---

## Configuration

### Celery App

**Fichier** : `app/lourabackend/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lourabackend.settings')

app = Celery('loura')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

---

### Settings Django

```python
# Broker et Backend
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'

# Sérialisation
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
```

**Voir** : `app/lourabackend/settings.py` (lignes 132-148)

---

## Workers et Beat

### Lancer Worker

```bash
# Worker seul
celery -A lourabackend worker -l info

# Worker + Beat (dev)
celery -A lourabackend worker --beat -l info

# Worker avec concurrency
celery -A lourabackend worker -l info --concurrency=4

# Worker en arrière-plan (production)
celery -A lourabackend worker -l info --detach --pidfile=/var/run/celery/worker.pid
```

---

### Lancer Beat (Scheduler)

```bash
# Beat seul
celery -A lourabackend beat -l info

# Beat en arrière-plan
celery -A lourabackend beat -l info --detach --pidfile=/var/run/celery/beat.pid
```

---

## Tâches disponibles

### 1. Check Credit Sale Deadlines

**Fichier** : `app/inventory/tasks.py` (lignes 18-128)

```python
@shared_task
def check_credit_sale_deadlines():
    """
    Vérifie les échéances de ventes à crédit.
    Envoie des notifications : 7j, 3j, 1j avant + retards.
    """
```

**Schedule** : Tous les jours à 8h00 UTC

**Config** :
```python
CELERY_BEAT_SCHEDULE = {
    'check-credit-sale-deadlines': {
        'task': 'inventory.tasks.check_credit_sale_deadlines',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

---

### 2. Update Overdue Credit Sales

**Fichier** : `app/inventory/tasks.py` (lignes 300-332)

```python
@shared_task
def update_overdue_credit_sales():
    """
    Met à jour le statut des ventes à crédit en retard.
    """
```

**Schedule** : Tous les jours à 9h00 UTC

---

### 3. Purge Old Notifications

**Fichier** : `app/notifications/tasks.py`

```python
@shared_task
def purge_old_notifications_task(days=30):
    """
    Supprime les notifications lues de plus de X jours.
    """
```

**Schedule** : Tous les lundis à 2h00

---

## Créer une tâche custom

### 1. Définir la tâche

```python
# app/myapp/tasks.py

from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task
def my_custom_task(param1, param2):
    """Ma tâche personnalisée."""
    logger.info(f"Début de la tâche avec {param1}, {param2}")

    # Votre logique métier
    result = do_something(param1, param2)

    logger.info("Tâche terminée")
    return result
```

---

### 2. Appeler la tâche

```python
# Dans une vue ou un signal

# Asynchrone (immédiat)
from myapp.tasks import my_custom_task
my_custom_task.delay('value1', 'value2')

# Avec délai
my_custom_task.apply_async(
    args=['value1', 'value2'],
    countdown=60  # Dans 60 secondes
)

# À une date précise
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
my_custom_task.apply_async(
    args=['value1', 'value2'],
    eta=eta
)
```

---

### 3. Tâche périodique

```python
# app/lourabackend/settings.py

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'my-periodic-task': {
        'task': 'myapp.tasks.my_custom_task',
        'schedule': crontab(hour=10, minute=0),  # 10h00 chaque jour
        'args': ('value1', 'value2'),
    },
}
```

---

## Monitoring

### Flower (Dashboard Web)

```bash
# Installer Flower
pip install flower

# Lancer
celery -A lourabackend flower
```

**URL** : http://localhost:5555

---

### Commandes utiles

```bash
# Voir les tâches actives
celery -A lourabackend inspect active

# Voir les tâches enregistrées
celery -A lourabackend inspect registered

# Voir les workers
celery -A lourabackend inspect stats

# Purger toutes les tâches en attente
celery -A lourabackend purge
```

---

## Debugging

### Logs

```python
# Dans votre tâche
import logging
logger = logging.getLogger(__name__)

@shared_task
def my_task():
    logger.info("Début de la tâche")
    try:
        # Code
        logger.debug("Debug info")
    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise
```

---

### Mode synchrone (développement)

```python
# app/lourabackend/settings.py

if DEBUG:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
```

Les tâches s'exécutent **synchronement** (pas besoin de worker).

---

## Production

### Systemd (Ubuntu/Debian)

**Fichier** : `/etc/systemd/system/celery.service`

```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/app
ExecStart=/app/venv/bin/celery -A lourabackend worker -l info --detach
Restart=always

[Install]
WantedBy=multi-user.target
```

**Fichier** : `/etc/systemd/system/celery-beat.service`

```ini
[Unit]
Description=Celery Beat
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/app
ExecStart=/app/venv/bin/celery -A lourabackend beat -l info --detach
Restart=always

[Install]
WantedBy=multi-user.target
```

**Activer** :
```bash
sudo systemctl enable celery celery-beat
sudo systemctl start celery celery-beat
```

---

## Références

- **Celery Documentation** : https://docs.celeryproject.org/
- **Celery Beat** : https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
