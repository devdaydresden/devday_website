from django.conf import settings

from twitterfeed.models import Tweet


def twitter_feed_context_processor(request):
    result = {}
    if request.path in settings.TWITTERFEED_PATHS:
        result['twitter_feed'] = Tweet.objects.filter(show_on_site__exact=True).select_related(
            'user_profile_image').order_by('-created_at')[:5]
    return result
