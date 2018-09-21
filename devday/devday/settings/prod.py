"""
Django production settings for devday.

"""
# noinspection PyUnresolvedReferences
from .base import *

ADMINS = [
    ('Jan Dittberner', 'jan.dittberner@t-systems.com'),
    ('Stefan Bethke', 'stefan.bethke@t-systems.com'),
]
ALLOWED_HOSTS = ['devday.de', 'www.devday.de', 'q4deumsy0dg.mms-at-work.de',
                 'localhost', 'devday-test.t-systems-mms.eu']

DATA_DIR = '/var/www/html/devday'
DEFAULT_FROM_EMAIL = 'info@devday.de'

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
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/srv/devday/devday.log',
            'formatter': 'simple',
            'level': 'INFO',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'attendee': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'devday': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'talk': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'cms': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

REGISTRATION_OPEN = False

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
STATIC_ROOT = os.path.join(DATA_DIR, 'static')

TWITTERFEED_PROXIES = {
    'http': 'http://iproxy.mms-dresden.de:8080/',
    'https': 'http://iproxy.mms-dresden.de:8080/',
}

TALK_SUBMISSION_OPEN = False
