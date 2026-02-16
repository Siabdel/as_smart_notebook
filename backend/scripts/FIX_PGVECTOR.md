# 🔧 Fix : "le type « vector » n'existe pas"

## ❌ Erreur Rencontrée

```
django.db.utils.ProgrammingError: ERREUR: le type « vector » n'existe pas
LINE 1: ...L, "content_length" integer NOT NULL, "embedding" vector(768...
```

## 🎯 Cause

L'extension **pgvector** n'est pas installée ou activée dans votre base de données PostgreSQL.

---

## ✅ Solution Complète

### **Option A : Utiliser le Script Automatique (RECOMMANDÉ)**

```bash
cd backend/scripts

# Rendre le script exécutable
chmod +x init_db.sh

# Exécuter (va tout installer automatiquement)
sudo ./init_db.sh
```

Le script va :
- ✅ Compiler et installer pgvector
- ✅ Créer la base de données
- ✅ Activer l'extension vector
- ✅ Tester que tout fonctionne

---

### **Option B : Installation Manuelle**

Si le script ne fonctionne pas, suivez ces étapes :

#### **Étape 1 : Installer les Dépendances de Compilation**

```bash
sudo apt-get update
sudo apt-get install -y build-essential postgresql-server-dev-all git
```

#### **Étape 2 : Compiler et Installer pgvector**

```bash
# Télécharger pgvector
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Compiler
make

# Installer (nécessite sudo)
sudo make install

# Nettoyage
cd /tmp
rm -rf pgvector
```

#### **Étape 3 : Activer l'Extension dans PostgreSQL**

```bash
# Se connecter à PostgreSQL en tant que superuser
sudo -u postgres psql

# Dans le shell PostgreSQL :
\c smartnotebook  # Connectez-vous à votre base de données

CREATE EXTENSION IF NOT EXISTS vector;

# Vérifier que l'extension est installée
\dx

# Vous devriez voir :
#  vector | 0.x.x | public | vector data type and ivfflat access method

# Quitter
\q
```

#### **Étape 4 : Vérifier l'Installation**

```bash
# Test rapide
sudo -u postgres psql -d smartnotebook -c "SELECT '1'::vector(3);"

# Si ça fonctionne, vous verrez :
#  vector 
# --------
#  [1,0,0]
```

---

## 🔍 Vérifications

### **1. Vérifier que pgvector est Compilé**

```bash
# Chercher le fichier vector.so
find /usr -name "vector.so" 2>/dev/null

# Devrait afficher quelque chose comme :
# /usr/lib/postgresql/14/lib/vector.so
```

### **2. Vérifier que l'Extension est Disponible**

```bash
sudo -u postgres psql -c "SELECT * FROM pg_available_extensions WHERE name='vector';"

# Devrait afficher :
#   name  | default_version | ...
# --------+-----------------+-----
#  vector | 0.x.x          | ...
```

### **3. Vérifier que l'Extension est Activée**

```bash
sudo -u postgres psql -d smartnotebook -c "\dx"

# Cherchez 'vector' dans la liste
```

---

## 🐛 Dépannage

### **Problème 1 : "postgresql-server-dev-all introuvable"**

```bash
# Sur Debian/Ubuntu, installer la version spécifique
sudo apt-get install postgresql-server-dev-14  # ou 15, 16 selon votre version

# Vérifier votre version PostgreSQL
psql --version
```

### **Problème 2 : "Permission denied" lors de make install**

```bash
# Assurez-vous d'utiliser sudo
sudo make install

# Ou changez les permissions du dossier PostgreSQL
sudo chmod -R 755 /usr/share/postgresql/
```

### **Problème 3 : "Extension vector does not exist"**

Si l'extension n'est pas disponible après l'installation :

```bash
# Redémarrer PostgreSQL
sudo systemctl restart postgresql

# Reconnecter et réessayer
sudo -u postgres psql -d smartnotebook -c "CREATE EXTENSION vector;"
```

### **Problème 4 : Version PostgreSQL trop Ancienne**

pgvector nécessite PostgreSQL 11+.

```bash
# Vérifier la version
psql --version

# Si < 11, mettre à jour PostgreSQL
sudo apt-get install postgresql-14
```

---

## 🚀 Après Installation de pgvector

### **1. Supprimer les Anciennes Migrations (si nécessaire)**

Si vous aviez déjà tenté de migrer :

```bash
cd backend

# Supprimer les fichiers de migration (SAUF __init__.py)
find apps/*/migrations -name "*.py" ! -name "__init__.py" -delete

# Supprimer l'historique des migrations dans la DB
python manage.py shell
```

Dans le shell Python :

```python
from django.db import connection
cursor = connection.cursor()

# Supprimer l'historique des migrations pour documents
cursor.execute("DELETE FROM django_migrations WHERE app='documents';")
connection.commit()

# Quitter
exit()
```

### **2. Recréer les Migrations**

```bash
# Créer les nouvelles migrations
python manage.py makemigrations

# Vous devriez voir :
# Migrations for 'documents':
#   apps/documents/migrations/0001_initial.py
#     - Create model SourceDocument
#     - Create model DocumentChunk
#     - Create model QueryLog

# Appliquer les migrations
python manage.py migrate

# Vous devriez voir :
# Running migrations:
#   Applying documents.0001_initial... OK
```

### **3. Vérifier que les Tables Existent**

```bash
sudo -u postgres psql -d smartnotebook

# Lister les tables
\dt

# Vérifier la structure de DocumentChunk
\d document_chunks

# Vous devriez voir la colonne "embedding" de type "vector(768)"
```

---

## 📋 Script de Vérification Complète

Créez `check_pgvector.sh` dans `backend/scripts/` :

```bash
#!/bin/bash

echo "🔍 Vérification de pgvector..."
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Vérifier que PostgreSQL tourne
echo -n "1. PostgreSQL service: "
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ Actif${NC}"
else
    echo -e "${RED}✗ Inactif${NC}"
    exit 1
fi

# 2. Vérifier que pgvector est compilé
echo -n "2. Fichier vector.so: "
if find /usr -name "vector.so" 2>/dev/null | grep -q vector.so; then
    echo -e "${GREEN}✓ Trouvé${NC}"
else
    echo -e "${RED}✗ Non trouvé${NC}"
    echo -e "${YELLOW}   → Exécutez: sudo ./init_db.sh${NC}"
    exit 1
fi

# 3. Vérifier que l'extension est disponible
echo -n "3. Extension disponible: "
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_available_extensions WHERE name='vector'" | grep -q 1; then
    echo -e "${GREEN}✓ Disponible${NC}"
else
    echo -e "${RED}✗ Non disponible${NC}"
    exit 1
fi

# 4. Vérifier que l'extension est activée
echo -n "4. Extension activée: "
DB_NAME=${1:-smartnotebook}
if sudo -u postgres psql -d "$DB_NAME" -tAc "SELECT 1 FROM pg_extension WHERE extname='vector'" | grep -q 1; then
    echo -e "${GREEN}✓ Activée${NC}"
else
    echo -e "${YELLOW}⚠ Non activée${NC}"
    echo -e "${YELLOW}   → Activation...${NC}"
    sudo -u postgres psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"
    echo -e "${GREEN}   ✓ Extension activée${NC}"
fi

# 5. Test fonctionnel
echo -n "5. Test fonctionnel: "
if sudo -u postgres psql -d "$DB_NAME" -tAc "SELECT '[1,2,3]'::vector(3);" &>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ Échec${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ pgvector est prêt !              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo "📋 Prochaines étapes:"
echo "   1. python manage.py makemigrations"
echo "   2. python manage.py migrate"
```

Utilisation :

```bash
chmod +x backend/scripts/check_pgvector.sh
./backend/scripts/check_pgvector.sh smartnotebook
```

---

## 🎯 Récapitulatif : Installation Complète

### **Commandes Rapides (tout en une fois)**

```bash
# 1. Installation automatique
cd backend/scripts
chmod +x init_db.sh
sudo ./init_db.sh

# 2. Vérification
chmod +x check_pgvector.sh
./check_pgvector.sh

# 3. Migrations Django
cd ..
python manage.py makemigrations
python manage.py migrate

# 4. Test
python manage.py shell
```

Dans le shell Python :

```python
from apps.documents.models import DocumentChunk
print("✅ Le modèle DocumentChunk est accessible !")
exit()
```

---

## 📊 Versions Testées

pgvector fonctionne avec :

| PostgreSQL | pgvector | Status |
|------------|----------|--------|
| 16.x | 0.5.x | ✅ |
| 15.x | 0.5.x | ✅ |
| 14.x | 0.5.x | ✅ |
| 13.x | 0.5.x | ✅ |
| 12.x | 0.5.x | ✅ |
| 11.x | 0.5.x | ✅ |

---

## 🆘 Toujours Bloqué ?

Si l'erreur persiste :

### **Option 1 : Réinstallation Propre**

```bash
# Supprimer pgvector
sudo rm -f /usr/lib/postgresql/*/lib/vector.so
sudo rm -f /usr/share/postgresql/*/extension/vector*

# Réinstaller
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make clean
make
sudo make install

# Redémarrer PostgreSQL
sudo systemctl restart postgresql

# Activer l'extension
sudo -u postgres psql -d smartnotebook -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### **Option 2 : Vérifier les Logs PostgreSQL**

```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

Cherchez des erreurs comme :
- `could not load library`
- `undefined symbol`

### **Option 3 : Installation via APT (Debian/Ubuntu)**

Si disponible dans vos dépôts :

```bash
sudo apt-get install postgresql-14-pgvector  # Adaptez selon votre version

sudo -u postgres psql -d smartnotebook -c "CREATE EXTENSION vector;"
```

---

## ✅ Une Fois pgvector Installé

L'erreur `le type « vector » n'existe pas` disparaîtra et vos migrations Django fonctionneront correctement ! 🎉

```bash
python manage.py migrate

# Output attendu :
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, documents, sessions
# Running migrations:
#   Applying documents.0001_initial... OK
```

---

**Besoin d'aide supplémentaire ? Partagez les logs d'erreur !** 🚀
