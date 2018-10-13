"""
Django production settings for devday.

"""
from .base import *

ADMINS = [
    ('Jan Dittberner', 'jan.dittberner@t-systems.com'),
    ('Stefan Bethke', 'stefan.bethke@t-systems.com'),
]
ADMINUSER_EMAIL = get_env_variable('DEVDAY_ADMINUSER_EMAIL')

ALLOWED_HOSTS = ['devday.de', 'www.devday.de',
                 'localhost', 'devday-test.mms-at-work.de']

DEFAULT_FROM_EMAIL = 'info@devday.de'

EMAIL_HOST = 'mail'
EMAIL_SUBJECT_PREFIX = '[Dev Day] '

LOGGING.update({
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
})

LOGGING['handlers'].update({
    'mail_admins': {
        'level': 'ERROR',
        'class': 'django.utils.log.AdminEmailHandler',
        'include_html': True,
        'filters': ['require_debug_false'],
    },
    'file': {
        'class': 'logging.FileHandler',
        'filename': os.path.join(BASE_DIR, 'logs', 'devday.log'),
        'formatter': 'simple',
        'level': 'INFO',
    },
})

for logname in [
    'django', 'cms',
    'devday', 'attendee', 'event', 'speaker', 'talk', 'twitterfeed'
]:
    LOGGING['loggers'][logname] = {
        'handlers': ['file', 'mail_admins'],
        'level': 'INFO',
        'propagate': True,
    }

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TWITTERFEED_PROXIES = {
    'http': 'http://iproxy.mms-dresden.de:8080/',
    'https': 'http://iproxy.mms-dresden.de:8080/',
}
