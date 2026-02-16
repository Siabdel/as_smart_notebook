"""
Configuration Django pour Smart-Notebook.
Intègre PostgreSQL avec pgvector, Celery, Redis et les apps principales.

Ce fichier doit être placé dans config/settings.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
load_dotenv()

# Répertoires de base
BASE_DIR = Path(__file__).resolve().parent.parent

# ========================================
# SÉCURITÉ
# ========================================

SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ========================================
# APPLICATIONS INSTALLÉES
# ========================================

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_celery_results',  # Optionnel: pour stocker les résultats Celery en DB
    
    # Apps locales
    'apps.core',
    'apps.documents',
    'apps.rag',
    'apps.podcasts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS doit être avant CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ========================================
# BASE DE DONNÉES POSTGRESQL + PGVECTOR
# ========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'smartnotebook'),
        'USER': os.getenv('DB_USER', 'smartnotebook_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            # Options PostgreSQL recommandées pour pgvector
            'options': '-c search_path=public',
        },
    }
}

# ========================================
# AUTHENTIFICATION
# ========================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ========================================
# INTERNATIONALISATION
# ========================================

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True

# ========================================
# FICHIERS STATIQUES ET MÉDIAS
# ========================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(BASE_DIR / 'media'))

# ========================================
# DJANGO REST FRAMEWORK
# ========================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Optionnel
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# ========================================
# CORS (pour Vue.js)
# ========================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server (Vue.js)
    "http://localhost:3000",  # Alternative
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# ========================================
# CELERY CONFIGURATION
# ========================================

CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/1')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Configuration des queues
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'ingestion': {
        'exchange': 'ingestion',
        'routing_key': 'ingestion',
    },
    'podcast': {
        'exchange': 'podcast',
        'routing_key': 'podcast',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance',
    },
}

# ========================================
# LOGGING
# ========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Création du dossier logs s'il n'existe pas
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# ========================================
# CONFIGURATION IA (OLLAMA + OPENROUTER)
# ========================================

# Ollama (Local)
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')

# OpenRouter (Cloud)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
OPENROUTER_DEFAULT_MODEL = os.getenv('OPENROUTER_DEFAULT_MODEL', 'anthropic/claude-3.5-sonnet')

# ========================================
# CONFIGURATION RAG
# ========================================

CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 512))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 5))

# ========================================
# SÉCURITÉ EN PRODUCTION
# ========================================

if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Autres
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# ========================================
# AUTRES CONFIGURATIONS
# ========================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Taille maximale des fichiers uploadés (50 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB

# Taille maximale totale d'une requête
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
