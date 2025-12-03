"""
Django settings for VercelApp project.
"""

import os
from pathlib import Path
import dj_database_url
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Detectar si estamos en Vercel
IS_VERCEL = "VERCEL" in os.environ

print(f"🔧 Entorno: {'Vercel' if IS_VERCEL else 'Local'}", file=sys.stderr)

# Configuración según el entorno
if IS_VERCEL:
    # ========== CONFIGURACIÓN PARA VERCEL (PRODUCCIÓN) ==========
    print("🔄 Configurando para Vercel...", file=sys.stderr)
    
    # SECRET_KEY desde variables de entorno (OBLIGATORIO en Vercel)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("❌ ERROR: SECRET_KEY no configurada en Vercel")
    
    # DEBUG desde variables de entorno
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    
    # Hosts permitidos en Vercel
    ALLOWED_HOSTS = [
        '.vercel.app',
        '.now.sh',
        'localhost',
        '127.0.0.1',
        'rentacar-system.vercel.app',  # Tu dominio específico
    ]
    
    # Base de datos PostgreSQL para Vercel
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        print(f"✅ Usando DATABASE_URL: {DATABASE_URL[:50]}...", file=sys.stderr)
        DATABASES = {
            'default': dj_database_url.config(
                default=DATABASE_URL,
                conn_max_age=600,
                conn_health_checks=True,
                ssl_require=True
            )
        }
    else:
        print("⚠️  DATABASE_URL no encontrada, usando configuración directa", file=sys.stderr)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('POSTGRES_DATABASE', 'neondb'),
                'USER': os.environ.get('POSTGRES_USER', 'neondb_owner'),
                'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
                'HOST': os.environ.get('POSTGRES_HOST', 'ep-steep-boat-a4php2pb-pooler.us-east-1.aws.neon.tech'),
                'PORT': os.environ.get('POSTGRES_PORT', '5432'),
                'OPTIONS': {'sslmode': 'require'},
            }
        }
    
    # Archivos estáticos con WhiteNoise
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Seguridad para producción
    if not DEBUG:
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
        SECURE_BROWSER_XSS_FILTER = True
        SECURE_CONTENT_TYPE_NOSNIFF = True
    
    print(f"✅ Configuración Vercel completada. DEBUG={DEBUG}", file=sys.stderr)
    
else:
    # ========== CONFIGURACIÓN PARA DESARROLLO LOCAL ==========
    print("🔄 Configurando para desarrollo local...", file=sys.stderr)
    
    # Clave secreta para desarrollo
    SECRET_KEY = 'django-insecure-clave-segura-para-desarrollo-local-12345'
    
    # Debug activado en local
    DEBUG = True
    
    # Hosts permitidos en local
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    
    # SQLite para desarrollo local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
    print("✅ Configuración local completada", file=sys.stderr)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rentacar_app',  # Tu aplicación principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # IMPORTANTE para Vercel
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'VercelApp.urls'

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

WSGI_APPLICATION = 'VercelApp.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'