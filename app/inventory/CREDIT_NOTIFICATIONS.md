# Système de Notifications pour Ventes à Crédit

## Vue d'ensemble

Le système envoie automatiquement des notifications aux administrateurs pour:
- **Échéances approchantes** (7, 3, 1 jours avant)
- **Paiements en retard** (rappels progressifs)

Les notifications apparaissent en temps réel dans l'interface frontend via WebSocket/SSE.

---

## Fonctionnalités

### 1. Délai de Grâce (Grace Period)

Chaque vente à crédit peut avoir un délai de grâce (`grace_period_days`).

**Exemple:**
- `due_date` = 2026-03-15
- `grace_period_days` = 3
- **Date limite effective** = 2026-03-18

Le statut `overdue` ne sera activé qu'après le 18 mars.

### 2. Notifications Automatiques

#### Échéances Approchantes
| Jours avant | Priorité | Type | Destinataires |
|-------------|----------|------|---------------|
| 7 jours | `medium` | `alert` | Tous les admins |
| 3 jours | `medium` | `alert` | Tous les admins |
| 1 jour | `high` | `alert` | Tous les admins |

#### Paiements en Retard
| Jours de retard | Priorité | Type | Destinataires |
|-----------------|----------|------|---------------|
| 0 (jour J) | `high` | `alert` | Tous les admins |
| 1 jour | `high` | `alert` | Tous les admins |
| 3 jours | `high` | `alert` | Tous les admins |
| 7 jours | `critical` | `alert` | Tous les admins |
| 14 jours | `critical` | `alert` | Tous les admins |
| 30 jours | `critical` | `alert` | Tous les admins |

### 3. Protection Anti-Spam

Les notifications ne sont envoyées qu'une fois par jour pour une même créance.
Les champs `last_reminder_date` et `reminder_count` permettent le tracking.

---

## Configuration

### Tâches Celery Périodiques

Configurées dans `lourabackend/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'check-credit-sale-deadlines': {
        'task': 'inventory.tasks.check_credit_sale_deadlines',
        'schedule': crontab(hour=8, minute=0),  # Tous les jours à 8h00 UTC
    },
    'update-overdue-credit-sales': {
        'task': 'inventory.tasks.update_overdue_credit_sales',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h00 UTC
    },
}
```

### Exécution en Développement

Avec `CELERY_TASK_ALWAYS_EAGER = True`, les tâches s'exécutent de manière synchrone.
Pas besoin de lancer un worker Celery séparé.

### Exécution en Production

1. Désactiver le mode eager:
   ```python
   CELERY_TASK_ALWAYS_EAGER = False
   ```

2. Lancer le worker Celery:
   ```bash
   celery -A lourabackend worker -l info
   ```

3. Lancer Celery Beat (scheduler):
   ```bash
   celery -A lourabackend beat -l info
   ```

4. Ou combiner les deux:
   ```bash
   celery -A lourabackend worker --beat -l info
   ```

---

## Tests Manuels

### Commande Django

Tester sans envoyer de vraies notifications:

```bash
cd backend/app
python manage.py check_credit_deadlines --dry-run
```

Tester pour une organisation spécifique:

```bash
python manage.py check_credit_deadlines --org mon-organisation
```

Envoyer les notifications réelles:

```bash
python manage.py check_credit_deadlines
```

### Test direct de la tâche Celery

```python
from inventory.tasks import check_credit_sale_deadlines

result = check_credit_sale_deadlines()
print(result)  # {'processed': 10, 'notifications_sent': 3}
```

---

## Architecture

### Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `inventory/tasks.py` | Tâches Celery périodiques |
| `inventory/models.py` | Modèle CreditSale avec logique `update_status()` |
| `inventory/management/commands/check_credit_deadlines.py` | Commande de test |
| `notifications/notification_helpers.py` | Helpers pour envoyer notifications |
| `lourabackend/settings.py` | Configuration Celery Beat |

### Flow de Notification

```
┌─────────────────────────────────────────┐
│ Celery Beat (8h00 tous les jours)      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ check_credit_sale_deadlines()           │
│ - Parcourt toutes les créances          │
│ - Calcule effective_due_date (+ grâce)  │
│ - Vérifie les seuils (7j, 3j, 1j, etc.) │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ send_notification()                     │
│ - Crée Notification model              │
│ - Push via WebSocket/SSE                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Frontend - NotificationPanel            │
│ - Affichage temps réel                  │
│ - Badge unread count                    │
│ - Lien vers credit sale detail          │
└─────────────────────────────────────────┘
```

---

## Statuts CreditSale

| Statut | Description | Condition |
|--------|-------------|-----------|
| `pending` | Aucun paiement reçu | `paid_amount = 0` et pas overdue |
| `partial` | Paiement partiel | `0 < paid_amount < total_amount` et pas overdue |
| `paid` | Entièrement payé | `remaining_amount = 0` |
| `overdue` | En retard | `effective_due_date < today` et `remaining_amount > 0` |
| `cancelled` | Annulé | Action manuelle |

---

## Exemples de Notifications

### Échéance dans 3 jours

```
Type: alert
Priorité: medium
Titre: "Échéance dans 3 jours - Client XYZ"
Message:
  La créance #VNT-2026-0042 arrive à échéance dans 3 jours.
  Client: Client XYZ
  Montant restant: 150,000 FCFA
  Date d'échéance: 13/03/2026
```

### Paiement en retard (7 jours)

```
Type: alert
Priorité: critical
Titre: "🔴 Paiement en retard (7 jours) - Client ABC"
Message:
  La créance #VNT-2026-0038 est en retard de 7 jours.
  Client: Client ABC
  Montant restant: 250,000 FCFA
  Date d'échéance: 03/03/2026
  Rappels envoyés: 4
```

---

## Monitoring

### Vérifier les logs Celery

```bash
# En développement (synchrone)
# Les logs apparaissent directement dans la console Django

# En production
tail -f celery-worker.log | grep "credit"
```

### Statistiques via Dashboard

Endpoint: `GET /api/inventory/credit-sales/summary/`

```json
{
  "total_credit": 1250000.00,
  "overdue_count": 3,
  "overdue_amount": 350000.00,
  "due_soon_count": 5
}
```

---

## Désactivation Temporaire

Pour désactiver les notifications automatiques temporairement:

### Option 1: Commenter dans settings.py

```python
CELERY_BEAT_SCHEDULE = {
    # 'check-credit-sale-deadlines': { ... },  # Commenté
}
```

### Option 2: Via Django Admin

Accéder à Django Admin → Periodic Tasks → Désactiver les tâches

---

## Dépannage

### Les notifications ne s'envoient pas

1. Vérifier que Celery est configuré:
   ```python
   python manage.py shell
   >>> from inventory.tasks import check_credit_sale_deadlines
   >>> check_credit_sale_deadlines()
   ```

2. Vérifier qu'il y a des créances avec échéance:
   ```python
   >>> from inventory.models import CreditSale
   >>> CreditSale.objects.filter(status__in=['pending','partial'], due_date__isnull=False).count()
   ```

3. Vérifier qu'il y a des admins actifs:
   ```python
   >>> from core.models import BaseUser
   >>> BaseUser.objects.filter(role__in=['admin','super_admin'], is_active=True).count()
   ```

### Les dates sont incorrectes

Vérifier le timezone dans `settings.py`:
```python
TIME_ZONE = 'UTC'  # ou 'Africa/Dakar' pour l'heure locale
USE_TZ = True
```

### Les notifications arrivent plusieurs fois

Le système vérifie `last_reminder_date` pour éviter les doublons.
Si ce champ n'est pas correctement mis à jour, réinitialiser:

```python
from inventory.models import CreditSale
CreditSale.objects.filter(last_reminder_date=None).update(last_reminder_date=timezone.now().date())
```

---

## Extension Future

### Email/SMS aux clients

Ajouter dans `inventory/tasks.py`:

```python
def send_customer_reminder(credit_sale):
    if credit_sale.customer.email:
        send_mail(
            subject=f"Rappel: Échéance de paiement - {sale_number}",
            message=...,
            from_email='noreply@loura.com',
            recipient_list=[credit_sale.customer.email]
        )
```

### Escalade selon le montant

```python
if credit_sale.remaining_amount > 1000000:  # > 1M FCFA
    priority = 'critical'
    # Notifier aussi le CEO
```

### Intégration WhatsApp

Utiliser une API comme Twilio pour envoyer des messages WhatsApp.
