import json
from datetime import datetime, timedelta
from email.utils import parsedate_tz

import pytz
import requests
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.db.transaction import atomic

from twitterfeed.models import TwitterSetting, Tweet, TwitterProfileImage


def get_access_token():
    access_token = TwitterSetting.objects.filter(name="access_token").first()
    if access_token is None:
        try:
            consumer_key = TwitterSetting.objects.get(name="consumer_key").value
            consumer_secret = TwitterSetting.objects.get(name="consumer_secret").value
            response = requests.post(
                'https://api.twitter.com/oauth2/token',
                data={'grant_type': 'client_credentials'}, auth=(consumer_key, consumer_secret),
                proxies=settings.TWITTERFEED_PROXIES
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


def create_markup(text, entities):
    result = text
    if 'hashtags' in entities:
        for hashtag in entities['hashtags']:
            result = result.replace(
                '#{}'.format(hashtag['text']),
                '<a href="https://twitter.com/hashtag/{0:s}">#{0:s}</a>'.format(hashtag['text'])
            )
    if 'media' in entities:
        for media in entities['media']:
            result = result.replace(
                media['url'],
                '<a href="{0:s}">{1:s}</a>'.format(media['media_url_https'], media['url'])
            )
    if 'urls' in entities:
        for url in entities['urls']:
            result = result.replace(
                url['url'],
                '<a href="{0:s}">{0:s}</a>'.format(url['url'])
            )
    if 'user_mentions' in entities:
        for user_mention in entities['user_mentions']:
            result = result.replace(
                '@{}'.format(user_mention['screen_name']),
                '<a href="https://twitter.com/{0:s}">@{0:s}</a>'.format(user_mention['screen_name'])
            )
    return result


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
            if options['verbosity'] > 0:
                self.stdout.write("Fetching tweets since {}".format(last_tweet.twitter_id))
            response = requests.get(twitter_search_url, headers=headers, params={
                'q': search_query.value, 'include_entities': 'true', 'count': 100,
                'since_id': last_tweet.twitter_id}, proxies=settings.TWITTERFEED_PROXIES)
        except Tweet.DoesNotExist:
            if options['verbosity'] > 0:
                self.stdout.write("no tweets yet, fetching tweets from one year in the past")
            response = requests.get(
                twitter_search_url, headers=headers,
                params={'q': search_query.value, 'include_entities': 'true', 'count': 100, 'tweet_mode': 'extended'},
                proxies=settings.TWITTERFEED_PROXIES)
        if options['verbosity'] > 1:
            self.stdout.write("fetched from " + response.url)
        response.raise_for_status()
        data = response.json()
        for tweet in data['statuses']:
            self.handle_tweet(tweet, options['verbosity'])

    @atomic
    def handle_tweet(self, tweet, verbosity):
        time_tuple = parsedate_tz(tweet['created_at'])
        tweet_datetime = datetime(*time_tuple[:6], tzinfo=pytz.utc)
        tweet_datetime -= timedelta(seconds=time_tuple[-1])
        profile_image, created = TwitterProfileImage.objects.get_or_create(
            user_profile_image_url=tweet['user']['profile_image_url_https'])
        if created:
            if verbosity > 1:
                self.stdout.write("add profile with url " + profile_image.user_profile_image_url)
            image_response = requests.get(
                profile_image.user_profile_image_url.replace('_normal', '_bigger'),
                proxies=settings.TWITTERFEED_PROXIES)
            image_response.raise_for_status()
            profile_image.image_data = SimpleUploadedFile(
                name=profile_image.user_profile_image_url.split('/')[-1],
                content=image_response.content,
                content_type=image_response.headers['Content-Type'])
            profile_image.save()
        Tweet.objects.create(
            twitter_id=tweet['id'],
            user_profile_image=profile_image,
            user_name=tweet['user']['name'],
            user_screen_name=tweet['user']['screen_name'],
            text=create_markup(tweet['text'], tweet['entities']),
            plain_text=tweet['text'],
            entities=json.dumps(tweet['entities']),
            created_at=tweet_datetime)
