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
