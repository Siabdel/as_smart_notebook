#!/bin/bash

###############################################################################
# Script de Vérification et Installation de pgvector
# Vérifie si pgvector est installé et l'installe si nécessaire
###############################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DB_NAME=${1:-smartnotebook}

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          VÉRIFICATION ET INSTALLATION PGVECTOR            ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "Base de données cible: ${YELLOW}$DB_NAME${NC}"
echo ""

###############################################################################
# Fonctions
###############################################################################

check_step() {
    local step_name=$1
    local check_command=$2
    
    echo -n "Vérification: $step_name... "
    
    if eval "$check_command" &>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ ÉCHEC${NC}"
        return 1
    fi
}

###############################################################################
# Vérifications
###############################################################################

echo -e "${YELLOW}[1/6]${NC} Vérification de PostgreSQL..."

# PostgreSQL installé
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL n'est pas installé${NC}"
    exit 1
fi

# PostgreSQL actif
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}⚠️  PostgreSQL n'est pas actif, démarrage...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

POSTGRES_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1)
echo -e "${GREEN}✓ PostgreSQL $POSTGRES_VERSION détecté et actif${NC}"

###############################################################################
# Vérifier que la DB existe
###############################################################################

echo -e "${YELLOW}[2/6]${NC} Vérification de la base de données..."

if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${RED}❌ La base de données '$DB_NAME' n'existe pas${NC}"
    echo -e "${YELLOW}→ Créez-la avec: sudo -u postgres createdb $DB_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Base de données '$DB_NAME' trouvée${NC}"

###############################################################################
# Vérifier si pgvector est compilé
###############################################################################

echo -e "${YELLOW}[3/6]${NC} Vérification de pgvector (fichier .so)..."

VECTOR_SO=$(find /usr -name "vector.so" 2>/dev/null | head -n1)

if [ -z "$VECTOR_SO" ]; then
    echo -e "${RED}✗ pgvector n'est pas installé${NC}"
    echo -e "${YELLOW}→ Installation en cours...${NC}"
    
    # Installer les dépendances
    echo -e "${BLUE}  → Installation des dépendances...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq build-essential postgresql-server-dev-all git
    
    # Compiler pgvector
    echo -e "${BLUE}  → Téléchargement et compilation de pgvector...${NC}"
    cd /tmp
    if [ -d "pgvector" ]; then
        rm -rf pgvector
    fi
    git clone --quiet https://github.com/pgvector/pgvector.git
    cd pgvector
    make -s
    sudo make install -s
    
    # Nettoyage
    cd /tmp
    rm -rf pgvector
    
    echo -e "${GREEN}✓ pgvector compilé et installé${NC}"
else
    echo -e "${GREEN}✓ pgvector déjà installé: $VECTOR_SO${NC}"
fi

###############################################################################
# Redémarrer PostgreSQL
###############################################################################

echo -e "${YELLOW}[4/6]${NC} Redémarrage de PostgreSQL..."

sudo systemctl restart postgresql
sleep 2

echo -e "${GREEN}✓ PostgreSQL redémarré${NC}"

###############################################################################
# Vérifier que l'extension est disponible
###############################################################################

echo -e "${YELLOW}[5/6]${NC} Vérification de la disponibilité de l'extension..."

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_available_extensions WHERE name='vector'" | grep -q 1; then
    echo -e "${RED}❌ L'extension vector n'est pas disponible${NC}"
    echo -e "${YELLOW}→ Vérifiez les logs: sudo tail -f /var/log/postgresql/postgresql-*.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Extension vector disponible${NC}"

###############################################################################
# Activer l'extension dans la DB
###############################################################################

echo -e "${YELLOW}[6/6]${NC} Activation de l'extension dans la base de données..."

if sudo -u postgres psql -d "$DB_NAME" -tAc "SELECT 1 FROM pg_extension WHERE extname='vector'" | grep -q 1; then
    echo -e "${GREEN}✓ Extension déjà activée${NC}"
else
    echo -e "${BLUE}  → Activation de l'extension vector...${NC}"
    sudo -u postgres psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null
    echo -e "${GREEN}✓ Extension activée${NC}"
fi

###############################################################################
# Test fonctionnel
###############################################################################

echo ""
echo -e "${YELLOW}Test fonctionnel...${NC}"

if sudo -u postgres psql -d "$DB_NAME" -tAc "SELECT '[1,2,3]'::vector(3);" &>/dev/null; then
    echo -e "${GREEN}✓ Test réussi : pgvector fonctionne correctement${NC}"
else
    echo -e "${RED}❌ Test échoué${NC}"
    exit 1
fi

###############################################################################
# Résumé
###############################################################################

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║          ✅ PGVECTOR EST PRÊT !                           ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Informations:${NC}"

# Version de l'extension
VERSION=$(sudo -u postgres psql -d "$DB_NAME" -tAc "SELECT extversion FROM pg_extension WHERE extname='vector';")
echo -e "   Version pgvector : ${GREEN}$VERSION${NC}"
echo -e "   PostgreSQL      : ${GREEN}$POSTGRES_VERSION${NC}"
echo -e "   Base de données : ${GREEN}$DB_NAME${NC}"

echo ""
echo -e "${YELLOW}📋 Prochaines étapes:${NC}"
echo ""
echo -e "   1. Retournez dans votre dossier backend:"
echo -e "      ${BLUE}cd /chemin/vers/backend${NC}"
echo ""
echo -e "   2. Activez l'environnement virtuel:"
echo -e "      ${BLUE}source venv/bin/activate${NC}"
echo ""
echo -e "   3. Supprimez les anciennes migrations (si elles existent):"
echo -e "      ${BLUE}find apps/*/migrations -name '*.py' ! -name '__init__.py' -delete${NC}"
echo ""
echo -e "   4. Créez les nouvelles migrations:"
echo -e "      ${BLUE}python manage.py makemigrations${NC}"
echo ""
echo -e "   5. Appliquez les migrations:"
echo -e "      ${BLUE}python manage.py migrate${NC}"
echo ""
echo -e "${GREEN}✨ Votre base de données sera prête pour Smart-Notebook !${NC}"
echo ""
