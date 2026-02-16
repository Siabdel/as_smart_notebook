#!/bin/bash

###############################################################################
# Smart-Notebook - Script d'Arrêt
# Arrête proprement tous les services
###############################################################################

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BACKEND_DIR="$(pwd)/backend"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║         SMART-NOTEBOOK - ARRÊT DES SERVICES               ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

###############################################################################
# Arrêt des services
###############################################################################

echo -e "${YELLOW}Arrêt en cours...${NC}"
echo ""

# Django
echo -e "${CYAN}[1/4]${NC} Arrêt de Django..."
if pgrep -f "manage.py runserver" > /dev/null; then
    pkill -f "manage.py runserver"
    echo -e "${GREEN}  ✓ Django arrêté${NC}"
else
    echo -e "${YELLOW}  ⚠️  Django n'était pas actif${NC}"
fi

# Celery Worker
echo -e "${CYAN}[2/4]${NC} Arrêt de Celery Worker..."
if pgrep -f "celery.*worker" > /dev/null; then
    pkill -f "celery.*worker"
    echo -e "${GREEN}  ✓ Celery Worker arrêté${NC}"
else
    echo -e "${YELLOW}  ⚠️  Celery Worker n'était pas actif${NC}"
fi

# Celery Beat
echo -e "${CYAN}[3/4]${NC} Arrêt de Celery Beat..."
if pgrep -f "celery.*beat" > /dev/null; then
    pkill -f "celery.*beat"
    echo -e "${GREEN}  ✓ Celery Beat arrêté${NC}"
else
    echo -e "${YELLOW}  ⚠️  Celery Beat n'était pas actif${NC}"
fi

# Frontend
echo -e "${CYAN}[4/4]${NC} Arrêt du serveur Frontend..."
if pgrep -f "http.server 8080" > /dev/null; then
    pkill -f "http.server 8080"
    echo -e "${GREEN}  ✓ Frontend arrêté${NC}"
else
    echo -e "${YELLOW}  ⚠️  Frontend n'était pas actif${NC}"
fi

# Nettoyage des fichiers PID
if [ -d "$BACKEND_DIR" ]; then
    rm -f "$BACKEND_DIR/.django.pid"
    rm -f "$BACKEND_DIR/.celery.pid"
    rm -f "$BACKEND_DIR/.beat.pid"
    rm -f "$BACKEND_DIR/.frontend.pid"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║        ✅ TOUS LES SERVICES ONT ÉTÉ ARRÊTÉS              ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}ℹ️  Note:${NC} PostgreSQL, Redis et Ollama continuent de tourner"
echo -e "   (services système). Pour les arrêter:"
echo ""
echo -e "   ${YELLOW}sudo systemctl stop postgresql${NC}"
echo -e "   ${YELLOW}sudo systemctl stop redis-server${NC}"
echo -e "   ${YELLOW}pkill ollama${NC}"
echo ""
echo -e "${CYAN}🔄 Pour redémarrer Smart-Notebook:${NC}"
echo -e "   ${GREEN}./start.sh${NC}"
echo ""
