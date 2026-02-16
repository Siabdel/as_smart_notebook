#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion Ollama et la génération d'embeddings.
Usage: python scripts/test_ollama.py
"""

import sys
import httpx
import json
import time
from typing import List, Dict, Any


# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"


def print_header(text: str):
    """Affiche un header coloré."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def test_ollama_connection() -> bool:
    """
    Teste la connexion au serveur Ollama.
    """
    print_header("Test 1: Connexion au serveur Ollama")
    
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('models', [])
        
        print(f"✅ Connexion réussie à Ollama ({OLLAMA_BASE_URL})")
        print(f"📦 {len(models)} modèle(s) disponible(s):")
        
        for model in models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0) / (1024**3)  # Conversion en GB
            print(f"   - {name} ({size:.2f} GB)")
        
        return True
    
    except httpx.ConnectError:
        print(f"❌ Impossible de se connecter à Ollama sur {OLLAMA_BASE_URL}")
        print("   Vérifiez qu'Ollama est démarré:")
        print("   sudo systemctl status ollama")
        print("   ou")
        print("   ollama serve")
        return False
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


def check_model_availability(model_name: str) -> bool:
    """
    Vérifie si un modèle spécifique est disponible.
    """
    print_header(f"Test 2: Vérification du modèle {model_name}")
    
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('models', [])
        model_names = [m.get('name', '') for m in models]
        
        if model_name in model_names:
            print(f"✅ Modèle '{model_name}' trouvé et disponible")
            return True
        else:
            print(f"⚠️  Modèle '{model_name}' non trouvé")
            print(f"   Modèles disponibles: {', '.join(model_names)}")
            print(f"\n   Pour télécharger le modèle:")
            print(f"   ollama pull {model_name}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


def test_embedding_generation(text: str) -> bool:
    """
    Teste la génération d'un embedding.
    """
    print_header("Test 3: Génération d'embedding")
    
    try:
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {
            "model": EMBEDDING_MODEL,
            "prompt": text
        }
        
        print(f"📝 Texte à vectoriser: '{text}'")
        print(f"🔄 Génération en cours...")
        
        start_time = time.time()
        response = httpx.post(url, json=payload, timeout=30.0)
        response.raise_for_status()
        execution_time = (time.time() - start_time) * 1000
        
        data = response.json()
        embedding = data.get('embedding')
        
        if not embedding:
            print("❌ Aucun embedding retourné")
            return False
        
        print(f"✅ Embedding généré avec succès")
        print(f"   - Dimensions: {len(embedding)}")
        print(f"   - Temps: {execution_time:.2f} ms")
        print(f"   - Premiers 5 éléments: {embedding[:5]}")
        
        return True
    
    except httpx.HTTPStatusError as e:
        print(f"❌ Erreur HTTP {e.response.status_code}")
        print(f"   Réponse: {e.response.text}")
        return False
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


def test_similarity_search():
    """
    Teste la recherche de similarité entre plusieurs embeddings.
    """
    print_header("Test 4: Recherche de similarité")
    
    texts = [
        "Django est un framework web Python",
        "Python est un langage de programmation",
        "Le chat dort sur le canapé"
    ]
    
    try:
        embeddings = []
        
        print("🔄 Génération des embeddings...")
        for text in texts:
            url = f"{OLLAMA_BASE_URL}/api/embeddings"
            payload = {"model": EMBEDDING_MODEL, "prompt": text}
            response = httpx.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            embedding = response.json().get('embedding')
            embeddings.append(embedding)
            print(f"   ✓ '{text[:40]}...'")
        
        # Calcul de la similarité cosinus
        import numpy as np
        
        def cosine_similarity(vec1, vec2):
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        print("\n📊 Matrice de similarité:")
        print("     ", end="")
        for i in range(len(texts)):
            print(f"  Text{i+1}", end="")
        print()
        
        for i, emb1 in enumerate(embeddings):
            print(f"Text{i+1}", end="")
            for j, emb2 in enumerate(embeddings):
                similarity = cosine_similarity(emb1, emb2)
                print(f"  {similarity:.3f}", end="")
            print()
        
        # Analyse
        sim_01 = cosine_similarity(embeddings[0], embeddings[1])
        sim_02 = cosine_similarity(embeddings[0], embeddings[2])
        
        print(f"\n📈 Analyse:")
        print(f"   - Text 1 vs Text 2 (Python/Django): {sim_01:.3f}")
        print(f"   - Text 1 vs Text 3 (Django/Chat):   {sim_02:.3f}")
        
        if sim_01 > sim_02:
            print(f"   ✅ Cohérent: Les textes similaires ont un score plus élevé")
            return True
        else:
            print(f"   ⚠️  Inattendu: Les textes différents ont un score plus élevé")
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


def main():
    """
    Exécute tous les tests.
    """
    print("\n" + "🔬 SMART-NOTEBOOK - Tests Ollama".center(60))
    
    results = []
    
    # Test 1: Connexion
    results.append(("Connexion Ollama", test_ollama_connection()))
    
    if not results[-1][1]:
        print("\n❌ Impossible de continuer sans connexion Ollama")
        sys.exit(1)
    
    # Test 2: Disponibilité du modèle
    results.append((f"Modèle {EMBEDDING_MODEL}", check_model_availability(EMBEDDING_MODEL)))
    
    if not results[-1][1]:
        print("\n⚠️  Continuons quand même avec les tests suivants...")
    
    # Test 3: Génération d'embedding
    results.append(("Génération d'embedding", test_embedding_generation("Hello, this is a test")))
    
    # Test 4: Similarité (nécessite numpy)
    try:
        import numpy
        results.append(("Recherche de similarité", test_similarity_search()))
    except ImportError:
        print("\n⚠️  numpy n'est pas installé, test de similarité ignoré")
        results.append(("Recherche de similarité", None))
    
    # Résumé
    print_header("RÉSUMÉ DES TESTS")
    
    total = len([r for r in results if r[1] is not None])
    passed = len([r for r in results if r[1] is True])
    
    for name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"{status} - {name}")
    
    print(f"\n📊 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés ! Ollama est prêt pour Smart-Notebook.")
        sys.exit(0)
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez la configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
