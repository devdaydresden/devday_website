from django.http import HttpResponse, JsonResponse
from django.views import View

from .models import Tweet


class TwitterwallView(View):
    def get(self, request):
        tweets = Tweet.objects.all().order_by('-created_at')[:100]
        r = []
        for tweet in tweets:
            r.append({
                "id": tweet.twitter_id,
                "location": "",
                "profileImage":
                    tweet.user_profile_image.user_profile_image_url,
                "screenName": tweet.user_screen_name,
                "text": tweet.text,
                "time": tweet.created_at.isoformat(),
            })
        return JsonResponse({"tweets": r})
