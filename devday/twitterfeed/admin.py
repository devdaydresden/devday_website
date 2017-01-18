from django.contrib.admin import site

from twitterfeed.models import Tweet, TwitterSetting

site.register(TwitterSetting)
site.register(Tweet)
