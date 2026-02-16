"""
Modèles Django pour la gestion des documents et des chunks vectorisés.
Utilise pgvector pour le stockage et la recherche vectorielle.
"""

from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField
from typing import List, Dict, Any
import hashlib


class SourceDocument(models.Model):
    """
    Document source uploadé par l'utilisateur (PDF, TXT, etc.)
    """
    
    # Métadonnées de base
    title = models.CharField(
        max_length=500,
        verbose_name="Titre du document"
    )
    
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name="Fichier source"
    )
    
    file_type = models.CharField(
        max_length=50,
        verbose_name="Type MIME",
        help_text="Ex: application/pdf, text/plain"
    )
    
    file_size = models.BigIntegerField(
        verbose_name="Taille du fichier (bytes)",
        default=0
    )
    
    file_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Hash SHA256 du fichier",
        help_text="Évite les doublons"
    )
    
    # Propriétaire
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Propriétaire"
    )
    
    # Statut du traitement
    class ProcessingStatus(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        PROCESSING = 'PROCESSING', 'En cours de traitement'
        COMPLETED = 'COMPLETED', 'Terminé'
        FAILED = 'FAILED', 'Échec'
    
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        verbose_name="Statut du traitement"
    )
    
    processing_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Message d'erreur"
    )
    
    # Statistiques
    total_pages = models.IntegerField(
        default=0,
        verbose_name="Nombre de pages"
    )
    
    total_chunks = models.IntegerField(
        default=0,
        verbose_name="Nombre de chunks générés"
    )
    
    total_characters = models.IntegerField(
        default=0,
        verbose_name="Nombre total de caractères"
    )
    
    # Métadonnées extraites
    extracted_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées extraites du PDF",
        help_text="Auteur, date de création, etc."
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'upload"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin de traitement"
    )
    
    class Meta:
        db_table = 'source_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['file_hash']),
        ]
        verbose_name = "Document source"
        verbose_name_plural = "Documents sources"
    
    def __str__(self) -> str:
        return f"{self.title} ({self.user.username})"
    
    def calculate_file_hash(self) -> str:
        """
        Calcule le hash SHA256 du fichier pour détecter les doublons.
        """
        sha256_hash = hashlib.sha256()
        
        # Lecture par chunks pour ne pas saturer la RAM
        self.file.open('rb')
        for byte_block in iter(lambda: self.file.read(4096), b""):
            sha256_hash.update(byte_block)
        self.file.close()
        
        return sha256_hash.hexdigest()
    
    def mark_as_processing(self) -> None:
        """Marque le document comme étant en cours de traitement."""
        self.processing_status = self.ProcessingStatus.PROCESSING
        self.processing_error = None
        self.save(update_fields=['processing_status', 'processing_error', 'updated_at'])
    
    def mark_as_completed(self, total_chunks: int) -> None:
        """Marque le document comme traité avec succès."""
        from django.utils import timezone
        self.processing_status = self.ProcessingStatus.COMPLETED
        self.total_chunks = total_chunks
        self.processed_at = timezone.now()
        self.save(update_fields=[
            'processing_status', 
            'total_chunks', 
            'processed_at', 
            'updated_at'
        ])
    
    def mark_as_failed(self, error_message: str) -> None:
        """Marque le document comme ayant échoué."""
        self.processing_status = self.ProcessingStatus.FAILED
        self.processing_error = error_message
        self.save(update_fields=['processing_status', 'processing_error', 'updated_at'])


class DocumentChunk(models.Model):
    """
    Fragment de texte d'un document avec son embedding vectoriel.
    Utilisé pour la recherche sémantique et le RAG.
    """
    
    # Relation avec le document source
    source_document = models.ForeignKey(
        SourceDocument,
        on_delete=models.CASCADE,
        related_name='chunks',
        verbose_name="Document source"
    )
    
    # Contenu textuel
    content = models.TextField(
        verbose_name="Contenu du chunk"
    )
    
    content_length = models.IntegerField(
        verbose_name="Longueur du contenu (caractères)"
    )
    
    # Embedding vectoriel (dimension 768 pour nomic-embed-text)
    # NOTE: Ajustez la dimension selon votre modèle
    # - nomic-embed-text: 768
    # - text-embedding-ada-002: 1536
    embedding = VectorField(
        dimensions=768,
        verbose_name="Vecteur d'embedding"
    )
    
    # Position dans le document
    chunk_index = models.IntegerField(
        verbose_name="Index du chunk",
        help_text="Position dans la séquence (0, 1, 2...)"
    )
    
    page_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Numéro de page source"
    )
    
    # Métadonnées contextuelles
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées du chunk",
        help_text="Section, paragraphe, etc."
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['source_document', 'chunk_index']
        indexes = [
            models.Index(fields=['source_document', 'chunk_index']),
            models.Index(fields=['page_number']),
        ]
        # Index vectoriel pour les recherches de similarité (géré par pgvector)
        # Créé automatiquement par la migration Django + pgvector
        verbose_name = "Chunk de document"
        verbose_name_plural = "Chunks de documents"
    
    def __str__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Chunk {self.chunk_index} - {self.source_document.title}: {preview}"
    
    @classmethod
    def search_similar(
        cls,
        query_embedding: List[float],
        user: User,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        source_document_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche les chunks les plus similaires à un embedding de requête.
        
        Args:
            query_embedding: Vecteur de la question utilisateur
            user: Utilisateur pour filtrer les documents
            top_k: Nombre de résultats à retourner
            similarity_threshold: Seuil de similarité minimale (0-1)
            source_document_ids: Liste optionnelle d'IDs de documents à filtrer
        
        Returns:
            Liste de dictionnaires avec chunk, distance et score
        """
        from django.db.models import F
        from pgvector.django import L2Distance
        
        # Construction de la requête de base
        queryset = cls.objects.filter(
            source_document__user=user,
            source_document__processing_status=SourceDocument.ProcessingStatus.COMPLETED
        )
        
        # Filtrage optionnel par documents spécifiques
        if source_document_ids:
            queryset = queryset.filter(source_document_id__in=source_document_ids)
        
        # Recherche vectorielle avec distance L2
        # Plus la distance est petite, plus c'est similaire
        results = queryset.annotate(
            distance=L2Distance('embedding', query_embedding)
        ).order_by('distance')[:top_k]
        
        # Conversion de la distance L2 en score de similarité (0-1)
        # Score = 1 / (1 + distance)
        output = []
        for chunk in results:
            similarity_score = 1.0 / (1.0 + chunk.distance)
            
            # Filtrage par seuil
            if similarity_score >= similarity_threshold:
                output.append({
                    'chunk': chunk,
                    'distance': float(chunk.distance),
                    'similarity_score': similarity_score,
                    'source_document': chunk.source_document,
                    'page_number': chunk.page_number,
                    'content': chunk.content
                })
        
        return output
    
    def save(self, *args, **kwargs):
        """Override pour calculer automatiquement la longueur du contenu."""
        self.content_length = len(self.content)
        super().save(*args, **kwargs)


class QueryLog(models.Model):
    """
    Log des questions posées par les utilisateurs pour analytics et amélioration.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='queries',
        verbose_name="Utilisateur"
    )
    
    query_text = models.TextField(
        verbose_name="Question posée"
    )
    
    # Documents contextuels utilisés
    source_documents = models.ManyToManyField(
        SourceDocument,
        related_name='queries',
        blank=True,
        verbose_name="Documents consultés"
    )
    
    # Résultats de la recherche vectorielle
    retrieved_chunks_count = models.IntegerField(
        default=0,
        verbose_name="Nombre de chunks récupérés"
    )
    
    # Réponse générée
    response_text = models.TextField(
        blank=True,
        verbose_name="Réponse générée"
    )
    
    # Métriques
    response_time_ms = models.IntegerField(
        default=0,
        verbose_name="Temps de réponse (ms)"
    )
    
    tokens_used = models.IntegerField(
        default=0,
        verbose_name="Tokens consommés (LLM)"
    )
    
    # Feedback utilisateur
    user_rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 6)],
        verbose_name="Note utilisateur (1-5)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de la requête"
    )
    
    class Meta:
        db_table = 'query_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = "Log de requête"
        verbose_name_plural = "Logs de requêtes"
    
    def __str__(self) -> str:
        preview = self.query_text[:50] + "..." if len(self.query_text) > 50 else self.query_text
        return f"{self.user.username}: {preview}"
