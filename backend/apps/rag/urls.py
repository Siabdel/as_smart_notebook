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
