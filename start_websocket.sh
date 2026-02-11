#!/bin/bash

# Script pour démarrer le serveur Django avec support WebSocket (Daphne)

cd "$(dirname "$0")/app"

# Activer l'environnement virtuel
source ../venv/bin/activate

echo "🚀 Démarrage du serveur ASGI avec Daphne..."
echo "📍 WebSocket disponible sur: ws://localhost:8000/ws/notifications/"
echo "📍 API HTTP disponible sur: http://localhost:8000/api/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

# Démarrer Daphne avec auto-reload en développement
daphne -b 0.0.0.0 -p 8000 lourabackend.asgi:application
