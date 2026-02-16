"""
Vues pour l'app documents (upload, liste, détail, suppression)
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import SourceDocument
from .serializers import DocumentUploadSerializer, DocumentListSerializer, SourceDocumentSerializer
from django.shortcuts import render


class DocumentUploadView(APIView):
    """
    Vue pour l'upload de documents.
    POST /api/documents/upload/
    """
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    
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


from rest_framework.permissions import AllowAny

class DocumentListView(ListAPIView):
    """
    Vue pour lister les documents de l'utilisateur.
    GET /api/documents/
    """
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

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
