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
