# Leçons Apprises - Loura Backend

> Ce fichier contient toutes les leçons apprises au fil du temps pour éviter de répéter les mêmes erreurs.

---

## [2026-03-25] docker-entrypoint.sh ne doit JAMAIS être exécuté directement sur l'hôte

### Ce qui s'est mal passé
- L'utilisateur a tenté d'exécuter `./docker-entrypoint.sh` directement sur l'hôte
- Erreur : `nc: getaddrinfo for host "db" port 5432: Temporary failure in name resolution`
- Le script ne pouvait pas résoudre le nom d'hôte "db" car il n'existait pas sur l'hôte

### Cause racine
- `docker-entrypoint.sh` est un **script d'initialisation de conteneur**, pas un script de déploiement
- Il est conçu pour s'exécuter **à l'intérieur d'un conteneur Docker**
- Le nom d'hôte "db" n'existe que dans le réseau Docker interne (`loura_network`)
- Sur l'hôte, ce nom d'hôte n'est pas résolvable

### Règle pour l'éviter
1. **JAMAIS exécuter `docker-entrypoint.sh` directement sur l'hôte**
2. **TOUJOURS utiliser `./deploy.sh`** pour lancer le projet
3. Le `docker-entrypoint.sh` sera automatiquement exécuté par Docker au démarrage du conteneur
4. Si on voit une erreur de résolution DNS pour "db", "redis" ou autre service, vérifier qu'on est bien dans un conteneur Docker

### Script correct à utiliser
```bash
# Pour déploiement
./deploy.sh

# Puis choisir :
# - Option 1 : Fresh deployment (première fois)
# - Option 3 : Start existing containers (si déjà construit)
# - Option 9 : Status check (vérifier l'état)
```

---

## [2026-04-15] Utiliser TokenService, pas AuthenticationService pour la génération de tokens

### Ce qui s'est mal passé
- Erreur `AttributeError: type object 'AuthenticationService' has no attribute 'generate_tokens_for_user'`
- Le code appelait `AuthenticationService.generate_tokens_for_user()` dans `hr/views.py:3609`
- Échec de l'acceptation d'invitation employé avec 500 Internal Server Error

### Cause racine
- La méthode `generate_tokens_for_user` appartient à la classe `TokenService` (ligne 293 dans `authentication/services.py`)
- L'architecture sépare les services en trois classes distinctes :
  - `AuthenticationService` : authentification, login, logout
  - `TokenService` : génération et gestion des tokens JWT
  - `ProfileService` : gestion du profil utilisateur
- Le code utilisait la mauvaise classe de service

### Règle pour l'éviter
1. **TOUJOURS utiliser `TokenService.generate_tokens_for_user()`** pour générer des tokens JWT
2. Vérifier l'architecture des services dans `authentication/services.py` :
   - `AuthenticationService` → login/logout/register
   - `TokenService` → tokens JWT
   - `ProfileService` → profil utilisateur
3. Ne jamais supposer qu'une méthode existe sans vérifier le code source
4. Import correct :
   ```python
   from authentication.services import TokenService
   tokens = TokenService.generate_tokens_for_user(user, user_type='employee')
   ```

---

## Template pour futures leçons

```
## [DATE] Titre court de la leçon

### Ce qui s'est mal passé
- Description du problème rencontré

### Cause racine
- Explication technique de pourquoi ça ne marchait pas

### Règle pour l'éviter
- Actions concrètes à prendre
- Commandes ou patterns à utiliser
```
