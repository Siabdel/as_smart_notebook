#!/bin/bash

###############################################################################
# Smart-Notebook - Script de Création de la Structure Complète
# Crée tous les dossiers et fichiers nécessaires pour Django
###############################################################################

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     SMART-NOTEBOOK - CRÉATION DE LA STRUCTURE             ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Vérifier qu'on est dans le bon dossier
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}⚠️  Ce script doit être exécuté depuis le dossier backend/${NC}"
    echo -e "${YELLOW}   Usage: cd backend && bash setup_structure.sh${NC}"
    exit 1
fi

echo -e "${GREEN}Création de la structure Django...${NC}"
echo ""

###############################################################################
# Création des dossiers principaux
###############################################################################

echo -e "${BLUE}[1/7]${NC} Création des dossiers principaux..."

mkdir -p config
mkdir -p apps/core
mkdir -p apps/documents/migrations
mkdir -p apps/documents/services
mkdir -p apps/rag/services
mkdir -p apps/podcasts/migrations
mkdir -p apps/podcasts/services
mkdir -p scripts
mkdir -p media/documents
mkdir -p media/podcasts
mkdir -p logs
mkdir -p staticfiles

echo -e "${GREEN}  ✓ Dossiers créés${NC}"

###############################################################################
# Création des fichiers __init__.py
###############################################################################

echo -e "${BLUE}[2/7]${NC} Création des fichiers __init__.py..."

touch config/__init__.py
touch apps/__init__.py
touch apps/core/__init__.py
touch apps/documents/__init__.py
touch apps/documents/migrations/__init__.py
touch apps/documents/services/__init__.py
touch apps/rag/__init__.py
touch apps/rag/services/__init__.py
touch apps/podcasts/__init__.py
touch apps/podcasts/migrations/__init__.py
touch apps/podcasts/services/__init__.py

echo -e "${GREEN}  ✓ Fichiers __init__.py créés${NC}"

###############################################################################
# Création de manage.py
###############################################################################

echo -e "${BLUE}[3/7]${NC} Création de manage.py..."

cat > manage.py << 'EOF'
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
EOF

chmod +x manage.py

echo -e "${GREEN}  ✓ manage.py créé${NC}"

###############################################################################
# Création de config/wsgi.py et config/asgi.py
###############################################################################

echo -e "${BLUE}[4/7]${NC} Création des fichiers WSGI/ASGI..."

cat > config/wsgi.py << 'EOF'
"""
WSGI config for Smart-Notebook project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
EOF

cat > config/asgi.py << 'EOF'
"""
ASGI config for Smart-Notebook project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
EOF

echo -e "${GREEN}  ✓ WSGI/ASGI créés${NC}"

###############################################################################
# Création des URLs
###############################################################################

echo -e "${BLUE}[5/7]${NC} Création des fichiers d'URL..."

# config/urls.py
cat > config/urls.py << 'EOF'
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

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOF

# apps/documents/urls.py
cat > apps/documents/urls.py << 'EOF'
"""
URLs pour l'app documents
"""
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
EOF

# apps/rag/urls.py
cat > apps/rag/urls.py << 'EOF'
"""
URLs pour l'app RAG
"""
from django.urls import path
from .views import AskDocumentView, DocumentStatsView, RateFeedbackView

app_name = 'rag'

urlpatterns = [
    path('ask/', AskDocumentView.as_view(), name='ask-document'),
    path('stats/', DocumentStatsView.as_view(), name='document-stats'),
    path('feedback/', RateFeedbackView.as_view(), name='rate-feedback'),
]
EOF

echo -e "${GREEN}  ✓ URLs créés${NC}"

###############################################################################
# Création des vues manquantes pour documents
###############################################################################

echo -e "${BLUE}[6/7]${NC} Création des vues Django..."

cat > apps/documents/views.py << 'EOF'
"""
Vues pour l'app documents (upload, liste, détail, suppression)
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import SourceDocument
from .serializers import DocumentUploadSerializer, DocumentListSerializer, SourceDocumentSerializer


class DocumentUploadView(APIView):
    """
    Vue pour l'upload de documents.
    POST /api/documents/upload/
    """
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
    """
    Vue pour lister les documents de l'utilisateur.
    GET /api/documents/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentListSerializer
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user).order_by('-created_at')


class DocumentDetailView(RetrieveAPIView):
    """
    Vue pour voir les détails d'un document.
    GET /api/documents/<id>/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SourceDocumentSerializer
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user)


class DocumentDeleteView(DestroyAPIView):
    """
    Vue pour supprimer un document.
    DELETE /api/documents/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SourceDocument.objects.filter(user=self.request.user)
EOF

echo -e "${GREEN}  ✓ Vues créées${NC}"

###############################################################################
# Création des apps.py
###############################################################################

echo -e "${BLUE}[7/7]${NC} Création des fichiers apps.py..."

cat > apps/core/apps.py << 'EOF'
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
EOF

cat > apps/documents/apps.py << 'EOF'
from django.apps import AppConfig

class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
EOF

cat > apps/rag/apps.py << 'EOF'
from django.apps import AppConfig

class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rag'
EOF

cat > apps/podcasts/apps.py << 'EOF'
from django.apps import AppConfig

class PodcastsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.podcasts'
EOF

echo -e "${GREEN}  ✓ apps.py créés${NC}"

###############################################################################
# Création du fichier .gitignore
###############################################################################

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Django
*.log
db.sqlite3
db.sqlite3-journal
/media
/staticfiles
/logs

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Celery
celerybeat-schedule
celerybeat.pid

# OS
.DS_Store
Thumbs.db
EOF

###############################################################################
# Résumé
###############################################################################

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║        ✅ STRUCTURE DJANGO CRÉÉE AVEC SUCCÈS !            ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📂 Structure créée:${NC}"
echo -e "   ✓ config/ (settings, urls, wsgi, asgi)"
echo -e "   ✓ apps/core/"
echo -e "   ✓ apps/documents/ (models, views, urls, migrations)"
echo -e "   ✓ apps/rag/ (views, urls)"
echo -e "   ✓ apps/podcasts/"
echo -e "   ✓ scripts/"
echo -e "   ✓ media/"
echo -e "   ✓ logs/"
echo -e "   ✓ manage.py"
echo ""
echo -e "${YELLOW}📋 Prochaines étapes:${NC}"
echo ""
echo -e "   1. Placez les fichiers générés dans les bons dossiers:"
echo -e "      ${GREEN}• django_settings.py${NC} → config/settings.py"
echo -e "      ${GREEN}• celery_config.py${NC} → config/celery.py"
echo -e "      ${GREEN}• documents_models.py${NC} → apps/documents/models.py"
echo -e "      ${GREEN}• serializers.py${NC} → apps/documents/serializers.py"
echo -e "      ${GREEN}• tasks.py${NC} → apps/documents/tasks.py"
echo -e "      ${GREEN}• views.py (RAG)${NC} → apps/rag/views.py"
echo -e "      ${GREEN}• ai_router.py${NC} → apps/core/ai_router.py"
echo -e "      ${GREEN}• init_db.sh${NC} → scripts/"
echo -e "      ${GREEN}• test_ollama.py${NC} → scripts/"
echo ""
echo -e "   2. Créez l'environnement virtuel:"
echo -e "      ${BLUE}python3 -m venv venv${NC}"
echo -e "      ${BLUE}source venv/bin/activate${NC}"
echo ""
echo -e "   3. Installez les dépendances:"
echo -e "      ${BLUE}pip install -r requirements.txt${NC}"
echo ""
echo -e "   4. Initialisez la base de données:"
echo -e "      ${BLUE}chmod +x scripts/init_db.sh${NC}"
echo -e "      ${BLUE}./scripts/init_db.sh${NC}"
echo ""
echo -e "   5. Configurez .env:"
echo -e "      ${BLUE}cp env_example.txt .env${NC}"
echo -e "      ${BLUE}nano .env${NC}"
echo ""
echo -e "   6. Appliquez les migrations:"
echo -e "      ${BLUE}python manage.py makemigrations${NC}"
echo -e "      ${BLUE}python manage.py migrate${NC}"
echo ""
echo -e "   7. Créez un superuser:"
echo -e "      ${BLUE}python manage.py createsuperuser${NC}"
echo ""
echo -e "${GREEN}✨ Vous êtes prêt à démarrer !${NC}"
echo ""
