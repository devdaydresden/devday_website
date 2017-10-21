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
    ('Stefan Bethke', 'stefan.bethke@t-systems.com'),
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_FROM_EMAIL = 'info@devday.de'

ALLOWED_HOSTS = ['devday.de', 'www.devday.de', 'q4deumsy0dg.mms-at-work.de', 'localhost',
                 'devday-test.t-systems-mms.eu']

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
            'filename': '/home/devdayprod/devday.log',
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


TWITTERFEED_PROXIES = {
    'http': 'http://iproxy.mms-dresden.de:8080/',
    'https': 'http://iproxy.mms-dresden.de:8080/',
}

REGISTRATION_OPEN = True
TALK_SUBMISSION_OPEN = True
