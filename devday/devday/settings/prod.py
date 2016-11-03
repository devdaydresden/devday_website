"""
Django production settings for devday.

"""
# noinspection PyUnresolvedReferences
from .base import *

DATA_DIR = '/var/www/html/devday'

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

ADMINS = [
    ('Jan Dittberner', 'jan.dittberner@t-systems.com'),
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_FROM_EMAIL = 'info@devday.de'

ALLOWED_HOSTS = ['devday.de', 'www.devday.de', 'q4deumsy0dg.mms-at-work.de', 'localhost', 'devday-test.t-systems-mms.eu']

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
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/devdayprod/devday.log',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'attendee': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'devday': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'talk': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
