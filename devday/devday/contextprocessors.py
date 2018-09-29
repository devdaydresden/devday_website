from django.conf import settings
from event.models import Event


def devdaysettings_contextprocessor(request):
    return {
        'twitter_url': settings.DEVDAY_TWITTER_URL,
        'xing_url': settings.DEVDAY_XING_URL,
        'facebook_url': settings.DEVDAY_FACEBOOK_URL,
        'talk_submission_open': Event.current_submission_open(),
        'attendee_registration_open': Event.current_registration_open(),
        'sponsoring_open': settings.SPONSORING_OPEN,
    }
