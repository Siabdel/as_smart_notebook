#!/bin/bash

###############################################################################
# Smart-Notebook - Script de Démarrage Complet
# Lance tous les services nécessaires dans des terminaux séparés
###############################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
BACKEND_DIR="$(pwd)/backend"
FRONTEND_DIR="$(pwd)/frontend"
VENV_PATH="$BACKEND_DIR/venv"

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║           SMART-NOTEBOOK - STARTUP SCRIPT                 ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

###############################################################################
# Vérifications préliminaires
###############################################################################

echo -e "${YELLOW}[1/8]${NC} Vérification des prérequis..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Python 3 détecté${NC}"

# Vérifier PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL n'est pas installé${NC}"
    exit 1
fi
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}  ⚠️  PostgreSQL n'est pas démarré, démarrage...${NC}"
    sudo systemctl start postgresql
fi
echo -e "${GREEN}  ✓ PostgreSQL actif${NC}"

# Vérifier Redis
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}❌ Redis n'est pas installé${NC}"
    exit 1
fi
if ! redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Redis n'est pas démarré, démarrage...${NC}"
    sudo systemctl start redis-server
    sleep 2
fi
echo -e "${GREEN}  ✓ Redis actif${NC}"

# Vérifier Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama n'est pas installé${NC}"
    echo -e "   Installation: ${BLUE}curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi

# Vérifier que le service Ollama tourne
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}  ⚠️  Ollama n'est pas démarré, démarrage...${NC}"
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi
echo -e "${GREEN}  ✓ Ollama actif${NC}"

# Vérifier le modèle d'embedding
if ! ollama list | grep -q "nomic-embed-text"; then
    echo -e "${YELLOW}  ⚠️  Modèle nomic-embed-text non trouvé, téléchargement...${NC}"
    ollama pull nomic-embed-text
fi
echo -e "${GREEN}  ✓ Modèle nomic-embed-text disponible${NC}"

###############################################################################
# Vérifier l'environnement virtuel Python
###############################################################################

echo -e "${YELLOW}[2/8]${NC} Vérification de l'environnement virtuel..."

if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}  ⚠️  Environnement virtuel non trouvé, création...${NC}"
    cd "$BACKEND_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    echo -e "${GREEN}  ✓ Environnement virtuel créé${NC}"
else
    echo -e "${GREEN}  ✓ Environnement virtuel détecté${NC}"
fi

###############################################################################
# Vérifier la base de données
###############################################################################

echo -e "${YELLOW}[3/8]${NC} Vérification de la base de données..."

source "$VENV_PATH/bin/activate"
cd "$BACKEND_DIR"

# Vérifier si la DB existe
DB_NAME=$(grep "^DB_NAME=" .env 2>/dev/null | cut -d'=' -f2 || echo "smartnotebook")
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}  ⚠️  Base de données non trouvée${NC}"
    echo -e "${BLUE}  → Exécutez d'abord: ./scripts/init_db.sh${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Base de données '$DB_NAME' active${NC}"

# Appliquer les migrations
echo -e "${BLUE}  → Application des migrations...${NC}"
python manage.py migrate --noinput > /dev/null 2>&1
echo -e "${GREEN}  ✓ Migrations appliquées${NC}"

###############################################################################
# Vérifier le fichier .env
###############################################################################

echo -e "${YELLOW}[4/8]${NC} Vérification de la configuration..."

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${YELLOW}  ⚠️  Fichier .env non trouvé${NC}"
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        echo -e "${BLUE}  → Copie de .env.example vers .env${NC}"
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo -e "${MAGENTA}  ⚠️  ATTENTION: Éditez .env avec vos vraies valeurs !${NC}"
    fi
fi

# Vérifier la clé OpenRouter
if ! grep -q "OPENROUTER_API_KEY=sk-" "$BACKEND_DIR/.env" 2>/dev/null; then
    echo -e "${MAGENTA}  ⚠️  OPENROUTER_API_KEY non configurée dans .env${NC}"
    echo -e "${BLUE}  → Le chat RAG ne fonctionnera pas sans clé API${NC}"
fi

echo -e "${GREEN}  ✓ Configuration chargée${NC}"

###############################################################################
# Fonction pour détecter le terminal
###############################################################################

detect_terminal() {
    if command -v gnome-terminal &> /dev/null; then
        echo "gnome-terminal"
    elif command -v konsole &> /dev/null; then
        echo "konsole"
    elif command -v xfce4-terminal &> /dev/null; then
        echo "xfce4-terminal"
    elif command -v xterm &> /dev/null; then
        echo "xterm"
    else
        echo "none"
    fi
}

TERMINAL=$(detect_terminal)

###############################################################################
# Démarrage des services
###############################################################################

echo -e "${YELLOW}[5/8]${NC} Démarrage de Django..."

if [ "$TERMINAL" != "none" ]; then
    # Lancer dans un nouveau terminal
    case $TERMINAL in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Django Development Server ===${NC}' && python manage.py runserver; exec bash" &
            ;;
        konsole)
            konsole -e bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Django Development Server ===${NC}' && python manage.py runserver; exec bash" &
            ;;
        xfce4-terminal)
            xfce4-terminal -e "bash -c 'cd $BACKEND_DIR && source venv/bin/activate && echo -e \"${GREEN}=== Django Development Server ===${NC}\" && python manage.py runserver; exec bash'" &
            ;;
        xterm)
            xterm -e "cd $BACKEND_DIR && source venv/bin/activate && echo -e '${GREEN}=== Django Development Server ===${NC}' && python manage.py runserver; exec bash" &
            ;;
    esac
    echo -e "${GREEN}  ✓ Django lancé dans un nouveau terminal${NC}"
else
    # Lancer en arrière-plan si pas de terminal graphique
    cd "$BACKEND_DIR"
    source venv/bin/activate
    python manage.py runserver > logs/django.log 2>&1 &
    DJANGO_PID=$!
    echo -e "${GREEN}  ✓ Django lancé en arrière-plan (PID: $DJANGO_PID)${NC}"
fi

sleep 3

###############################################################################
# Démarrage de Celery Worker
###############################################################################

echo -e "${YELLOW}[6/8]${NC} Démarrage de Celery Worker..."

if [ "$TERMINAL" != "none" ]; then
    case $TERMINAL in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Celery Worker ===${NC}' && celery -A config worker --loglevel=info; exec bash" &
            ;;
        konsole)
            konsole -e bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Celery Worker ===${NC}' && celery -A config worker --loglevel=info; exec bash" &
            ;;
        xfce4-terminal)
            xfce4-terminal -e "bash -c 'cd $BACKEND_DIR && source venv/bin/activate && echo -e \"${GREEN}=== Celery Worker ===${NC}\" && celery -A config worker --loglevel=info; exec bash'" &
            ;;
        xterm)
            xterm -e "cd $BACKEND_DIR && source venv/bin/activate && echo -e '${GREEN}=== Celery Worker ===${NC}' && celery -A config worker --loglevel=info; exec bash" &
            ;;
    esac
    echo -e "${GREEN}  ✓ Celery Worker lancé dans un nouveau terminal${NC}"
else
    cd "$BACKEND_DIR"
    source venv/bin/activate
    celery -A config worker --loglevel=info > logs/celery.log 2>&1 &
    CELERY_PID=$!
    echo -e "${GREEN}  ✓ Celery Worker lancé en arrière-plan (PID: $CELERY_PID)${NC}"
fi

sleep 2

###############################################################################
# Démarrage de Celery Beat (optionnel)
###############################################################################

echo -e "${YELLOW}[7/8]${NC} Démarrage de Celery Beat..."

if [ "$TERMINAL" != "none" ]; then
    case $TERMINAL in
        gnome-terminal)
            gnome-terminal -- bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Celery Beat ===${NC}' && celery -A config beat --loglevel=info; exec bash" &
            ;;
        konsole)
            konsole -e bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && echo -e '${GREEN}=== Celery Beat ===${NC}' && celery -A config beat --loglevel=info; exec bash" &
            ;;
        xfce4-terminal)
            xfce4-terminal -e "bash -c 'cd $BACKEND_DIR && source venv/bin/activate && echo -e \"${GREEN}=== Celery Beat ===${NC}\" && celery -A config beat --loglevel=info; exec bash'" &
            ;;
        xterm)
            xterm -e "cd $BACKEND_DIR && source venv/bin/activate && echo -e '${GREEN}=== Celery Beat ===${NC}' && celery -A config beat --loglevel=info; exec bash" &
            ;;
    esac
    echo -e "${GREEN}  ✓ Celery Beat lancé dans un nouveau terminal${NC}"
else
    cd "$BACKEND_DIR"
    source venv/bin/activate
    celery -A config beat --loglevel=info > logs/celery-beat.log 2>&1 &
    BEAT_PID=$!
    echo -e "${GREEN}  ✓ Celery Beat lancé en arrière-plan (PID: $BEAT_PID)${NC}"
fi

sleep 2

###############################################################################
# Démarrage du Frontend
###############################################################################

echo -e "${YELLOW}[8/8]${NC} Démarrage du serveur Frontend..."

# Vérifier si le fichier index.html existe
if [ ! -f "$FRONTEND_DIR/index.html" ]; then
    echo -e "${RED}  ❌ Fichier index.html non trouvé dans $FRONTEND_DIR${NC}"
    echo -e "${BLUE}  → Placez le fichier index.html dans le dossier frontend/${NC}"
else
    cd "$FRONTEND_DIR"
    
    if [ "$TERMINAL" != "none" ]; then
        case $TERMINAL in
            gnome-terminal)
                gnome-terminal -- bash -c "cd '$FRONTEND_DIR' && echo -e '${GREEN}=== Frontend Server (http://localhost:8080) ===${NC}' && python3 -m http.server 8080; exec bash" &
                ;;
            konsole)
                konsole -e bash -c "cd '$FRONTEND_DIR' && echo -e '${GREEN}=== Frontend Server (http://localhost:8080) ===${NC}' && python3 -m http.server 8080; exec bash" &
                ;;
            xfce4-terminal)
                xfce4-terminal -e "bash -c 'cd $FRONTEND_DIR && echo -e \"${GREEN}=== Frontend Server (http://localhost:8080) ===${NC}\" && python3 -m http.server 8080; exec bash'" &
                ;;
            xterm)
                xterm -e "cd $FRONTEND_DIR && echo -e '${GREEN}=== Frontend Server (http://localhost:8080) ===${NC}' && python3 -m http.server 8080; exec bash" &
                ;;
        esac
        echo -e "${GREEN}  ✓ Frontend lancé dans un nouveau terminal${NC}"
    else
        python3 -m http.server 8080 > /dev/null 2>&1 &
        FRONTEND_PID=$!
        echo -e "${GREEN}  ✓ Frontend lancé en arrière-plan (PID: $FRONTEND_PID)${NC}"
    fi
fi

sleep 2

###############################################################################
# Résumé et accès
###############################################################################

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║          ✅ SMART-NOTEBOOK DÉMARRÉ AVEC SUCCÈS !          ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📊 Services actifs:${NC}"
echo -e "   ${GREEN}✓${NC} PostgreSQL  → Port 5432"
echo -e "   ${GREEN}✓${NC} Redis       → Port 6379"
echo -e "   ${GREEN}✓${NC} Ollama      → http://localhost:11434"
echo -e "   ${GREEN}✓${NC} Django      → http://localhost:8000"
echo -e "   ${GREEN}✓${NC} Celery      → Worker + Beat actifs"
echo -e "   ${GREEN}✓${NC} Frontend    → http://localhost:8080"
echo ""
echo -e "${CYAN}🌐 Accès:${NC}"
echo -e "   ${BLUE}→ Interface Web:${NC}  http://localhost:8080"
echo -e "   ${BLUE}→ API Backend:${NC}    http://localhost:8000/api"
echo -e "   ${BLUE}→ Django Admin:${NC}   http://localhost:8000/admin"
echo ""
echo -e "${CYAN}📝 Logs:${NC}"
echo -e "   ${BLUE}→ Django:${NC}  tail -f $BACKEND_DIR/logs/django.log"
echo -e "   ${BLUE}→ Celery:${NC}  tail -f $BACKEND_DIR/logs/celery.log"
echo ""
echo -e "${CYAN}🛑 Pour arrêter tous les services:${NC}"
echo -e "   ${BLUE}→ Exécutez:${NC} ./stop.sh"
echo -e "   ${BLUE}→ Ou:${NC}       pkill -f 'manage.py runserver'"
echo -e "                pkill -f 'celery'"
echo -e "                pkill -f 'http.server 8080'"
echo ""
echo -e "${YELLOW}⚡ Conseil:${NC} Ouvrez http://localhost:8080 dans votre navigateur !"
echo ""

# Ouvrir automatiquement dans le navigateur par défaut (optionnel)
if command -v xdg-open &> /dev/null; then
    sleep 3
    xdg-open http://localhost:8080 &> /dev/null &
    echo -e "${GREEN}✨ Navigateur ouvert automatiquement !${NC}"
fi

# Sauvegarder les PIDs pour l'arrêt ultérieur
if [ "$TERMINAL" == "none" ]; then
    echo "$DJANGO_PID" > "$BACKEND_DIR/.django.pid"
    echo "$CELERY_PID" > "$BACKEND_DIR/.celery.pid"
    echo "$BEAT_PID" > "$BACKEND_DIR/.beat.pid"
    echo "$FRONTEND_PID" > "$BACKEND_DIR/.frontend.pid"
fi

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
