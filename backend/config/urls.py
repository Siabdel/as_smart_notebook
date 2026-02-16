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
    # frentend
    path('', include('apps.frentend.urls')),
]

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
