"""
Tâches Celery pour le traitement asynchrone des documents.
Gère l'extraction de texte, le chunking et la génération d'embeddings.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.files.base import File
from django.utils import timezone
from typing import List, Dict, Any, Tuple
import re
import os

# Imports pour l'extraction de texte
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

# Import des modèles (ajustez le chemin selon votre structure)
# from apps.documents.models import SourceDocument, DocumentChunk
# from apps.core.ai_router import get_ai_router

logger = get_task_logger(__name__)


# ========================================
# CONFIGURATION
# ========================================

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 512))  # Caractères par chunk
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))  # Chevauchement entre chunks


# ========================================
# UTILITAIRES D'EXTRACTION DE TEXTE
# ========================================

def extract_text_from_pdf(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extrait le texte d'un fichier PDF.
    
    Args:
        file_path: Chemin vers le fichier PDF
    
    Returns:
        Tuple (texte_extrait, métadonnées)
    
    Raises:
        Exception: Si l'extraction échoue
    """
    if not PdfReader:
        raise ImportError("pypdf n'est pas installé. Exécutez: pip install pypdf")
    
    try:
        reader = PdfReader(file_path)
        
        # Extraction des métadonnées
        metadata = {
            'num_pages': len(reader.pages),
            'author': reader.metadata.get('/Author', '') if reader.metadata else '',
            'title': reader.metadata.get('/Title', '') if reader.metadata else '',
            'creator': reader.metadata.get('/Creator', '') if reader.metadata else '',
            'creation_date': str(reader.metadata.get('/CreationDate', '')) if reader.metadata else '',
        }
        
        # Extraction du texte de toutes les pages
        full_text = ""
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    full_text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
            except Exception as e:
                logger.warning(f"⚠️ Erreur extraction page {page_num}: {str(e)}")
                continue
        
        if not full_text.strip():
            raise ValueError("Aucun texte extrait du PDF (le document est peut-être scanné)")
        
        logger.info(f"✅ PDF extrait: {len(reader.pages)} pages, {len(full_text)} caractères")
        
        return full_text.strip(), metadata
    
    except Exception as e:
        logger.error(f"❌ Erreur extraction PDF: {str(e)}")
        raise


def extract_text_from_txt(file_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Extrait le texte d'un fichier TXT.
    
    Args:
        file_path: Chemin vers le fichier TXT
    
    Returns:
        Tuple (texte_extrait, métadonnées)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        metadata = {
            'num_pages': 1,
            'encoding': 'utf-8'
        }
        
        logger.info(f"✅ TXT extrait: {len(text)} caractères")
        return text, metadata
    
    except UnicodeDecodeError:
        # Tentative avec un autre encodage
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                text = f.read()
            metadata = {'num_pages': 1, 'encoding': 'latin-1'}
            return text, metadata
        except Exception as e:
            logger.error(f"❌ Erreur extraction TXT: {str(e)}")
            raise


def ocr_pdf_with_tesseract(file_path: str) -> str:
    """
    Effectue un OCR sur un PDF scanné (placeholder pour OCR léger).
    
    NOTE: Cette fonction nécessite tesseract-ocr installé sur le système:
    sudo apt-get install tesseract-ocr tesseract-ocr-fra
    
    Args:
        file_path: Chemin vers le PDF scanné
    
    Returns:
        Texte extrait par OCR
    """
    if not pytesseract or not Image:
        raise ImportError("pytesseract et Pillow requis pour l'OCR")
    
    # TODO: Implémenter l'OCR complet avec pdf2image + tesseract
    # Pour l'instant, on retourne un placeholder
    logger.warning("⚠️ OCR non implémenté dans cette version")
    return ""


# ========================================
# CHUNKING INTELLIGENT
# ========================================

def split_text_into_chunks(
    text: str, 
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Découpe intelligemment un texte en chunks avec chevauchement.
    
    Stratégie:
    1. Découpage préférentiel sur les paragraphes (double saut de ligne)
    2. Si un paragraphe est trop long, découpage sur les phrases
    3. Chevauchement pour maintenir le contexte entre chunks
    
    Args:
        text: Texte à découper
        chunk_size: Taille cible d'un chunk (en caractères)
        overlap: Nombre de caractères à chevaucher entre chunks
    
    Returns:
        Liste de dictionnaires avec 'content' et 'metadata'
    """
    # Nettoyage du texte
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 sauts de ligne
    text = re.sub(r' {2,}', ' ', text)      # Max 1 espace
    text = text.strip()
    
    # Découpage par paragraphes
    paragraphs = re.split(r'\n\n+', text)
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Si le paragraphe seul dépasse la taille, le découper par phrases
        if len(para) > chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                    current_chunk += (sentence + " ")
                else:
                    # Sauvegarder le chunk actuel
                    if current_chunk.strip():
                        chunks.append({
                            'content': current_chunk.strip(),
                            'chunk_index': chunk_index,
                            'metadata': {}
                        })
                        chunk_index += 1
                    
                    # Démarrer un nouveau chunk avec overlap
                    if overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-overlap:]
                        current_chunk = overlap_text + sentence + " "
                    else:
                        current_chunk = sentence + " "
        
        else:
            # Ajouter le paragraphe au chunk actuel
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += (para + "\n\n")
            else:
                # Sauvegarder et recommencer
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'chunk_index': chunk_index,
                        'metadata': {}
                    })
                    chunk_index += 1
                
                # Overlap
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"
    
    # Dernier chunk
    if current_chunk.strip():
        chunks.append({
            'content': current_chunk.strip(),
            'chunk_index': chunk_index,
            'metadata': {}
        })
    
    logger.info(f"✅ Texte découpé en {len(chunks)} chunks (taille: {chunk_size}, overlap: {overlap})")
    
    return chunks


# ========================================
# TÂCHE CELERY PRINCIPALE
# ========================================

@shared_task(bind=True, max_retries=3)
def process_document_ingestion(self, document_id: int):
    """
    Tâche Celery principale pour l'ingestion d'un document.
    
    Étapes:
    1. Chargement du document depuis la DB
    2. Extraction du texte (PDF, TXT, OCR)
    3. Découpage en chunks
    4. Génération des embeddings (Ollama local)
    5. Sauvegarde des chunks en DB avec vecteurs
    
    Args:
        document_id: ID du SourceDocument à traiter
    """
    # Import ici pour éviter les imports circulaires
    from apps.documents.models import SourceDocument, DocumentChunk
    from apps.core.ai_router import get_ai_router
    
    logger.info(f"🚀 Démarrage ingestion document ID={document_id}")
    
    try:
        # 1. Chargement du document
        document = SourceDocument.objects.get(id=document_id)
        document.mark_as_processing()
        
        file_path = document.file.path
        file_type = document.file_type.lower()
        
        # 2. Extraction du texte selon le type de fichier
        if 'pdf' in file_type:
            try:
                extracted_text, metadata = extract_text_from_pdf(file_path)
            except ValueError:
                # PDF scanné, tentative OCR
                logger.warning(f"⚠️ PDF scanné détecté, tentative OCR...")
                extracted_text = ocr_pdf_with_tesseract(file_path)
                metadata = {'num_pages': 0, 'ocr_used': True}
                
                if not extracted_text:
                    raise ValueError("OCR échoué: aucun texte extrait")
        
        elif 'text' in file_type or file_path.endswith('.txt'):
            extracted_text, metadata = extract_text_from_txt(file_path)
        
        else:
            raise ValueError(f"Type de fichier non supporté: {file_type}")
        
        # Mise à jour des métadonnées du document
        document.extracted_metadata = metadata
        document.total_pages = metadata.get('num_pages', 0)
        document.total_characters = len(extracted_text)
        document.save(update_fields=['extracted_metadata', 'total_pages', 'total_characters'])
        
        # 3. Découpage en chunks
        chunks_data = split_text_into_chunks(extracted_text)
        
        if not chunks_data:
            raise ValueError("Aucun chunk généré (texte trop court?)")
        
        # 4. Génération des embeddings et sauvegarde
        ai_router = get_ai_router()
        chunks_created = 0
        
        for chunk_data in chunks_data:
            try:
                # Génération de l'embedding (local Ollama)
                embedding_result = ai_router.get_embedding(
                    text=chunk_data['content'],
                    normalize=True
                )
                
                # Création du DocumentChunk
                DocumentChunk.objects.create(
                    source_document=document,
                    content=chunk_data['content'],
                    embedding=embedding_result.embedding,
                    chunk_index=chunk_data['chunk_index'],
                    metadata=chunk_data.get('metadata', {})
                )
                
                chunks_created += 1
                
                # Log de progression tous les 10 chunks
                if chunks_created % 10 == 0:
                    logger.info(f"  📦 {chunks_created}/{len(chunks_data)} chunks traités...")
            
            except Exception as e:
                logger.error(f"❌ Erreur traitement chunk {chunk_data['chunk_index']}: {str(e)}")
                # Continue avec les autres chunks
                continue
        
        # 5. Finalisation
        if chunks_created == 0:
            raise ValueError("Aucun chunk n'a pu être créé")
        
        document.mark_as_completed(total_chunks=chunks_created)
        
        logger.info(
            f"✅ Ingestion terminée - Document ID={document_id} | "
            f"Chunks: {chunks_created} | Caractères: {document.total_characters}"
        )
        
        return {
            'status': 'success',
            'document_id': document_id,
            'chunks_created': chunks_created,
            'total_characters': document.total_characters
        }
    
    except SourceDocument.DoesNotExist:
        logger.error(f"❌ Document ID={document_id} introuvable")
        raise
    
    except Exception as e:
        error_message = f"Erreur lors de l'ingestion: {str(e)}"
        logger.error(f"❌ {error_message}")
        
        # Mise à jour du statut d'erreur
        try:
            document = SourceDocument.objects.get(id=document_id)
            document.mark_as_failed(error_message)
        except:
            pass
        
        # Retry de la tâche (max 3 tentatives)
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_failed_documents():
    """
    Tâche périodique pour nettoyer les documents en échec depuis plus de 24h.
    À exécuter via Celery Beat.
    """
    from apps.documents.models import SourceDocument
    from datetime import timedelta
    
    threshold_date = timezone.now() - timedelta(hours=24)
    
    failed_docs = SourceDocument.objects.filter(
        processing_status=SourceDocument.ProcessingStatus.FAILED,
        updated_at__lt=threshold_date
    )
    
    count = failed_docs.count()
    
    if count > 0:
        logger.info(f"🗑️ Nettoyage de {count} documents en échec...")
        failed_docs.delete()
    
    return {'cleaned': count}


@shared_task
def reprocess_document(document_id: int):
    """
    Retente le traitement d'un document échoué.
    Supprime les anciens chunks avant de recommencer.
    
    Args:
        document_id: ID du document à retraiter
    """
    from apps.documents.models import SourceDocument, DocumentChunk
    
    try:
        document = SourceDocument.objects.get(id=document_id)
        
        # Suppression des anciens chunks
        DocumentChunk.objects.filter(source_document=document).delete()
        
        # Reset du statut
        document.processing_status = SourceDocument.ProcessingStatus.PENDING
        document.processing_error = None
        document.save(update_fields=['processing_status', 'processing_error'])
        
        # Relance du traitement
        process_document_ingestion.delay(document_id)
        
        logger.info(f"🔄 Retraitement lancé pour document ID={document_id}")
        
        return {'status': 'relaunched', 'document_id': document_id}
    
    except SourceDocument.DoesNotExist:
        logger.error(f"❌ Document ID={document_id} introuvable")
        raise
