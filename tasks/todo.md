# TODO - Loura Backend

> État actuel des tâches et actions à réaliser.

---

## État Actuel du Projet

### Infrastructure Docker
- ✅ docker-compose.yml configuré avec 5 services (db, redis, web, celery_worker, celery_beat)
- ✅ docker-entrypoint.sh créé pour l'initialisation des conteneurs
- ✅ deploy.sh créé pour la gestion du déploiement
- ⚠️  **Containers non démarrés** - en attente de lancement

### Configuration
- ⚠️  Vérifier l'existence du fichier `.env`
- ⚠️  Vérifier que les variables d'environnement sont correctement configurées

---

## Prochaines Actions

### 🔴 Priorité Haute - Démarrage du projet

1. **Vérifier la configuration .env**
   - Vérifier si `.env` existe
   - Si non, copier depuis `.env.example`
   - Configurer les variables essentielles :
     - `SECRET_KEY`
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`
     - `OPENAI_API_KEY` (si nécessaire)

2. **Lancer le déploiement**
   ```bash
   ./deploy.sh
   # Choisir option 1 (Fresh deployment)
   ```

3. **Vérifier le statut**
   ```bash
   ./deploy.sh
   # Choisir option 9 (Status check)
   ```

### 🟡 Priorité Moyenne - Post-déploiement

- [ ] Vérifier que tous les services sont "Healthy"
- [ ] Tester l'accès à l'API : http://localhost:8000
- [ ] Vérifier les logs en cas d'erreur
- [ ] Créer un superuser si nécessaire

### 🟢 Priorité Basse - Maintenance

- [ ] Configurer les backups automatiques
- [ ] Documenter les endpoints API
- [ ] Optimiser les migrations Django si nécessaire

---

## Notes

- **Ne JAMAIS exécuter `docker-entrypoint.sh` directement** (voir tasks/lessons.md)
- Toujours utiliser `./deploy.sh` pour gérer le projet
- Le projet utilise Daphne (ASGI) pour supporter Django Channels

---

## Commandes Utiles

```bash
# Déploiement
./deploy.sh

# Voir les logs
docker compose logs -f web

# Accéder au shell Django
docker compose exec web python manage.py shell

# Exécuter les migrations
docker compose exec web python manage.py migrate

# Créer un superuser
docker compose exec web python manage.py createsuperuser
```

---

_Dernière mise à jour : 2026-03-25_
