"""
Django development settings for local devday development.

"""
from .base import *

ADMINUSER_EMAIL = 'admin@devday.de'

DEBUG = True
# see: http://django-debug-toolbar.readthedocs.io/en/stable/installation.html#explicit-setup
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'devday.extras.show_toolbar_callback'
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += [
    'debug_toolbar',
]

for logname in [
    'django', 'django.request', 'cms',
    'devday', 'attendee', 'event', 'speaker', 'talk', 'twitterfeed'
]:
    LOGGING['loggers'][logname] = {
        'handlers': ['console'],
        'level': 'INFO',
    }

MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware',
              ] + MIDDLEWARE

TWITTERFEED_PROXIES = {
    'http': '',
    'https': '',
}
