#!/bin/bash
set -e

echo "=== PromoCut - Démarrage ==="

# Backend
echo ""
echo "[Backend] Installation des dépendances..."
cd "$(dirname "$0")/backend"
pip install -r requirements.txt -q

echo "[Backend] Création des dossiers..."
mkdir -p uploads outputs assets/music

echo "[Backend] Démarrage de l'API (port 8000)..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Frontend
echo ""
cd "$(dirname "$0")/frontend"
echo "[Frontend] Installation des dépendances..."
npm install -q

echo "[Frontend] Démarrage du serveur de dev (port 3000)..."
npm run dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "======================================="
echo "  PromoCut est démarré !"
echo "  Frontend : http://localhost:3000"
echo "  Backend  : http://localhost:8000"
echo "  API docs : http://localhost:8000/docs"
echo "======================================="
echo ""
echo "Ctrl+C pour arrêter les deux serveurs."

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Serveurs arrêtés.'" EXIT
wait
