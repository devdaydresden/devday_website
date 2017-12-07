"""
Django development settings for local devday development.

"""

import os

from .base import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

MIDDLEWARE_CLASSES = [
                         'debug_toolbar.middleware.DebugToolbarMiddleware',
                     ] + MIDDLEWARE_CLASSES

INSTALLED_APPS += [
    'debug_toolbar',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# settings for django-debug-toolbar
# see: http://django-debug-toolbar.readthedocs.io/en/stable/installation.html#explicit-setup
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INTERNAL_IPS = ('127.0.0.1', '::1')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)s %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        }

    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'devday.log'),
            'formatter': 'simple',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'attendee': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'devday': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'talk': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

#EVENT_ID = 1
TALK_SUBMISSION_OPEN = True

TWITTERFEED_PROXIES = {
    'http': 'http://proxy.mms-dresden.de:8080/',
    'https': 'http://proxy.mms-dresden.de:8080/',
}

REGISTRATION_OPEN = True
