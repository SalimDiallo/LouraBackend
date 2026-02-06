"""
Celery — configuration du projet Loura
=======================================
En développement : CELERY_TASK_ALWAYS_EAGER = True
→ les tâches s'exécutent synchronement dans le même processus.
Pas besoin de lancer un worker séparé.

En production, mettre CELERY_TASK_ALWAYS_EAGER = False
et lancer : celery -A lourabackend worker -l info
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lourabackend.settings')

app = Celery('loura')

# Charge toute la config Celery depuis Django settings (préfixe CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodécouvrir les tasks.py dans chaque app Django
app.autodiscover_tasks()
