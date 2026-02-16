# 📦 Smart-Notebook - Fichiers Générés

## 🎯 Récapitulatif Complet

Tous les fichiers essentiels pour démarrer votre clone de NotebookLM ont été générés avec succès !

---

## 📂 Liste des Fichiers

### 🔧 Configuration & Installation

#### 1. **requirements.txt** 
- Toutes les dépendances Python nécessaires
- Django 5, DRF, Celery, pgvector, OpenAI SDK, etc.
- **Emplacement**: Racine du projet backend

#### 2. **env_example.txt** (à renommer en `.env`)
- Variables d'environnement complètes
- Clés API, configuration DB, Ollama, OpenRouter
- **Emplacement**: Racine du projet backend
- **Action requise**: Renommer en `.env` et remplir vos vraies valeurs

#### 3. **init_db.sh**
- Script Bash d'initialisation PostgreSQL + pgvector
- Crée la DB, l'utilisateur, active l'extension
- **Emplacement**: `scripts/init_db.sh`
- **Usage**: `chmod +x init_db.sh && ./init_db.sh`

#### 4. **django_settings.py**
- Configuration Django complète (settings.py)
- PostgreSQL, Celery, CORS, Logging, etc.
- **Emplacement**: `config/settings.py`

#### 5. **celery_config.py**
- Configuration Celery avec queues et tâches périodiques
- **Emplacement**: `config/celery.py`

---

### 🏗️ Modèles Django

#### 6. **documents_models.py**
- `SourceDocument`: Documents uploadés (PDFs, TXT)
- `DocumentChunk`: Fragments vectorisés avec pgvector
- `QueryLog`: Historique des questions RAG
- **Emplacement**: `apps/documents/models.py`

---

### 🤖 Intelligence Artificielle

#### 7. **ai_router.py**
- Classe `AIRouter` qui gère Ollama (local) + OpenRouter (cloud)
- Méthodes: `get_embedding()`, `chat_completion()`
- Gestion d'erreurs robuste
- **Emplacement**: `apps/core/ai_router.py`

---

### ⚙️ Tâches Asynchrones

#### 8. **tasks.py**
- Tâches Celery pour ingestion de documents
- `process_document_ingestion()`: extraction, chunking, embeddings
- `cleanup_failed_documents()`: maintenance périodique
- **Emplacement**: `apps/documents/tasks.py`

---

### 🌐 API REST

#### 9. **views.py**
- `AskDocumentView`: Endpoint RAG principal
- `DocumentStatsView`: Statistiques utilisateur
- `RateFeedbackView`: Notation des réponses
- **Emplacement**: `apps/rag/views.py`

#### 10. **serializers.py**
- Serializers DRF pour upload, validation, RAG
- `DocumentUploadSerializer`, `AskQuestionSerializer`, etc.
- **Emplacement**: `apps/documents/serializers.py`

---

### 🧪 Tests & Utilitaires

#### 11. **test_ollama.py**
- Script de test pour vérifier Ollama
- Teste la connexion, les embeddings, la similarité
- **Emplacement**: `scripts/test_ollama.py`
- **Usage**: `python scripts/test_ollama.py`

---

### 📚 Documentation

#### 12. **README_BACKEND.md**
- Documentation complète du backend
- Installation, configuration, architecture, API
- Dépannage et bonnes pratiques
- **Emplacement**: `README.md` (racine backend)

---

## 🚀 Guide de Démarrage Rapide

### 1️⃣ Installer les prérequis
```bash
# PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Redis
sudo apt-get install redis-server

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# Tesseract (optionnel)
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

### 2️⃣ Initialiser la base de données
```bash
chmod +x scripts/init_db.sh
./scripts/init_db.sh
```

### 3️⃣ Installer les dépendances Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4️⃣ Configurer l'environnement
```bash
cp env_example.txt .env
nano .env  # Remplir vos valeurs
```

### 5️⃣ Lancer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6️⃣ Démarrer les services
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker --loglevel=info

# Terminal 3: Celery Beat
celery -A config beat --loglevel=info
```

---

## 📋 Structure Recommandée du Projet

```
backend/
├── manage.py
├── requirements.txt
├── .env                          # ← À créer depuis env_example.txt
├── README.md                      # ← README_BACKEND.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py                # ← django_settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py                  # ← celery_config.py
│
├── apps/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ai_router.py           # ← ai_router.py
│   │   └── ...
│   │
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── models.py              # ← documents_models.py
│   │   ├── serializers.py         # ← serializers.py
│   │   ├── views.py               # ← (création views upload)
│   │   ├── urls.py
│   │   └── tasks.py               # ← tasks.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── views.py               # ← views.py
│   │   ├── serializers.py         # ← (partie RAG de serializers.py)
│   │   └── urls.py
│   │
│   └── podcasts/
│       └── ...
│
├── scripts/
│   ├── init_db.sh                 # ← init_db.sh
│   └── test_ollama.py             # ← test_ollama.py
│
├── media/
│   ├── documents/
│   └── podcasts/
│
└── logs/
    ├── django.log
    └── celery.log
```

---

## ✅ Checklist de Vérification

- [ ] PostgreSQL installé et configuré
- [ ] pgvector installé via `init_db.sh`
- [ ] Redis démarré (`redis-cli ping` → PONG)
- [ ] Ollama installé et modèle téléchargé (`ollama list`)
- [ ] Variables `.env` configurées
- [ ] Migrations Django exécutées
- [ ] Superuser créé
- [ ] Test Ollama réussi (`python scripts/test_ollama.py`)
- [ ] Django démarre sans erreur
- [ ] Celery worker connecté

---

## 🎓 Concepts Clés

### Architecture Hybride IA
- **Local (Ollama)**: Embeddings uniquement (économise les coûts API)
- **Cloud (OpenRouter)**: Génération de texte (meilleure qualité)

### Workflow RAG
1. Upload PDF → Extraction texte → Chunking
2. Génération embeddings (Ollama) → Stockage pgvector
3. Question utilisateur → Vectorisation → Recherche similarité
4. Contexte + Question → LLM (OpenRouter) → Réponse citée

### Technologies Critiques
- **pgvector**: Extension PostgreSQL pour recherche vectorielle L2
- **Celery**: Traitement asynchrone (ingestion longue durée)
- **Redis**: Message broker pour Celery
- **Ollama**: LLM local pour embeddings (RTX 3060 compatible)

---

## 🆘 Besoin d'Aide ?

### Problèmes Courants

**Ollama ne démarre pas**
```bash
sudo systemctl status ollama
sudo systemctl restart ollama
```

**pgvector non trouvé**
```bash
sudo -u postgres psql -d smartnotebook -c "CREATE EXTENSION vector;"
```

**Celery ne trouve pas les tâches**
```bash
# Vérifier que __init__.py existe dans apps/documents/
# Relancer avec: celery -A config worker --loglevel=debug
```

---

## 📞 Ressources Additionnelles

- **Ollama Docs**: https://ollama.ai/docs
- **pgvector Repo**: https://github.com/pgvector/pgvector
- **OpenRouter API**: https://openrouter.ai/docs
- **Celery Docs**: https://docs.celeryq.dev
- **Django Docs**: https://docs.djangoproject.com

---

## 🎉 Félicitations !

Vous avez maintenant tous les fichiers nécessaires pour construire votre clone de NotebookLM. 

**Prochaines étapes suggérées**:
1. Installer et tester le backend
2. Créer le frontend Vue.js 3
3. Intégrer la génération de podcasts (edge-tts)
4. Déployer en production

Bon développement ! 🚀
