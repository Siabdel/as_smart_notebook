"""
Gestionnaire unifié pour les appels IA hybrides.
- Local (Ollama): Embeddings avec nomic-embed-text
- Cloud (OpenRouter): Génération de texte avec Claude/DeepSeek
"""

import httpx
import os
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import json
import time
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Énumération des fournisseurs IA disponibles."""
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


@dataclass
class EmbeddingResult:
    """Résultat d'une génération d'embedding."""
    embedding: List[float]
    model: str
    dimensions: int
    provider: AIProvider
    execution_time_ms: int


@dataclass
class ChatMessage:
    """Message dans une conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class ChatCompletionResult:
    """Résultat d'une complétion de chat."""
    content: str
    model: str
    provider: AIProvider
    tokens_used: int
    execution_time_ms: int
    finish_reason: str


class OllamaConnectionError(Exception):
    """Erreur de connexion au serveur Ollama."""
    pass


class OpenRouterConnectionError(Exception):
    """Erreur de connexion à l'API OpenRouter."""
    pass


class AIRouter:
    """
    Routeur IA hybride qui gère les appels locaux (Ollama) et cloud (OpenRouter).
    
    Architecture:
    - Embeddings : Toujours en local via Ollama (nomic-embed-text)
    - Chat/Génération : Toujours en cloud via OpenRouter (Claude/DeepSeek)
    
    Configuration via variables d'environnement:
    - OLLAMA_BASE_URL
    - OLLAMA_EMBEDDING_MODEL
    - OPENROUTER_API_KEY
    - OPENROUTER_BASE_URL
    - OPENROUTER_DEFAULT_MODEL
    """
    
    def __init__(
        self,
        ollama_base_url: Optional[str] = None,
        ollama_embedding_model: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        openrouter_base_url: Optional[str] = None,
        openrouter_default_model: Optional[str] = None,
        timeout: int = 120
    ):
        """
        Initialise le routeur IA avec les configurations nécessaires.
        
        Args:
            ollama_base_url: URL du serveur Ollama (défaut: http://localhost:11434)
            ollama_embedding_model: Modèle d'embedding Ollama (défaut: nomic-embed-text)
            openrouter_api_key: Clé API OpenRouter
            openrouter_base_url: URL de l'API OpenRouter
            openrouter_default_model: Modèle par défaut pour OpenRouter
            timeout: Timeout pour les requêtes HTTP (secondes)
        """
        # Configuration Ollama (Local)
        self.ollama_base_url = ollama_base_url or os.getenv(
            'OLLAMA_BASE_URL', 
            'http://localhost:11434'
        )
        self.ollama_embedding_model = ollama_embedding_model or os.getenv(
            'OLLAMA_EMBEDDING_MODEL', 
            'nomic-embed-text'
        )
        
        # Configuration OpenRouter (Cloud)
        self.openrouter_api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        self.openrouter_base_url = openrouter_base_url or os.getenv(
            'OPENROUTER_BASE_URL',
            'https://openrouter.ai/api/v1'
        )
        self.openrouter_default_model = openrouter_default_model or os.getenv(
            'OPENROUTER_DEFAULT_MODEL',
            'anthropic/claude-3.5-sonnet'
        )
        
        # Validation de la configuration
        if not self.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY non configurée. Les fonctionnalités de chat seront indisponibles.")
        
        # Client HTTP pour Ollama
        self.http_client = httpx.Client(timeout=timeout)
        
        # Client OpenAI-compatible pour OpenRouter
        if self.openrouter_api_key:
            self.openrouter_client = OpenAI(
                base_url=self.openrouter_base_url,
                api_key=self.openrouter_api_key,
                timeout=timeout
            )
        else:
            self.openrouter_client = None
        
        logger.info(f"✅ AIRouter initialisé - Ollama: {self.ollama_base_url} | OpenRouter: {'Configuré' if self.openrouter_client else 'Non configuré'}")
    
    # ========================================
    # EMBEDDINGS (LOCAL - OLLAMA)
    # ========================================
    
    def get_embedding(
        self, 
        text: str,
        model: Optional[str] = None,
        normalize: bool = True
    ) -> EmbeddingResult:
        """
        Génère un embedding vectoriel pour un texte donné (local Ollama).
        
        Args:
            text: Texte à vectoriser
            model: Modèle d'embedding à utiliser (défaut: nomic-embed-text)
            normalize: Normaliser le vecteur (recommandé pour la recherche de similarité)
        
        Returns:
            EmbeddingResult avec le vecteur généré
        
        Raises:
            OllamaConnectionError: Si la connexion à Ollama échoue
        """
        model = model or self.ollama_embedding_model
        start_time = time.time()
        
        try:
            # Appel à l'API Ollama /api/embeddings
            url = f"{self.ollama_base_url}/api/embeddings"
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = self.http_client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get('embedding')
            
            if not embedding:
                raise OllamaConnectionError("Aucun embedding retourné par Ollama")
            
            # Normalisation du vecteur si demandée
            if normalize:
                import numpy as np
                embedding = np.array(embedding)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = (embedding / norm).tolist()
            
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.debug(f"✅ Embedding généré - Modèle: {model} | Dimensions: {len(embedding)} | Temps: {execution_time}ms")
            
            return EmbeddingResult(
                embedding=embedding,
                model=model,
                dimensions=len(embedding),
                provider=AIProvider.OLLAMA,
                execution_time_ms=execution_time
            )
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Erreur HTTP Ollama: {e.response.status_code} - {e.response.text}")
            raise OllamaConnectionError(f"Erreur HTTP {e.response.status_code}: {e.response.text}")
        
        except httpx.RequestError as e:
            logger.error(f"❌ Erreur de connexion Ollama: {str(e)}")
            raise OllamaConnectionError(f"Impossible de se connecter à Ollama sur {self.ollama_base_url}: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la génération d'embedding: {str(e)}")
            raise OllamaConnectionError(f"Erreur inattendue: {str(e)}")
    
    def get_embeddings_batch(
        self, 
        texts: List[str],
        model: Optional[str] = None,
        normalize: bool = True
    ) -> List[EmbeddingResult]:
        """
        Génère des embeddings pour plusieurs textes (séquentiel).
        
        Args:
            texts: Liste de textes à vectoriser
            model: Modèle d'embedding
            normalize: Normaliser les vecteurs
        
        Returns:
            Liste d'EmbeddingResult
        """
        results = []
        for text in texts:
            result = self.get_embedding(text, model=model, normalize=normalize)
            results.append(result)
        
        logger.info(f"✅ Batch d'embeddings généré: {len(results)} textes")
        return results
    
    # ========================================
    # CHAT COMPLETION (CLOUD - OPENROUTER)
    # ========================================
    
    def chat_completion(
        self,
        messages: List[ChatMessage] | List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> ChatCompletionResult:
        """
        Génère une réponse de chat via OpenRouter (Claude, DeepSeek, etc.).
        
        Args:
            messages: Liste de messages (format ChatMessage ou dict)
            model: Modèle à utiliser (défaut: claude-3.5-sonnet)
            temperature: Créativité (0.0 = déterministe, 1.0 = créatif)
            max_tokens: Nombre maximum de tokens dans la réponse
            stream: Mode streaming (non implémenté dans cette version)
        
        Returns:
            ChatCompletionResult avec la réponse générée
        
        Raises:
            OpenRouterConnectionError: Si l'appel échoue
        """
        if not self.openrouter_client:
            raise OpenRouterConnectionError("OpenRouter n'est pas configuré (clé API manquante)")
        
        model = model or self.openrouter_default_model
        start_time = time.time()
        
        # Conversion des messages au format OpenAI
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            else:
                formatted_messages.append(msg)
        
        try:
            # Appel à l'API OpenRouter (compatible OpenAI)
            response = self.openrouter_client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Extraction de la réponse
            choice = response.choices[0]
            content = choice.message.content
            finish_reason = choice.finish_reason
            
            # Comptage des tokens
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            logger.info(
                f"✅ Chat completion - Modèle: {model} | Tokens: {tokens_used} | "
                f"Temps: {execution_time}ms | Finish: {finish_reason}"
            )
            
            return ChatCompletionResult(
                content=content,
                model=model,
                provider=AIProvider.OPENROUTER,
                tokens_used=tokens_used,
                execution_time_ms=execution_time,
                finish_reason=finish_reason
            )
        
        except Exception as e:
            logger.error(f"❌ Erreur OpenRouter: {str(e)}")
            raise OpenRouterConnectionError(f"Erreur lors de l'appel à OpenRouter: {str(e)}")
    
    # ========================================
    # MÉTHODES UTILITAIRES
    # ========================================
    
    def test_ollama_connection(self) -> bool:
        """
        Teste la connexion au serveur Ollama.
        
        Returns:
            True si la connexion est OK, False sinon
        """
        try:
            url = f"{self.ollama_base_url}/api/tags"
            response = self.http_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            logger.info(f"✅ Connexion Ollama OK - {len(models)} modèles disponibles")
            
            # Vérification que le modèle d'embedding est disponible
            model_names = [m.get('name', '') for m in models]
            if self.ollama_embedding_model not in model_names:
                logger.warning(
                    f"⚠️ Modèle '{self.ollama_embedding_model}' non trouvé. "
                    f"Modèles disponibles: {', '.join(model_names)}"
                )
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Connexion Ollama échouée: {str(e)}")
            return False
    
    def test_openrouter_connection(self) -> bool:
        """
        Teste la connexion à l'API OpenRouter.
        
        Returns:
            True si la connexion est OK, False sinon
        """
        if not self.openrouter_client:
            logger.error("❌ OpenRouter non configuré")
            return False
        
        try:
            # Test avec un message minimal
            messages = [ChatMessage(role="user", content="Hello")]
            result = self.chat_completion(messages, max_tokens=10)
            
            logger.info(f"✅ Connexion OpenRouter OK - Modèle: {result.model}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Connexion OpenRouter échouée: {str(e)}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de santé des deux providers.
        
        Returns:
            Dictionnaire avec les statuts et informations
        """
        return {
            "ollama": {
                "configured": True,
                "url": self.ollama_base_url,
                "model": self.ollama_embedding_model,
                "status": "healthy" if self.test_ollama_connection() else "unhealthy"
            },
            "openrouter": {
                "configured": self.openrouter_client is not None,
                "model": self.openrouter_default_model,
                "status": "healthy" if self.test_openrouter_connection() else "unhealthy"
            }
        }
    
    def __del__(self):
        """Ferme proprement les connexions HTTP."""
        try:
            self.http_client.close()
        except:
            pass


# ========================================
# SINGLETON GLOBAL (optionnel)
# ========================================

_ai_router_instance: Optional[AIRouter] = None

def get_ai_router() -> AIRouter:
    """
    Retourne l'instance singleton du routeur IA.
    Utilisé dans les vues Django pour éviter la réinstanciation.
    """
    global _ai_router_instance
    if _ai_router_instance is None:
        _ai_router_instance = AIRouter()
    return _ai_router_instance
