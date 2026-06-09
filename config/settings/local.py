"""
HR-Pro Local Development Settings (Docker'siz)
SQLite + Console email + No Redis
"""

from .base import *

# Remove production-only apps for local development
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ['django_celery_beat']]

# Remove whitenoise middleware for local
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'whitenoise' not in mw]

# Debug mode
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# SQLite database (PostgreSQL o'rniga)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache - local memory (Redis o'rniga)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email - console (MailHog o'rniga)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery - eager mode (Redis'siz)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Static files - whitenoise disabled for local
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
