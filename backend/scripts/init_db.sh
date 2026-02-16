#!/bin/bash

###############################################################################
# Script d'initialisation de la base de données PostgreSQL avec pgvector
# pour Smart-Notebook
#
# Ce script configure PostgreSQL pour utiliser l'extension pgvector
# nécessaire pour le stockage et la recherche vectorielle.
#
# Prérequis:
# - PostgreSQL 12+ installé
# - Droits sudo
# - Extension pgvector compilée (voir instructions ci-dessous)
#
# Usage:
#   chmod +x init_db.sh
#   ./init_db.sh
###############################################################################

set -e  # Arrêt du script en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (modifiez selon vos besoins)
DB_NAME="smartnotebook"
DB_USER="smartnotebook_user"
DB_PASSWORD="votre_mot_de_passe_securise"  # ⚠️ CHANGEZ CE MOT DE PASSE
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Smart-Notebook - Initialisation PostgreSQL${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

###############################################################################
# 1. Vérification de PostgreSQL
###############################################################################

echo -e "${YELLOW}[1/6]${NC} Vérification de PostgreSQL..."

if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL n'est pas installé${NC}"
    echo -e "Installation sous Debian/Ubuntu:"
    echo -e "  sudo apt-get update"
    echo -e "  sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Vérification que le service tourne
if ! sudo systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}⚠️  PostgreSQL n'est pas démarré, tentative de démarrage...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

POSTGRES_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1)
echo -e "${GREEN}✅ PostgreSQL $POSTGRES_VERSION détecté${NC}"

###############################################################################
# 2. Installation de pgvector
###############################################################################

echo -e "${YELLOW}[2/6]${NC} Vérification de l'extension pgvector..."

# Vérification si pgvector est déjà installé
PGVECTOR_INSTALLED=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_available_extensions WHERE name='vector'" 2>/dev/null || echo "0")

if [ "$PGVECTOR_INSTALLED" != "1" ]; then
    echo -e "${YELLOW}⚠️  pgvector n'est pas installé. Installation en cours...${NC}"
    
    # Installation des dépendances de compilation
    echo -e "  → Installation des dépendances..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq build-essential postgresql-server-dev-all git
    
    # Clone et compilation de pgvector
    echo -e "  → Téléchargement de pgvector..."
    cd /tmp
    if [ -d "pgvector" ]; then
        rm -rf pgvector
    fi
    git clone --quiet https://github.com/pgvector/pgvector.git
    cd pgvector
    
    echo -e "  → Compilation de pgvector..."
    make -s
    sudo make install -s
    
    # Nettoyage
    cd /tmp
    rm -rf pgvector
    
    echo -e "${GREEN}✅ pgvector compilé et installé${NC}"
else
    echo -e "${GREEN}✅ pgvector déjà installé${NC}"
fi

###############################################################################
# 3. Création de l'utilisateur PostgreSQL
###############################################################################

echo -e "${YELLOW}[3/6]${NC} Création de l'utilisateur PostgreSQL..."

# Vérification si l'utilisateur existe déjà
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null || echo "0")

if [ "$USER_EXISTS" != "1" ]; then
    sudo -u postgres psql <<EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER USER $DB_USER CREATEDB;
EOF
    echo -e "${GREEN}✅ Utilisateur '$DB_USER' créé${NC}"
else
    echo -e "${GREEN}✅ Utilisateur '$DB_USER' existe déjà${NC}"
fi

###############################################################################
# 4. Création de la base de données
###############################################################################

echo -e "${YELLOW}[4/6]${NC} Création de la base de données..."

# Vérification si la DB existe déjà
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" != "1" ]; then
    sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
    echo -e "${GREEN}✅ Base de données '$DB_NAME' créée${NC}"
else
    echo -e "${GREEN}✅ Base de données '$DB_NAME' existe déjà${NC}"
fi

###############################################################################
# 5. Activation de l'extension pgvector
###############################################################################

echo -e "${YELLOW}[5/6]${NC} Activation de l'extension pgvector..."

sudo -u postgres psql -d $DB_NAME <<EOF
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Vérification de l'installation
VECTOR_ENABLED=$(sudo -u postgres psql -d $DB_NAME -tAc "SELECT 1 FROM pg_extension WHERE extname='vector'" 2>/dev/null || echo "0")

if [ "$VECTOR_ENABLED" = "1" ]; then
    echo -e "${GREEN}✅ Extension pgvector activée${NC}"
else
    echo -e "${RED}❌ Échec de l'activation de pgvector${NC}"
    exit 1
fi

###############################################################################
# 6. Test de connexion et configuration finale
###############################################################################

echo -e "${YELLOW}[6/6]${NC} Test de connexion et configuration finale..."

# Test de connexion
if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Connexion à la base de données réussie${NC}"
else
    echo -e "${RED}❌ Échec de connexion à la base de données${NC}"
    exit 1
fi

# Création de la table de test pour vérifier pgvector
echo -e "  → Test de pgvector..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME <<EOF
DROP TABLE IF EXISTS pgvector_test;
CREATE TABLE pgvector_test (
    id SERIAL PRIMARY KEY,
    embedding vector(768)
);

INSERT INTO pgvector_test (embedding) VALUES 
    (array_fill(0.1::real, ARRAY[768])::vector),
    (array_fill(0.2::real, ARRAY[768])::vector);

SELECT COUNT(*) FROM pgvector_test;

DROP TABLE pgvector_test;
EOF

echo -e "${GREEN}✅ pgvector fonctionne correctement${NC}"

###############################################################################
# Affichage des informations de connexion
###############################################################################

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Configuration terminée avec succès !${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📋 ${YELLOW}Informations de connexion:${NC}"
echo -e "   Database  : $DB_NAME"
echo -e "   User      : $DB_USER"
echo -e "   Password  : $DB_PASSWORD"
echo -e "   Host      : $DB_HOST"
echo -e "   Port      : $DB_PORT"
echo ""
echo -e "📝 ${YELLOW}Configuration Django (.env):${NC}"
echo -e "   DB_NAME=$DB_NAME"
echo -e "   DB_USER=$DB_USER"
echo -e "   DB_PASSWORD=$DB_PASSWORD"
echo -e "   DB_HOST=$DB_HOST"
echo -e "   DB_PORT=$DB_PORT"
echo ""
echo -e "🚀 ${YELLOW}Prochaines étapes:${NC}"
echo -e "   1. Copiez les variables ci-dessus dans votre fichier .env"
echo -e "   2. Exécutez: python manage.py makemigrations"
echo -e "   3. Exécutez: python manage.py migrate"
echo -e "   4. Créez un superuser: python manage.py createsuperuser"
echo ""
echo -e "${GREEN}✨ Votre base de données est prête pour Smart-Notebook !${NC}"
echo ""
