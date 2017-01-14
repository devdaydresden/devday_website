from django.conf import settings


def devdaysettings_contextprocessor(request):
    return {
        'twitter_url': settings.DEVDAY_TWITTER_URL,
        'xing_url': settings.DEVDAY_XING_URL,
        'facebook_url': settings.DEVDAY_FACEBOOK_URL,
        'talk_submission_open': settings.TALK_SUBMISSION_OPEN,
    }
