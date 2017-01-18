from datetime import datetime, timedelta
from email.utils import parsedate_tz

import pytz
import requests
from django.core.management import BaseCommand
from django.core.management import CommandError

from twitterfeed.models import TwitterSetting, Tweet


def get_access_token():
    access_token = TwitterSetting.objects.filter(name="access_token").first()
    if access_token is None:
        try:
            consumer_key = TwitterSetting.objects.get(name="consumer_key").value
            consumer_secret = TwitterSetting.objects.get(name="consumer_secret").value
            response = requests.post(
                'https://api.twitter.com/oauth2/token',
                data={'grant_type': 'client_credentials'}, auth=(consumer_key, consumer_secret)
            )
            response.raise_for_status()
            data = response.json()
            if data['token_type'] == 'bearer':
                access_token = TwitterSetting.objects.create(name='access_token', value=data['access_token'])
            else:
                raise CommandError("unknown token_type %s" % data['token_type'])
        except TwitterSetting.DoesNotExist:
            raise CommandError(
                "necessary twitter setting consumer_key or consumer_secret does not exist. "
                "Use the admin site to set these settings")
        except requests.HTTPError:
            raise CommandError(
                "A problem occurred calling the twitter oauth2 endpoint when trying to receive an access token.")
    return access_token.value


class Command(BaseCommand):
    help = 'Fetches tweets from twitter.com'

    def handle(self, *args, **options):
        access_token = get_access_token()
        try:
            search_query = TwitterSetting.objects.get(name='search_query')
        except TwitterSetting.DoesNotExist:
            raise CommandError(
                "necessary twitter setting search_query does not exist. Use the admin site to set this setting")
        twitter_search_url = 'https://api.twitter.com/1.1/search/tweets.json'
        headers = {'Authorization': "Bearer {}".format(access_token)}
        try:
            last_tweet = Tweet.objects.latest('twitter_id')
            self.stdout.write("Fetching tweets since {}".format(last_tweet.twitter_id))
            response = requests.get(twitter_search_url, headers=headers, params={
                'q': search_query.value, 'include_entities': False, 'count': 100,
                'since_id': last_tweet.twitter_id})
        except Tweet.DoesNotExist:
            self.stdout.write("no tweets yet, fetching tweets from one year in the past")
            response = requests.get(twitter_search_url, headers=headers, params={
                'q': search_query.value, 'include_entities': False, 'count': 100})
        response.raise_for_status()
        data = response.json()
        for tweet in data['statuses']:
            time_tuple = parsedate_tz(tweet['created_at'])
            tweet_datetime = datetime(*time_tuple[:6], tzinfo=pytz.utc)
            tweet_datetime -= timedelta(seconds=time_tuple[-1])
            Tweet.objects.create(
                twitter_id=tweet['id'],
                user_profile_image_url=tweet['user']['profile_image_url_https'],
                user_name=tweet['user']['name'],
                user_screen_name=tweet['user']['screen_name'],
                text=tweet['text'],
                created_at=tweet_datetime)
