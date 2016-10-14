"""
Django production settings for devday.

"""
# noinspection PyUnresolvedReferences
from .base import *

DATA_DIR = '/var/www/html/devday'

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

ALLOWED_HOSTS = ['devday.de', 'www.devday.de', 'q4deumsy0dg.mms-at-work.de', 'localhost']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join('/home/devdayprod/devday.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
