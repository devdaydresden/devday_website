"""
Django development settings for local devday development.

"""

import os

from .base import *

ADMINUSER_EMAIL = 'admin@devday.de'

DEBUG = True
# see: http://django-debug-toolbar.readthedocs.io/en/stable/installation.html#explicit-setup
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'devday.extras.show_toolbar_callback'
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# for development, we're using the upcoming event. Cf.
# devday/event/migrations/0001_initial.py
EVENT_ID = 3

INSTALLED_APPS += [
    'debug_toolbar',
]

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

MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware',
                      ] + MIDDLEWARE_CLASSES

TWITTERFEED_PROXIES = {
    'http': 'http://proxy.mms-dresden.de:8080/',
    'https': 'http://proxy.mms-dresden.de:8080/',
}
