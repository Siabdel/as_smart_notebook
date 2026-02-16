"""
Configuration Celery pour Smart-Notebook.
Gère les tâches asynchrones (ingestion de documents, génération de podcasts).

Documentation: https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Création de l'instance Celery
app = Celery('smartnotebook')

# Configuration depuis les settings Django avec le préfixe CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches dans les apps Django
# Celery cherche les fichiers tasks.py dans chaque app installée
app.autodiscover_tasks()


# ========================================
# CONFIGURATION DES TÂCHES PÉRIODIQUES (CELERY BEAT)
# ========================================

app.conf.beat_schedule = {
    # Nettoyage des documents échoués toutes les 6 heures
    'cleanup-failed-documents': {
        'task': 'apps.documents.tasks.cleanup_failed_documents',
        'schedule': crontab(minute=0, hour='*/6'),  # Toutes les 6h
        'options': {
            'expires': 3600,  # Expire après 1h si non exécuté
        }
    },
    
    # TODO: Ajouter d'autres tâches périodiques ici
    # Exemple: Génération de rapports quotidiens, nettoyage de cache, etc.
}


# ========================================
# CONFIGURATION AVANCÉE
# ========================================

app.conf.update(
    # Sérialisation JSON pour la compatibilité
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',  # Ajustez selon votre fuseau horaire
    enable_utc=True,
    
    # Gestion des résultats
    result_backend='redis://localhost:6379/1',  # DB Redis séparée pour les résultats
    result_expires=3600,  # Résultats expirent après 1h
    
    # Limites de ressources
    worker_prefetch_multiplier=4,  # Nombre de tâches pré-chargées par worker
    worker_max_tasks_per_child=1000,  # Redémarre le worker après 1000 tâches (évite les fuites mémoire)
    
    # Timeouts
    task_time_limit=300,  # Timeout hard à 5 minutes
    task_soft_time_limit=240,  # Timeout soft à 4 minutes (permet nettoyage)
    
    # Retry configuration par défaut
    task_acks_late=True,  # Acknowledge après exécution (pas avant)
    task_reject_on_worker_lost=True,  # Rejeter les tâches si le worker crash
    
    # Optimisations
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
)


# ========================================
# ROUTES DE TÂCHES (optionnel)
# ========================================

# Permet de router certaines tâches vers des queues spécifiques
# Utile si vous avez plusieurs workers avec des capacités différentes
# (ex: un worker GPU pour les embeddings, un worker CPU pour l'extraction)

app.conf.task_routes = {
    # Tâches d'ingestion → queue 'ingestion'
    'apps.documents.tasks.process_document_ingestion': {
        'queue': 'ingestion',
        'routing_key': 'ingestion.process',
    },
    
    # Tâches de podcast → queue 'podcast'
    'apps.podcasts.tasks.*': {
        'queue': 'podcast',
        'routing_key': 'podcast.*',
    },
    
    # Tâches de nettoyage → queue 'maintenance'
    'apps.documents.tasks.cleanup_*': {
        'queue': 'maintenance',
        'routing_key': 'maintenance.*',
    },
}


# ========================================
# SIGNAL DE DEBUG (optionnel)
# ========================================

@app.task(bind=True)
def debug_task(self):
    """
    Tâche de test pour vérifier que Celery fonctionne.
    
    Usage:
    from config.celery import debug_task
    debug_task.delay()
    """
    print(f'Request: {self.request!r}')
    return {
        'status': 'OK',
        'worker': self.request.hostname,
        'task_id': self.request.id
    }
