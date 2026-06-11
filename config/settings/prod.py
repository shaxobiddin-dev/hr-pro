"""
HR-Pro Production Settings
Server: DigitalOcean Droplet (Ubuntu)
"""

import os
from .base import *

# Debug mode - NEVER True in production
DEBUG = False

# Allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '137.184.104.67').split(',')

# Secret key - MUST be set in environment
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production-immediately!')

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'hrpro_db'),
        'USER': os.getenv('DB_USER', 'hrpro_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'HrPro_Secure_2024!'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Security settings (SSL keyin qo'shiladi)
SECURE_SSL_REDIRECT = os.getenv('USE_SSL', 'False') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('USE_SSL', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('USE_SSL', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    'http://137.184.104.67',
    # Domain qo'shilganda:
    # 'https://your-domain.com',
]

# Static files
STATIC_ROOT = os.getenv('STATIC_ROOT', '/var/www/hr-pro/staticfiles')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/hr-pro/media')

# WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware - WhiteNoise qo'shish
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Cache - Simple (Redis yo'q)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session - Database (Redis yo'q)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Email (keyin sozlanadi)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Sentry (ixtiyoriy)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment='production',
    )

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/hr-pro/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
