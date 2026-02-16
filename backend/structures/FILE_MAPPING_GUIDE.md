# 📂 Smart-Notebook - Guide de Placement des Fichiers

## 🎯 Problème
Les fichiers générés doivent être placés dans la structure Django correcte.

## ✅ Solution : 2 Options

---

## **OPTION 1 : Script Automatique (RECOMMANDÉ)**

### 1️⃣ Téléchargez le script

Téléchargez `setup_structure.sh` (disponible dans les fichiers générés)

### 2️⃣ Créez le dossier backend et exécutez

```bash
mkdir -p smart-notebook/backend
cd smart-notebook/backend

# Placez tous les fichiers téléchargés ici temporairement
# Puis exécutez :
bash setup_structure.sh
```

### 3️⃣ Le script crée automatiquement

✅ Toute la structure Django  
✅ Tous les dossiers apps/  
✅ Tous les fichiers __init__.py  
✅ manage.py, urls.py, wsgi.py, asgi.py  
✅ .gitignore  

### 4️⃣ Placez ensuite les fichiers générés

Suivez le guide ci-dessous.

---

## **OPTION 2 : Placement Manuel**

### Structure Complète à Créer

```
smart-notebook/
│
├── backend/
│   │
│   ├── manage.py                    ← Créer (voir ci-dessous)
│   ├── requirements.txt             ← Fichier généré
│   ├── .env                         ← Créer depuis env_example.txt
│   ├── .gitignore                   ← Créer
│   │
│   ├── config/
│   │   ├── __init__.py              ← Créer (vide)
│   │   ├── settings.py              ← django_settings.py
│   │   ├── celery.py                ← celery_config.py
│   │   ├── urls.py                  ← Créer (voir ci-dessous)
│   │   ├── wsgi.py                  ← Créer (voir ci-dessous)
│   │   └── asgi.py                  ← Créer (voir ci-dessous)
│   │
│   ├── apps/
│   │   ├── __init__.py              ← Créer (vide)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py          ← Créer (vide)
│   │   │   ├── apps.py              ← Créer (voir ci-dessous)
│   │   │   ├── ai_router.py         ← Fichier généré
│   │   │   ├── exceptions.py        ← Créer (vide pour l'instant)
│   │   │   └── validators.py        ← Créer (vide pour l'instant)
│   │   │
│   │   ├── documents/
│   │   │   ├── __init__.py          ← Créer (vide)
│   │   │   ├── apps.py              ← Créer (voir ci-dessous)
│   │   │   ├── models.py            ← documents_models.py
│   │   │   ├── serializers.py       ← serializers.py (partie documents)
│   │   │   ├── views.py             ← Créer (voir ci-dessous)
│   │   │   ├── urls.py              ← Créer (voir ci-dessous)
│   │   │   ├── tasks.py             ← Fichier généré
│   │   │   ├── admin.py             ← Créer (optionnel)
│   │   │   ├── migrations/
│   │   │   │   └── __init__.py      ← Créer (vide)
│   │   │   └── services/
│   │   │       ├── __init__.py      ← Créer (vide)
│   │   │       ├── text_extractor.py ← Créer (vide pour l'instant)
│   │   │       └── chunking.py      ← Créer (vide pour l'instant)
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py          ← Créer (vide)
│   │   │   ├── apps.py              ← Créer (voir ci-dessous)
│   │   │   ├── views.py             ← views.py (RAG)
│   │   │   ├── serializers.py       ← serializers.py (partie RAG)
│   │   │   ├── urls.py              ← Créer (voir ci-dessous)
│   │   │   └── services/
│   │   │       ├── __init__.py      ← Créer (vide)
│   │   │       ├── retriever.py     ← Créer (vide pour l'instant)
│   │   │       └── context_builder.py ← Créer (vide pour l'instant)
│   │   │
│   │   └── podcasts/
│   │       ├── __init__.py          ← Créer (vide)
│   │       ├── apps.py              ← Créer (voir ci-dessous)
│   │       ├── models.py            ← Créer (vide pour l'instant)
│   │       ├── views.py             ← Créer (vide pour l'instant)
│   │       ├── urls.py              ← Créer (vide pour l'instant)
│   │       ├── migrations/
│   │       │   └── __init__.py      ← Créer (vide)
│   │       └── services/
│   │           ├── __init__.py      ← Créer (vide)
│   │           ├── script_generator.py ← Créer (vide pour l'instant)
│   │           └── tts_engine.py    ← Créer (vide pour l'instant)
│   │
│   ├── scripts/
│   │   ├── init_db.sh               ← Fichier généré
│   │   └── test_ollama.py           ← Fichier généré
│   │
│   ├── media/
│   │   ├── documents/               ← Créer (dossier vide)
│   │   └── podcasts/                ← Créer (dossier vide)
│   │
│   ├── logs/                        ← Créer (dossier vide)
│   └── staticfiles/                 ← Créer (dossier vide)
│
├── frontend/
│   └── index.html                   ← Fichier généré
│
├── start.sh                         ← Fichier généré
└── stop.sh                          ← Fichier généré
```

---

## 📋 **Mapping Détaillé des Fichiers Générés**

| Fichier Généré | Destination | Action |
|----------------|-------------|--------|
| `django_settings.py` | `backend/config/settings.py` | Renommer |
| `celery_config.py` | `backend/config/celery.py` | Renommer |
| `documents_models.py` | `backend/apps/documents/models.py` | Renommer |
| `ai_router.py` | `backend/apps/core/ai_router.py` | Copier |
| `tasks.py` | `backend/apps/documents/tasks.py` | Copier |
| `views.py` (RAG) | `backend/apps/rag/views.py` | Copier |
| `serializers.py` | `backend/apps/documents/serializers.py` | Copier (tout) |
| `requirements.txt` | `backend/requirements.txt` | Copier |
| `env_example.txt` | `backend/.env` | Renommer et éditer |
| `init_db.sh` | `backend/scripts/init_db.sh` | Copier |
| `test_ollama.py` | `backend/scripts/test_ollama.py` | Copier |
| `index.html` | `frontend/index.html` | Copier |
| `start.sh` | `start.sh` (racine) | Copier |
| `stop.sh` | `stop.sh` (racine) | Copier |

---

## 🔧 **Fichiers à Créer Manuellement**

### 1. `backend/manage.py`

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

### 2. `backend/config/__init__.py`

**Fichier vide** (juste `touch config/__init__.py`)

### 3. `backend/config/urls.py`

```python
"""
URL Configuration for Smart-Notebook
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/documents/', include('apps.documents.urls')),
    path('api/rag/', include('apps.rag.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### 4. `backend/config/wsgi.py`

```python
"""
WSGI config for Smart-Notebook project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
```

### 5. `backend/config/asgi.py`

```python
"""
ASGI config for Smart-Notebook project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
```

### 6. `backend/apps/documents/urls.py`

```python
"""URLs pour l'app documents"""
from django.urls import path
from .views import (
    DocumentUploadView, 
    DocumentListView, 
    DocumentDetailView,
    DocumentDeleteView
)

app_name = 'documents'

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='upload'),
    path('', DocumentListView.as_view(), name='list'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', DocumentDeleteView.as_view(), name='delete'),
]
```

### 7. `backend/apps/documents/views.py`

```python
"""Vues pour l'app documents"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import SourceDocument
from .serializers import DocumentUploadSerializer, DocumentListSerializer, SourceDocumentSerializer


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            document = serializer.save()
            return Response({
                'id': document.id,
                'title': document.title,
                'status': document.processing_status,
                'message': 'Document uploadé avec succès. Traitement en cours...'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentListSerializer
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user).order_by('-created_at')


class DocumentDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SourceDocumentSerializer
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user)


class DocumentDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user)
```

### 8. `backend/apps/rag/urls.py`

```python
"""URLs pour l'app RAG"""
from django.urls import path
from .views import AskDocumentView, DocumentStatsView, RateFeedbackView

app_name = 'rag'

urlpatterns = [
    path('ask/', AskDocumentView.as_view(), name='ask-document'),
    path('stats/', DocumentStatsView.as_view(), name='document-stats'),
    path('feedback/', RateFeedbackView.as_view(), name='rate-feedback'),
]
```

### 9. Fichiers `apps.py` pour chaque app

**`backend/apps/core/apps.py`**
```python
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
```

**`backend/apps/documents/apps.py`**
```python
from django.apps import AppConfig

class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
```

**`backend/apps/rag/apps.py`**
```python
from django.apps import AppConfig

class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rag'
```

**`backend/apps/podcasts/apps.py`**
```python
from django.apps import AppConfig

class PodcastsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.podcasts'
```

### 10. Tous les fichiers `__init__.py`

**Créez des fichiers vides** dans :
- `backend/config/__init__.py`
- `backend/apps/__init__.py`
- `backend/apps/core/__init__.py`
- `backend/apps/documents/__init__.py`
- `backend/apps/documents/migrations/__init__.py`
- `backend/apps/documents/services/__init__.py`
- `backend/apps/rag/__init__.py`
- `backend/apps/rag/services/__init__.py`
- `backend/apps/podcasts/__init__.py`
- `backend/apps/podcasts/migrations/__init__.py`
- `backend/apps/podcasts/services/__init__.py`

---

## ⚡ **Commandes Rapides**

### Pour créer tous les dossiers :

```bash
cd backend

mkdir -p config
mkdir -p apps/{core,documents/{migrations,services},rag/services,podcasts/{migrations,services}}
mkdir -p scripts media/{documents,podcasts} logs staticfiles
```

### Pour créer tous les __init__.py :

```bash
touch config/__init__.py
touch apps/{__init__.py,core/__init__.py,documents/{__init__.py,migrations/__init__.py,services/__init__.py},rag/{__init__.py,services/__init__.py},podcasts/{__init__.py,migrations/__init__.py,services/__init__.py}}
```

---

## ✅ **Vérification Finale**

Une fois tous les fichiers placés :

```bash
cd backend

# Activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Vérifier que Django trouve les apps
python manage.py check

# Si pas d'erreur, vous êtes prêt !
```

---

## 🎯 **Résumé**

**Option 1 (Recommandée)** : Utilisez `setup_structure.sh` → Tout est créé automatiquement  
**Option 2** : Suivez ce guide et créez manuellement chaque fichier/dossier

Dans les deux cas, vous aurez une structure Django complète et prête à l'emploi ! 🚀
