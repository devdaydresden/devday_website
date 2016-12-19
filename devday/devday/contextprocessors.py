from django.conf import settings


def devdaysettings_contextprocessor(request):
    return {
        'twitter_url': settings.DEVDAY_TWITTER_URL
    }
