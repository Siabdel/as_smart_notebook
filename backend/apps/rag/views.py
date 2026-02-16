"""
Vues API pour le système RAG (Retrieval-Augmented Generation).
Gère les requêtes utilisateur et génère des réponses contextuelles.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from typing import List, Dict, Any, Optional
import time
import logging

# Import des modèles (ajustez selon votre structure)
# from apps.documents.models import SourceDocument, DocumentChunk, QueryLog
# from apps.core.ai_router import get_ai_router, ChatMessage

logger = logging.getLogger(__name__)


# ========================================
# CONFIGURATION RAG
# ========================================

TOP_K_RESULTS = 5  # Nombre de chunks à récupérer
SIMILARITY_THRESHOLD = 0.6  # Seuil de pertinence (0-1)
MAX_CONTEXT_LENGTH = 3000  # Caractères max dans le contexte


# ========================================
# CONSTRUCTION DU CONTEXTE RAG
# ========================================

def build_rag_context(
    retrieved_chunks: List[Dict[str, Any]],
    max_length: int = MAX_CONTEXT_LENGTH
) -> str:
    """
    Construit le contexte RAG à partir des chunks récupérés.
    
    Args:
        retrieved_chunks: Liste de chunks avec scores de similarité
        max_length: Longueur maximale du contexte en caractères
    
    Returns:
        Contexte formaté pour le LLM
    """
    if not retrieved_chunks:
        return "Aucun contexte pertinent trouvé dans les documents."
    
    context_parts = []
    current_length = 0
    
    for idx, chunk_data in enumerate(retrieved_chunks, start=1):
        chunk = chunk_data['chunk']
        score = chunk_data['similarity_score']
        source = chunk_data['source_document']
        page = chunk_data.get('page_number', 'N/A')
        
        # Format: [Source X, Page Y, Score: Z.ZZ] Contenu...
        header = f"[Source: {source.title}, Page: {page}, Pertinence: {score:.2f}]\n"
        content = chunk.content.strip()
        
        chunk_text = f"{header}{content}\n\n"
        
        # Vérification de la longueur
        if current_length + len(chunk_text) > max_length:
            break
        
        context_parts.append(chunk_text)
        current_length += len(chunk_text)
    
    context = "=== CONTEXTE EXTRAIT DES DOCUMENTS ===\n\n" + "".join(context_parts)
    
    logger.debug(f"📄 Contexte RAG construit: {len(context_parts)} chunks, {current_length} caractères")
    
    return context


def create_rag_prompt(question: str, context: str) -> List[Dict[str, str]]:
    """
    Crée le prompt RAG complet pour le LLM.
    
    Args:
        question: Question de l'utilisateur
        context: Contexte extrait des documents
    
    Returns:
        Liste de messages pour l'API de chat
    """
    system_prompt = """Tu es un assistant intelligent spécialisé dans l'analyse de documents.
Ta mission est de répondre aux questions en te basant UNIQUEMENT sur le contexte fourni.

RÈGLES IMPORTANTES:
1. Base tes réponses EXCLUSIVEMENT sur le contexte fourni
2. Si l'information n'est pas dans le contexte, dis-le clairement
3. Cite toujours tes sources (titre du document, numéro de page)
4. Sois précis et factuel
5. Si tu n'es pas sûr, exprime ton incertitude
6. Réponds en français de manière claire et structurée

Format de réponse attendu:
- Réponse directe et concise
- Citations entre guillemets si pertinent
- Références aux sources utilisées
"""
    
    user_prompt = f"""{context}

=== QUESTION DE L'UTILISATEUR ===
{question}

Réponds à cette question en te basant uniquement sur le contexte ci-dessus."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    return messages


# ========================================
# VUE API PRINCIPALE
# ========================================

class AskDocumentView(APIView):
    """
    Endpoint principal pour poser des questions sur les documents.
    
    POST /api/rag/ask/
    Body: {
        "question": "Quelle est la conclusion du rapport?",
        "document_ids": [1, 2, 3],  # Optionnel: filtrer par documents
        "top_k": 5,  # Optionnel: nombre de chunks à récupérer
        "model": "anthropic/claude-3.5-sonnet"  # Optionnel: modèle LLM
    }
    
    Response: {
        "answer": "La conclusion indique que...",
        "sources": [
            {
                "document_title": "Rapport 2024",
                "page": 12,
                "excerpt": "...",
                "relevance_score": 0.89
            }
        ],
        "metadata": {
            "query_time_ms": 1523,
            "chunks_retrieved": 5,
            "tokens_used": 450,
            "model_used": "claude-3.5-sonnet"
        }
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Traite une question utilisateur via RAG."""
        
        start_time = time.time()
        
        # 1. Validation des données d'entrée
        question = request.data.get('question', '').strip()
        document_ids = request.data.get('document_ids', None)
        top_k = request.data.get('top_k', TOP_K_RESULTS)
        model = request.data.get('model', None)
        
        if not question:
            return Response(
                {"error": "Le champ 'question' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(question) > 1000:
            return Response(
                {"error": "La question est trop longue (max 1000 caractères)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"🔍 Nouvelle requête RAG: '{question[:100]}...' (user: {request.user.username})")
        
        try:
            # Import ici pour éviter les imports circulaires
            from apps.documents.models import DocumentChunk, QueryLog
            from apps.core.ai_router import get_ai_router
            
            ai_router = get_ai_router()
            
            # 2. Génération de l'embedding de la question (local Ollama)
            logger.debug("📊 Génération de l'embedding de la question...")
            embedding_result = ai_router.get_embedding(
                text=question,
                normalize=True
            )
            
            # 3. Recherche vectorielle de similarité (SQL avec pgvector)
            logger.debug(f"🔎 Recherche des {top_k} chunks les plus pertinents...")
            retrieved_chunks = DocumentChunk.search_similar(
                query_embedding=embedding_result.embedding,
                user=request.user,
                top_k=top_k,
                similarity_threshold=SIMILARITY_THRESHOLD,
                source_document_ids=document_ids
            )
            
            if not retrieved_chunks:
                return Response({
                    "answer": "Je n'ai pas trouvé d'information pertinente dans vos documents pour répondre à cette question.",
                    "sources": [],
                    "metadata": {
                        "query_time_ms": int((time.time() - start_time) * 1000),
                        "chunks_retrieved": 0,
                        "tokens_used": 0,
                        "model_used": None
                    }
                }, status=status.HTTP_200_OK)
            
            # 4. Construction du contexte RAG
            context = build_rag_context(retrieved_chunks)
            
            # 5. Génération de la réponse via OpenRouter
            logger.debug(f"🤖 Génération de la réponse via LLM...")
            messages = create_rag_prompt(question, context)
            
            completion_result = ai_router.chat_completion(
                messages=messages,
                model=model,
                temperature=0.3,  # Faible température pour plus de précision
                max_tokens=1500
            )
            
            # 6. Formatage des sources pour la réponse
            sources = []
            for chunk_data in retrieved_chunks:
                sources.append({
                    "document_id": chunk_data['source_document'].id,
                    "document_title": chunk_data['source_document'].title,
                    "page": chunk_data.get('page_number', None),
                    "excerpt": chunk_data['content'][:200] + "..." if len(chunk_data['content']) > 200 else chunk_data['content'],
                    "relevance_score": round(chunk_data['similarity_score'], 3)
                })
            
            # 7. Calcul du temps total
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # 8. Log de la requête en DB (async dans une transaction)
            with transaction.atomic():
                query_log = QueryLog.objects.create(
                    user=request.user,
                    query_text=question,
                    response_text=completion_result.content,
                    retrieved_chunks_count=len(retrieved_chunks),
                    response_time_ms=total_time_ms,
                    tokens_used=completion_result.tokens_used
                )
                
                # Association avec les documents sources
                source_doc_ids = list(set([c['source_document'].id for c in retrieved_chunks]))
                query_log.source_documents.set(source_doc_ids)
            
            logger.info(
                f"✅ Requête RAG terminée en {total_time_ms}ms - "
                f"{len(retrieved_chunks)} chunks, {completion_result.tokens_used} tokens"
            )
            
            # 9. Réponse finale
            return Response({
                "answer": completion_result.content,
                "sources": sources,
                "metadata": {
                    "query_time_ms": total_time_ms,
                    "chunks_retrieved": len(retrieved_chunks),
                    "tokens_used": completion_result.tokens_used,
                    "model_used": completion_result.model,
                    "query_id": query_log.id
                }
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement RAG: {str(e)}", exc_info=True)
            
            return Response({
                "error": "Une erreur est survenue lors du traitement de votre question",
                "details": str(e) if request.user.is_staff else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentStatsView(APIView):
    """
    Retourne les statistiques sur les documents de l'utilisateur.
    
    GET /api/rag/stats/
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Retourne les stats des documents."""
        
        from apps.documents.models import SourceDocument, DocumentChunk
        from django.db.models import Count, Sum
        
        # Stats globales
        user_docs = SourceDocument.objects.filter(user=request.user)
        
        stats = {
            "total_documents": user_docs.count(),
            "documents_processing": user_docs.filter(
                processing_status=SourceDocument.ProcessingStatus.PROCESSING
            ).count(),
            "documents_completed": user_docs.filter(
                processing_status=SourceDocument.ProcessingStatus.COMPLETED
            ).count(),
            "documents_failed": user_docs.filter(
                processing_status=SourceDocument.ProcessingStatus.FAILED
            ).count(),
            "total_chunks": DocumentChunk.objects.filter(
                source_document__user=request.user
            ).count(),
            "total_characters": user_docs.aggregate(
                total=Sum('total_characters')
            )['total'] or 0,
        }
        
        # Documents récents
        recent_docs = user_docs.order_by('-created_at')[:5].values(
            'id', 'title', 'processing_status', 'created_at', 'total_chunks'
        )
        
        stats['recent_documents'] = list(recent_docs)
        
        return Response(stats, status=status.HTTP_200_OK)


class RateFeedbackView(APIView):
    """
    Permet à l'utilisateur de noter une réponse RAG.
    
    POST /api/rag/feedback/
    Body: {
        "query_id": 123,
        "rating": 4  # 1-5
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Enregistre le feedback utilisateur."""
        
        from apps.documents.models import QueryLog
        
        query_id = request.data.get('query_id')
        rating = request.data.get('rating')
        
        if not query_id or not rating:
            return Response(
                {"error": "Les champs 'query_id' et 'rating' sont requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (1 <= rating <= 5):
            return Response(
                {"error": "La note doit être entre 1 et 5"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            query_log = QueryLog.objects.get(id=query_id, user=request.user)
            query_log.user_rating = rating
            query_log.save(update_fields=['user_rating'])
            
            logger.info(f"⭐ Feedback enregistré: Query {query_id} - Note {rating}/5")
            
            return Response({
                "message": "Merci pour votre feedback!",
                "query_id": query_id,
                "rating": rating
            }, status=status.HTTP_200_OK)
        
        except QueryLog.DoesNotExist:
            return Response(
                {"error": "Requête introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )


# ========================================
# URLS (à ajouter dans apps/rag/urls.py)
# ========================================

"""
from django.urls import path
from .views import AskDocumentView, DocumentStatsView, RateFeedbackView

app_name = 'rag'

urlpatterns = [
    path('ask/', AskDocumentView.as_view(), name='ask-document'),
    path('stats/', DocumentStatsView.as_view(), name='document-stats'),
    path('feedback/', RateFeedbackView.as_view(), name='rate-feedback'),
]
"""
