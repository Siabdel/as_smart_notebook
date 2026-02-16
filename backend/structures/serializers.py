"""
Serializers Django REST Framework pour la gestion des documents.
Gère l'upload, la validation et la sérialisation des documents sources.
"""

from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile
from typing import Dict, Any
import magic
import os

# Import des modèles (ajustez selon votre structure)
# from apps.documents.models import SourceDocument, DocumentChunk, QueryLog


# ========================================
# CONFIGURATION
# ========================================

ALLOWED_MIME_TYPES = [
    'application/pdf',
    'text/plain',
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


# ========================================
# SERIALIZERS POUR DOCUMENTS
# ========================================

class DocumentChunkSerializer(serializers.ModelSerializer):
    """
    Serializer pour les chunks de documents (lecture seule).
    """
    source_document_title = serializers.CharField(
        source='source_document.title',
        read_only=True
    )
    
    class Meta:
        model = None  # Remplacer par DocumentChunk
        fields = [
            'id',
            'source_document',
            'source_document_title',
            'content',
            'content_length',
            'chunk_index',
            'page_number',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields


class SourceDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer pour les documents sources (lecture et création).
    """
    # Champs calculés
    file_url = serializers.SerializerMethodField()
    processing_progress = serializers.SerializerMethodField()
    chunks_count = serializers.IntegerField(
        source='chunks.count',
        read_only=True
    )
    
    # Métadonnées de l'utilisateur (lecture seule)
    user_email = serializers.EmailField(
        source='user.email',
        read_only=True
    )
    
    class Meta:
        model = None  # Remplacer par SourceDocument
        fields = [
            'id',
            'title',
            'file',
            'file_url',
            'file_type',
            'file_size',
            'file_hash',
            'user',
            'user_email',
            'processing_status',
            'processing_error',
            'processing_progress',
            'total_pages',
            'total_chunks',
            'chunks_count',
            'total_characters',
            'extracted_metadata',
            'created_at',
            'updated_at',
            'processed_at',
        ]
        read_only_fields = [
            'id',
            'file_hash',
            'user',
            'user_email',
            'processing_status',
            'processing_error',
            'processing_progress',
            'total_pages',
            'total_chunks',
            'chunks_count',
            'total_characters',
            'extracted_metadata',
            'created_at',
            'updated_at',
            'processed_at',
        ]
    
    def get_file_url(self, obj) -> str:
        """Retourne l'URL complète du fichier."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_processing_progress(self, obj) -> Dict[str, Any]:
        """Calcule la progression du traitement."""
        if obj.processing_status == obj.ProcessingStatus.COMPLETED:
            return {
                'percentage': 100,
                'status': 'completed',
                'message': f'{obj.total_chunks} chunks créés'
            }
        elif obj.processing_status == obj.ProcessingStatus.PROCESSING:
            return {
                'percentage': 50,
                'status': 'processing',
                'message': 'Extraction et vectorisation en cours...'
            }
        elif obj.processing_status == obj.ProcessingStatus.FAILED:
            return {
                'percentage': 0,
                'status': 'failed',
                'message': obj.processing_error or 'Erreur inconnue'
            }
        else:  # PENDING
            return {
                'percentage': 0,
                'status': 'pending',
                'message': 'En attente de traitement'
            }


class DocumentUploadSerializer(serializers.Serializer):
    """
    Serializer pour l'upload de documents avec validation stricte.
    """
    file = serializers.FileField(
        required=True,
        help_text="Fichier à uploader (PDF ou TXT)"
    )
    
    title = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Titre personnalisé (optionnel, déduit du nom de fichier si absent)"
    )
    
    def validate_file(self, file: UploadedFile) -> UploadedFile:
        """
        Valide le fichier uploadé :
        - Type MIME autorisé
        - Taille maximale
        - Détection de doublons via hash
        """
        # 1. Vérification de la taille
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"Le fichier est trop volumineux. Taille max : {MAX_FILE_SIZE / (1024*1024):.0f} MB"
            )
        
        # 2. Vérification du type MIME réel (pas juste l'extension)
        try:
            # Lecture des premiers octets pour déterminer le type MIME
            file.seek(0)
            mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)  # Reset pour lecture ultérieure
            
            if mime not in ALLOWED_MIME_TYPES:
                raise serializers.ValidationError(
                    f"Type de fichier non supporté : {mime}. "
                    f"Types autorisés : {', '.join(ALLOWED_MIME_TYPES)}"
                )
        
        except Exception as e:
            raise serializers.ValidationError(
                f"Impossible de déterminer le type de fichier : {str(e)}"
            )
        
        return file
    
    def validate_title(self, title: str) -> str:
        """Valide et nettoie le titre."""
        if title:
            title = title.strip()
            if not title:
                raise serializers.ValidationError("Le titre ne peut pas être vide")
        return title
    
    def create(self, validated_data: Dict[str, Any]):
        """
        Crée un nouveau SourceDocument et lance le traitement asynchrone.
        """
        from apps.documents.models import SourceDocument
        from apps.documents.tasks import process_document_ingestion
        
        file = validated_data['file']
        title = validated_data.get('title')
        user = self.context['request'].user
        
        # Génération du titre si non fourni
        if not title:
            title = os.path.splitext(file.name)[0]
        
        # Détection du type MIME
        file.seek(0)
        mime_type = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        
        # Création du document
        document = SourceDocument.objects.create(
            title=title,
            file=file,
            file_type=mime_type,
            file_size=file.size,
            user=user,
            processing_status=SourceDocument.ProcessingStatus.PENDING
        )
        
        # Calcul et sauvegarde du hash (pour détecter les doublons)
        document.file_hash = document.calculate_file_hash()
        document.save(update_fields=['file_hash'])
        
        # Lancement du traitement asynchrone via Celery
        process_document_ingestion.delay(document.id)
        
        return document


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Serializer léger pour la liste des documents (sans les chunks).
    """
    processing_status_display = serializers.CharField(
        source='get_processing_status_display',
        read_only=True
    )
    
    class Meta:
        model = None  # Remplacer par SourceDocument
        fields = [
            'id',
            'title',
            'file_type',
            'file_size',
            'processing_status',
            'processing_status_display',
            'total_pages',
            'total_chunks',
            'created_at',
            'processed_at',
        ]
        read_only_fields = fields


# ========================================
# SERIALIZERS POUR RAG
# ========================================

class AskQuestionSerializer(serializers.Serializer):
    """
    Serializer pour les requêtes RAG.
    """
    question = serializers.CharField(
        required=True,
        max_length=1000,
        help_text="Question à poser aux documents"
    )
    
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Liste d'IDs de documents à interroger (optionnel, tous par défaut)"
    )
    
    top_k = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text="Nombre de chunks à récupérer"
    )
    
    model = serializers.CharField(
        required=False,
        help_text="Modèle LLM à utiliser (optionnel, utilise le défaut)"
    )
    
    def validate_question(self, question: str) -> str:
        """Valide la question."""
        question = question.strip()
        if not question:
            raise serializers.ValidationError("La question ne peut pas être vide")
        
        if len(question) < 5:
            raise serializers.ValidationError(
                "La question doit contenir au moins 5 caractères"
            )
        
        return question
    
    def validate_document_ids(self, document_ids):
        """Valide que les documents existent et appartiennent à l'utilisateur."""
        if document_ids:
            from apps.documents.models import SourceDocument
            user = self.context['request'].user
            
            # Vérification des documents
            valid_docs = SourceDocument.objects.filter(
                id__in=document_ids,
                user=user,
                processing_status=SourceDocument.ProcessingStatus.COMPLETED
            ).count()
            
            if valid_docs != len(document_ids):
                raise serializers.ValidationError(
                    "Certains documents sont introuvables ou non traités"
                )
        
        return document_ids


class QueryLogSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'historique des questions.
    """
    source_documents_info = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Remplacer par QueryLog
        fields = [
            'id',
            'query_text',
            'response_text',
            'source_documents_info',
            'retrieved_chunks_count',
            'response_time_ms',
            'tokens_used',
            'user_rating',
            'created_at',
        ]
        read_only_fields = fields
    
    def get_source_documents_info(self, obj):
        """Retourne les infos des documents sources utilisés."""
        return [
            {
                'id': doc.id,
                'title': doc.title,
            }
            for doc in obj.source_documents.all()
        ]


class RateFeedbackSerializer(serializers.Serializer):
    """
    Serializer pour noter une réponse RAG.
    """
    query_id = serializers.IntegerField(
        required=True,
        help_text="ID de la requête à noter"
    )
    
    rating = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=5,
        help_text="Note de 1 (mauvais) à 5 (excellent)"
    )
    
    def validate_query_id(self, query_id):
        """Valide que la requête existe et appartient à l'utilisateur."""
        from apps.documents.models import QueryLog
        user = self.context['request'].user
        
        if not QueryLog.objects.filter(id=query_id, user=user).exists():
            raise serializers.ValidationError(
                "Cette requête est introuvable ou ne vous appartient pas"
            )
        
        return query_id


# ========================================
# SERIALIZERS POUR STATISTIQUES
# ========================================

class DocumentStatsSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques utilisateur (lecture seule).
    """
    total_documents = serializers.IntegerField()
    documents_processing = serializers.IntegerField()
    documents_completed = serializers.IntegerField()
    documents_failed = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    total_characters = serializers.IntegerField()
    recent_documents = serializers.ListField()


# ========================================
# SERIALIZER DE RÉPONSE RAG
# ========================================

class RAGSourceSerializer(serializers.Serializer):
    """Serializer pour une source dans la réponse RAG."""
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()
    page = serializers.IntegerField(allow_null=True)
    excerpt = serializers.CharField()
    relevance_score = serializers.FloatField()


class RAGMetadataSerializer(serializers.Serializer):
    """Serializer pour les métadonnées de la réponse RAG."""
    query_time_ms = serializers.IntegerField()
    chunks_retrieved = serializers.IntegerField()
    tokens_used = serializers.IntegerField()
    model_used = serializers.CharField()
    query_id = serializers.IntegerField()


class RAGResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse complète RAG."""
    answer = serializers.CharField()
    sources = RAGSourceSerializer(many=True)
    metadata = RAGMetadataSerializer()
