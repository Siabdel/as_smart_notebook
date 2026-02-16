# 🚀 Smart-Notebook - Backend

Clone local de Google NotebookLM avec architecture IA hybride (Local + Cloud).

## 📋 Table des matières

- [Architecture](#-architecture)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [API Endpoints](#-api-endpoints)
- [Architecture Technique](#-architecture-technique)

## 🏗️ Architecture

### Stack Technique
- **Backend**: Django 5 + Django REST Framework
- **Base de données**: PostgreSQL 14+ avec extension pgvector
- **Tâches async**: Celery + Redis
- **IA Locale**: Ollama (embeddings avec nomic-embed-text)
- **IA Cloud**: OpenRouter (génération avec Claude 3.5 Sonnet)
- **TTS**: edge-tts (synthèse vocale sans GPU)

### Stratégie IA Hybride
```
┌─────────────────────────────────────────────────────────┐
│                    SMART-NOTEBOOK                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📄 Documents  →  🔄 Processing  →  💾 Vector DB        │
│                                                          │
│  ┌──────────────┐        ┌──────────────┐              │
│  │   OLLAMA     │        │  OPENROUTER  │              │
│  │   (Local)    │        │   (Cloud)    │              │
│  ├──────────────┤        ├──────────────┤              │
│  │ Embeddings   │        │ Text Gen     │              │
│  │ nomic-embed  │        │ Claude 3.5   │              │
│  │ 768 dims     │        │ DeepSeek     │              │
│  └──────────────┘        └──────────────┘              │
│         ↓                        ↓                       │
│  Vector Search ───────→ RAG Context → Answer           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Prérequis

### Logiciels requis
- **Python 3.11+**
- **PostgreSQL 14+** avec extension pgvector
- **Redis 6+**
- **Ollama** ([installation](https://ollama.ai/download))
- **Tesseract OCR** (optionnel, pour PDFs scannés)

### Matériel
- **RAM**: 8 GB minimum (16 GB recommandé)
- **GPU**: Optionnel (les embeddings Ollama tournent sur CPU)
- **Espace disque**: 10 GB pour Ollama + modèles

## 📦 Installation

### 1. Clone du projet
```bash
git clone https://github.com/votre-username/smart-notebook.git
cd smart-notebook/backend
```

### 2. Environnement virtuel Python
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installation des dépendances Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Installation de PostgreSQL et pgvector
```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Exécution du script d'initialisation
chmod +x scripts/init_db.sh
./scripts/init_db.sh
```

Le script va :
- ✅ Installer pgvector
- ✅ Créer la base de données
- ✅ Créer l'utilisateur PostgreSQL
- ✅ Activer l'extension vector

### 5. Installation de Redis
```bash
# Debian/Ubuntu
sudo apt-get install redis-server

# Démarrage du service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérification
redis-cli ping  # Doit retourner PONG
```

### 6. Installation d'Ollama
```bash
# Téléchargement et installation
curl -fsSL https://ollama.com/install.sh | sh

# Téléchargement du modèle d'embeddings
ollama pull nomic-embed-text

# Vérification
ollama list  # Doit afficher nomic-embed-text
```

### 7. Installation de Tesseract (optionnel, pour OCR)
```bash
# Debian/Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

## ⚙️ Configuration

### 1. Variables d'environnement
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos vraies valeurs
nano .env
```

Variables importantes à modifier :
```bash
SECRET_KEY=votre-clé-secrète-django
OPENROUTER_API_KEY=sk-or-v1-votre-clé-ici
DB_PASSWORD=votre-mot-de-passe-db
```

### 2. Migrations Django
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Création d'un superutilisateur
```bash
python manage.py createsuperuser
```

### 4. Collecte des fichiers statiques
```bash
python manage.py collectstatic --noinput
```

## 🚀 Utilisation

### Démarrage du serveur Django
```bash
python manage.py runserver
```

Accès : http://localhost:8000

### Démarrage de Celery Worker
**Terminal 2** :
```bash
celery -A config worker --loglevel=info
```

### Démarrage de Celery Beat (tâches périodiques)
**Terminal 3** :
```bash
celery -A config beat --loglevel=info
```

### Démarrage complet avec un seul script (optionnel)
```bash
# Créer un fichier start.sh
cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python manage.py runserver &
celery -A config worker --loglevel=info &
celery -A config beat --loglevel=info &
wait
EOF

chmod +x start.sh
./start.sh
```

## 📡 API Endpoints

### Documents
```http
POST   /api/documents/upload/          # Upload d'un PDF/TXT
GET    /api/documents/                 # Liste des documents
GET    /api/documents/<id>/            # Détails d'un document
DELETE /api/documents/<id>/            # Suppression
POST   /api/documents/<id>/reprocess/  # Retraitement
```

### RAG (Question-Réponse)
```http
POST   /api/rag/ask/                   # Poser une question
GET    /api/rag/stats/                 # Statistiques utilisateur
POST   /api/rag/feedback/              # Noter une réponse
```

### Exemple d'utilisation
```bash
# Upload d'un document
curl -X POST http://localhost:8000/api/documents/upload/ \
  -H "Authorization: Token votre-token" \
  -F "file=@rapport.pdf" \
  -F "title=Rapport annuel 2024"

# Poser une question
curl -X POST http://localhost:8000/api/rag/ask/ \
  -H "Authorization: Token votre-token" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la conclusion principale du rapport?",
    "document_ids": [1, 2],
    "top_k": 5
  }'
```

## 🏛️ Architecture Technique

### Flux d'ingestion de documents
```
1. User upload PDF
   ↓
2. Validation (type MIME, taille, hash)
   ↓
3. Sauvegarde en DB (status: PENDING)
   ↓
4. Tâche Celery déclenchée
   ↓
5. Extraction texte (pypdf ou OCR)
   ↓
6. Chunking intelligent (overlap)
   ↓
7. Génération embeddings (Ollama local)
   ↓
8. Sauvegarde chunks + vecteurs (pgvector)
   ↓
9. Update status: COMPLETED
```

### Flux RAG (Question → Réponse)
```
1. User question
   ↓
2. Vectorisation question (Ollama)
   ↓
3. Recherche similarité L2 (pgvector SQL)
   ↓
4. Récupération top-K chunks
   ↓
5. Construction contexte RAG
   ↓
6. Appel LLM (OpenRouter Claude)
   ↓
7. Réponse + sources citées
```

### Modèles de données
- **SourceDocument** : Métadonnées du PDF/TXT
- **DocumentChunk** : Fragments avec embeddings (vector[768])
- **QueryLog** : Historique des questions + analytics

## 🧪 Tests

### Test de connexion Ollama
```bash
curl http://localhost:11434/api/tags
```

### Test de connexion PostgreSQL
```bash
psql -h localhost -U smartnotebook_user -d smartnotebook -c "SELECT version();"
```

### Test de l'API
```bash
python manage.py shell
>>> from apps.core.ai_router import get_ai_router
>>> router = get_ai_router()
>>> router.test_ollama_connection()
>>> router.test_openrouter_connection()
```

## 📊 Monitoring

### Logs Django
```bash
tail -f logs/django.log
```

### Logs Celery
```bash
tail -f logs/celery.log
```

### Monitoring Redis
```bash
redis-cli
> INFO
> MONITOR
```

## 🔒 Sécurité

### En production
- ✅ Changez `SECRET_KEY`
- ✅ Désactivez `DEBUG=False`
- ✅ Configurez HTTPS
- ✅ Restreignez `ALLOWED_HOSTS`
- ✅ Utilisez des mots de passe forts
- ✅ Activez le rate limiting

## 🐛 Dépannage

### Problème : Ollama ne démarre pas
```bash
sudo systemctl status ollama
sudo systemctl restart ollama
```

### Problème : pgvector non trouvé
```bash
# Réinstaller l'extension
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
sudo -u postgres psql -d smartnotebook -c "CREATE EXTENSION vector;"
```

### Problème : Celery worker crash
```bash
# Vérifier Redis
redis-cli ping

# Relancer avec verbose
celery -A config worker --loglevel=debug
```

## 📝 Licence

MIT License

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou une PR.

## 📞 Support

- Documentation : https://docs.smart-notebook.dev
- Issues : https://github.com/votre-username/smart-notebook/issues

---

Fait avec ❤️ pour la communauté open-source
