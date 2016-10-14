"""
Django production settings for devday.

"""
# noinspection PyUnresolvedReferences
from .base import *

DATA_DIR = '/var/www/html/devday'

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

ALLOWED_HOSTS = ['devday.de', 'www.devday.de', 'q4deumsy0dg.mms-at-work.de', 'localhost']
