# 🚀 Smart-Notebook - Guide de Démarrage Rapide

## ⚡ Installation en 5 Minutes

### 1️⃣ Structure du Projet

Créez cette arborescence :

```
smart-notebook/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                    # ← À créer depuis env_example.txt
│   ├── config/
│   │   ├── settings.py         # ← django_settings.py
│   │   └── celery.py           # ← celery_config.py
│   ├── apps/
│   │   ├── core/
│   │   │   └── ai_router.py    # ← ai_router.py
│   │   ├── documents/
│   │   │   ├── models.py       # ← documents_models.py
│   │   │   ├── serializers.py  # ← serializers.py
│   │   │   └── tasks.py        # ← tasks.py
│   │   └── rag/
│   │       └── views.py        # ← views.py
│   ├── scripts/
│   │   ├── init_db.sh          # ← init_db.sh
│   │   └── test_ollama.py      # ← test_ollama.py
│   ├── media/
│   └── logs/
│
├── frontend/
│   └── index.html              # ← index.html
│
├── start.sh                    # ← start.sh
└── stop.sh                     # ← stop.sh
```

### 2️⃣ Installation des Prérequis

```bash
# PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Redis
sudo apt-get install redis-server

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text

# Tesseract OCR (optionnel)
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# Python 3
sudo apt-get install python3 python3-venv python3-pip
```

### 3️⃣ Configuration du Backend

```bash
# Créer l'environnement virtuel
cd backend
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
chmod +x scripts/init_db.sh
./scripts/init_db.sh

# Configurer l'environnement
cp env_example.txt .env
nano .env  # Éditez vos valeurs

# Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Créer un token API
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from rest_framework.authtoken.models import Token
>>> user = User.objects.get(username='votre-username')
>>> token, created = Token.objects.get_or_create(user=user)
>>> print(f"Token: {token.key}")
>>> exit()
```

### 4️⃣ Configuration du Frontend

```bash
cd ../frontend

# Éditer index.html
nano index.html

# Modifier ces lignes (vers ligne 685) :
apiBaseUrl: 'http://localhost:8000/api',
authToken: 'votre-token-copié-ci-dessus',
```

### 5️⃣ Démarrage !

```bash
# Retour à la racine du projet
cd ..

# Rendre les scripts exécutables
chmod +x start.sh stop.sh

# Démarrer tous les services
./start.sh
```

Le script `start.sh` va :
- ✅ Vérifier tous les prérequis
- ✅ Démarrer PostgreSQL et Redis
- ✅ Démarrer Ollama
- ✅ Lancer Django (http://localhost:8000)
- ✅ Lancer Celery Worker
- ✅ Lancer Celery Beat
- ✅ Lancer le Frontend (http://localhost:8080)
- ✅ Ouvrir automatiquement votre navigateur

---

## 🎯 Accès Rapide

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8080 | Interface utilisateur |
| **API Backend** | http://localhost:8000/api | API REST |
| **Django Admin** | http://localhost:8000/admin | Interface d'admin |
| **Ollama** | http://localhost:11434 | Service d'embeddings |

---

## 🔑 Variables d'Environnement Essentielles

Dans `backend/.env` :

```bash
# Django
SECRET_KEY=votre-clé-secrète-générée
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (rempli automatiquement par init_db.sh)
DB_NAME=smartnotebook
DB_USER=smartnotebook_user
DB_PASSWORD=votre-mot-de-passe

# OpenRouter (OBLIGATOIRE pour le chat)
OPENROUTER_API_KEY=sk-or-v1-votre-clé-ici

# Ollama (déjà configuré par défaut)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**⚠️ IMPORTANT** : Obtenez votre clé OpenRouter sur https://openrouter.ai/keys

---

## 🧪 Tester l'Installation

### Test 1 : Ollama
```bash
cd backend
source venv/bin/activate
python scripts/test_ollama.py
```

### Test 2 : Backend API
```bash
curl http://localhost:8000/api/rag/stats/
```

### Test 3 : Upload un PDF
1. Ouvrez http://localhost:8080
2. Glissez un PDF dans la zone d'upload
3. Attendez le traitement (status COMPLETED)
4. Posez une question dans le chat

---

## 🛑 Arrêter les Services

```bash
./stop.sh
```

---

## 🐛 Dépannage Express

### Problème : "Connection refused" sur l'API
```bash
# Vérifier que Django tourne
ps aux | grep "manage.py runserver"

# Relancer si nécessaire
cd backend
source venv/bin/activate
python manage.py runserver
```

### Problème : "Ollama not found"
```bash
# Vérifier Ollama
ollama list

# Si absent, installer
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text
```

### Problème : "pgvector extension not found"
```bash
cd backend
./scripts/init_db.sh
```

### Problème : "CORS Error" dans le navigateur
```bash
# Vérifier CORS dans backend/config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
]
```

### Problème : "401 Unauthorized"
```bash
# Vérifier le token dans frontend/index.html
authToken: 'votre-token-ici'
```

---

## 📊 Monitoring

### Logs Django
```bash
tail -f backend/logs/django.log
```

### Logs Celery
```bash
tail -f backend/logs/celery.log
```

### Status des services
```bash
# PostgreSQL
sudo systemctl status postgresql

# Redis
redis-cli ping  # Doit retourner PONG

# Ollama
curl http://localhost:11434/api/tags
```

---

## 🚀 Utilisation

### 1. Uploader un Document
- Glissez un PDF dans la zone de drop
- Attendez que le status passe à "COMPLETED"
- Le document est automatiquement découpé et vectorisé

### 2. Poser une Question
- Tapez votre question dans le chat
- L'IA recherche les passages pertinents
- Réponse générée avec sources citées

### 3. Voir les Documents
- Scroll vers le bas pour voir tous vos documents
- Statuts en temps réel (PENDING → PROCESSING → COMPLETED)
- Suppression possible avec le bouton rouge

---

## 🎨 Personnalisation

### Changer les couleurs du frontend

Éditez `frontend/index.html`, section CSS `:root` :

```css
:root {
    --primary: #0A0E27;      /* Couleur principale */
    --accent: #00FF9D;       /* Couleur d'accent */
    --text-primary: #FFFFFF; /* Texte */
}
```

### Changer le modèle LLM

Éditez `backend/.env` :

```bash
# Au lieu de Claude 3.5 Sonnet
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3.5-sonnet

# Vous pouvez utiliser :
OPENROUTER_DEFAULT_MODEL=deepseek/deepseek-chat  # Plus économique
OPENROUTER_DEFAULT_MODEL=meta-llama/llama-3.1-70b-instruct
OPENROUTER_DEFAULT_MODEL=google/gemini-pro-1.5
```

---

## 📦 Déploiement en Production

### Backend (Django + Celery)
- Utilisez **Gunicorn** au lieu de `runserver`
- Configurez **Nginx** comme reverse proxy
- Activez **HTTPS** avec Let's Encrypt
- Utilisez **Supervisor** pour gérer Celery
- Configurez **PostgreSQL** avec backup automatique

### Frontend
- Hébergez sur **Netlify** ou **Vercel**
- Ou servez via **Nginx** depuis le backend
- Activez la compression Gzip
- Configurez le caching des assets

### Sécurité
- Changez `DEBUG=False`
- Générez une nouvelle `SECRET_KEY`
- Configurez `ALLOWED_HOSTS`
- Activez HTTPS uniquement
- Utilisez des mots de passe forts pour PostgreSQL

---

## 🎓 Architecture Résumée

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │─────→│    Django    │─────→│  PostgreSQL  │
│  (Vue.js 3)  │ HTTP │   (API REST) │      │  + pgvector  │
│ localhost:8080│      │localhost:8000│      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                ┌────────────┴────────────┐
                ↓                         ↓
         ┌─────────────┐          ┌─────────────┐
         │   Celery    │          │   Ollama    │
         │   Worker    │          │  (Local)    │
         │  (Async)    │          │ Embeddings  │
         └─────────────┘          └─────────────┘
                │                         
                ↓                         
         ┌─────────────┐          
         │ OpenRouter  │          
         │  (Cloud)    │          
         │ Text Gen    │          
         └─────────────┘          
```

---

## ✅ Checklist Finale

Avant de dire "ça marche" :

- [ ] PostgreSQL actif et DB créée
- [ ] pgvector installé et activé
- [ ] Redis actif (`redis-cli ping`)
- [ ] Ollama actif avec modèle `nomic-embed-text`
- [ ] Fichier `.env` configuré avec OpenRouter API key
- [ ] Migrations Django appliquées
- [ ] Superuser créé
- [ ] Token API généré
- [ ] Frontend configuré avec le bon token
- [ ] `./start.sh` lance tous les services
- [ ] http://localhost:8080 affiche l'interface
- [ ] Upload d'un PDF fonctionne
- [ ] Chat RAG retourne des réponses

---

## 🆘 Support

Si vous êtes bloqué :

1. Vérifiez les logs : `tail -f backend/logs/django.log`
2. Testez Ollama : `python backend/scripts/test_ollama.py`
3. Vérifiez que tous les services tournent : `ps aux | grep -E "django|celery|ollama"`
4. Consultez le README_BACKEND.md pour plus de détails

---

**Fait avec ❤️ pour la communauté open-source**

Bon développement ! 🚀
