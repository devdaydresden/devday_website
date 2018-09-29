from django.conf import settings
from event.models import Event


def devdaysettings_contextprocessor(request):
    return {
        'twitter_url': settings.DEVDAY_TWITTER_URL,
        'xing_url': settings.DEVDAY_XING_URL,
        'facebook_url': settings.DEVDAY_FACEBOOK_URL,
        'sponsoring_open': settings.SPONSORING_OPEN,
    }
