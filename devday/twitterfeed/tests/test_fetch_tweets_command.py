import codecs
from email.utils import formatdate

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone

from twitterfeed.management.commands.fetch_tweets import get_access_token, create_markup, Command as FetchTweetCommand
from twitterfeed.models import TwitterSetting, Tweet, TwitterProfileImage

try:
    # noinspection PyCompatibility
    from unittest.mock import call, patch, MagicMock
except ImportError:
    # noinspection PyUnresolvedReferences
    from mock import call, patch, MagicMock


@patch('twitterfeed.management.commands.fetch_tweets.requests.post')
@override_settings(TWITTERFEED_PROXIES={})
class TestGetAccessToken(TestCase):
    def test_get_access_token_needs_consumer_key(self, mock_post):
        with self.assertRaises(CommandError) as exception_context:
            get_access_token()
        self.assertEqual(
            "{}".format(exception_context.exception),
            "necessary twitter setting consumer_key or consumer_secret does not exist. "
            "Use the admin site to set these settings")
        mock_post.assert_not_called()

    def test_get_access_token_needs_consumer_secret(self, mock_post):
        TwitterSetting.objects.create(name='consumer_key', value='myconsumer')
        with self.assertRaises(CommandError) as exception_context:
            get_access_token()
        self.assertEqual(
            "{}".format(exception_context.exception),
            "necessary twitter setting consumer_key or consumer_secret does not exist. "
            "Use the admin site to set these settings")
        mock_post.assert_not_called()

    def test_get_access_token_handles_http_error(self, mock_post):
        TwitterSetting.objects.create(name='consumer_key', value='myconsumer')
        TwitterSetting.objects.create(name='consumer_secret', value='mysecret')
        mock_post.side_effect = requests.HTTPError
        with self.assertRaises(CommandError) as exception_context:
            get_access_token()
        self.assertEqual(
            "{}".format(exception_context.exception),
            "A problem occurred calling the twitter oauth2 endpoint when trying to receive an access token.")
        mock_post.assert_called_with(
            'https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'},
            auth=('myconsumer', 'mysecret'), proxies={})

    def test_get_access_token_handles_unknown_token_type(self, mock_post):
        TwitterSetting.objects.create(name='consumer_key', value='myconsumer')
        TwitterSetting.objects.create(name='consumer_secret', value='mysecret')
        mock_response = MagicMock()
        mock_response.json.return_value = {'token_type': 'other'}
        mock_post.return_value = mock_response
        with self.assertRaises(CommandError) as exception_context:
            get_access_token()
        self.assertEqual(
            "{}".format(exception_context.exception),
            "unknown token_type other")

    def test_get_access_token_effect(self, mock_post):
        TwitterSetting.objects.create(name='consumer_key', value='myconsumer')
        TwitterSetting.objects.create(name='consumer_secret', value='mysecret')
        mock_response = MagicMock()
        mock_response.json.return_value = {'token_type': 'bearer', 'access_token': '4ll y0ur b4s3 4r3 b3l0ng t0 u5'}
        mock_post.return_value = mock_response
        access_token = get_access_token()
        self.assertEqual(access_token, '4ll y0ur b4s3 4r3 b3l0ng t0 u5')
        token_setting = TwitterSetting.objects.get(name='access_token')
        self.assertEqual(token_setting.value, '4ll y0ur b4s3 4r3 b3l0ng t0 u5')

    def test_get_access_token_returns_existing_token(self, mock_post):
        TwitterSetting.objects.create(name='access_token', value='4ll y0ur b4s3 4r3 b3l0ng t0 u5')
        access_token = get_access_token()
        self.assertEqual(access_token, '4ll y0ur b4s3 4r3 b3l0ng t0 u5')
        mock_post.assert_not_called()


class TestCreateMarkup(TestCase):
    def test_create_markup_returns_source_for_empty_entities(self):
        formatted = create_markup('A test tweet', {})
        self.assertEqual(formatted, 'A test tweet')

    def test_create_markup_replaces_hashtag(self):
        formatted = create_markup('A #test tweet', {'hashtags': [{'text': 'test'}]})
        self.assertEqual(formatted, 'A <a href="https://twitter.com/hashtag/test">#test</a> tweet')

    def test_create_markup_replaces_media(self):
        formatted = create_markup(
            'A tweet with http://twimg.example.org/img.jpg', {
                'media': [{'url': 'http://twimg.example.org/img.jpg',
                           'media_url_https': 'https://twimg.example.org/img_media.jpg'}]})
        self.assertEqual(
            formatted,
            'A tweet with <a href="https://twimg.example.org/img_media.jpg">http://twimg.example.org/img.jpg</a>')

    def test_create_markup_replaces_url(self):
        formatted = create_markup(
            'A tweet with https://www.example.org/', {'urls': [{'url': 'https://www.example.org/'}]})
        self.assertEqual(
            formatted,
            'A tweet with <a href="https://www.example.org/">https://www.example.org/</a>')

    def test_create_markup_replaces_at_mention(self):
        formatted = create_markup(
            'A tweet for @tester', {'user_mentions': [{'screen_name': 'tester'}]})
        self.assertEqual(
            formatted,
            'A tweet for <a href="https://twitter.com/tester">@tester</a>')


@override_settings(TWITTERFEED_PROXIES={})
class TestFetchTweetCommand(TestCase):
    def setUp(self):
        TwitterSetting.objects.create(name='access_token', value='4ll y0ur b4s3 4r3 b3l0ng t0 u5')

    def test_command_handles_missing_search_query(self):
        with self.assertRaises(CommandError) as exception_context:
            call_command('fetch_tweets', verbosity=0)
        self.assertEqual(
            "{}".format(exception_context.exception),
            "necessary twitter setting search_query does not exist. Use the admin site to set this setting")

    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_fetches_all_tweets_if_none_saved(self, mock_get):
        TwitterSetting.objects.create(name='search_query', value='#example OR TO:example')
        call_command('fetch_tweets', verbosity=0)
        mock_get.assert_called_with(
            'https://api.twitter.com/1.1/search/tweets.json',
            headers={'Authorization': 'Bearer 4ll y0ur b4s3 4r3 b3l0ng t0 u5'},
            params={'q': '#example OR TO:example', 'include_entities': 'true', 'count': 100},
            proxies={})

    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_fetches_after_last_tweet(self, mock_get):
        TwitterSetting.objects.create(name='search_query', value='#example OR TO:example')
        Tweet.objects.create(created_at=timezone.now(), twitter_id=815)
        call_command('fetch_tweets', verbosity=0)
        mock_get.assert_called_with(
            'https://api.twitter.com/1.1/search/tweets.json',
            headers={'Authorization': 'Bearer 4ll y0ur b4s3 4r3 b3l0ng t0 u5'},
            params={'q': '#example OR TO:example', 'include_entities': 'true', 'count': 100, 'since_id': 815},
            proxies={})

    @patch('django.core.management.sys.stderr')
    @patch('django.core.management.sys.stdout')
    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_verbose_output_no_tweets(self, mock_get, mock_stdout, mock_stderr):
        TwitterSetting.objects.create(name='search_query', value='#example OR TO:example')
        mock_response = MagicMock()
        mock_response.url = 'http://mock.example.org/'
        mock_get.return_value = mock_response
        call_command('fetch_tweets', verbosity=2)
        self.assertEqual(mock_stdout.write.call_count, 2)
        self.assertTupleEqual((
            call('no tweets yet, fetching tweets from one year in the past\n'),
            call('fetched from http://mock.example.org/\n')),
            tuple(mock_stdout.write.call_args_list))
        mock_stderr.write.assert_not_called()

    @patch('django.core.management.sys.stderr')
    @patch('django.core.management.sys.stdout')
    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_verbose_output_existing_tweet(self, mock_get, mock_stdout, mock_stderr):
        TwitterSetting.objects.create(name='search_query', value='#example OR TO:example')
        Tweet.objects.create(created_at=timezone.now(), twitter_id=815)
        mock_response = MagicMock()
        mock_response.url = 'http://mock.example.org/'
        mock_get.return_value = mock_response
        call_command('fetch_tweets', verbosity=2)
        self.assertEqual(mock_stdout.write.call_count, 2)
        self.assertTupleEqual((
            call('Fetching tweets since 815\n'),
            call('fetched from http://mock.example.org/\n')),
            tuple(mock_stdout.write.call_args_list))
        mock_stderr.write.assert_not_called()

    @patch('twitterfeed.management.commands.fetch_tweets.Command.handle_tweet')
    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_creates_tweet_in_db(self, mock_get, mock_handle_tweet):
        TwitterSetting.objects.create(name='search_query', value='#example OR TO:example')
        mock_response = MagicMock()
        mock_response.json.return_value = {'statuses': [{
            'fake_tweet': True
        }]}
        mock_get.return_value = mock_response
        call_command('fetch_tweets', verbosity=0)
        mock_handle_tweet.assert_called_with({'fake_tweet': True}, 0)


class TestFetchTweetCommandHandleTweet(TestCase):
    def setUp(self):
        self.mock_stdout = MagicMock()
        self.command = FetchTweetCommand(stdout=self.mock_stdout)
        self.mock_response = MagicMock()
        self.image_data = codecs.decode(
            b'/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////'
            b'////////////////////////////////////////////////////////2wBDAf//'
            b'////////////////////////////////////////////////////////////////'
            b'////////////////////wAARCAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAA'
            b'AAAAAAAAA//EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAA'
            b'AAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AQH//2Q==',
            'base64')
        self.mock_response.content = self.image_data
        self.mock_response.headers = {'Content-Type': 'text/jpeg'}

    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_handle_tweet_creates_profile_image_and_tweet(self, mock_get):
        mock_get.return_value = self.mock_response
        self.command.handle_tweet({
            'id': 815,
            'created_at': formatdate(),
            'text': 'A test tweet',
            'user': {
                'profile_image_url_https': 'https://www.example.org/test_normal.jpg',
                'name': 'Test Tweeter',
                'screen_name': 'tester',
            },
            'entities': {},
        }, 0)
        self.assertEqual(Tweet.objects.count(), 1)
        self.assertEqual(TwitterProfileImage.objects.count(), 1)
        mock_get.assert_called_with('https://www.example.org/test_bigger.jpg')

    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_handle_tweet_reuses_existing_profile_image(self, mock_get):
        profile_image = TwitterProfileImage.objects.create(
            user_profile_image_url='https://www.example.org/test_normal.jpg',
            image_data=SimpleUploadedFile(
                name='test_normal.jpg', content=self.image_data, content_type='image/jpeg'
            ))
        self.command.handle_tweet({
            'id': 815,
            'created_at': formatdate(),
            'text': 'A test tweet',
            'user': {
                'profile_image_url_https': 'https://www.example.org/test_normal.jpg',
                'name': 'Test Tweeter',
                'screen_name': 'tester',
            },
            'entities': {},
        }, 0)
        self.assertEqual(Tweet.objects.count(), 1)
        self.assertEqual(Tweet.objects.first().user_profile_image, profile_image)

    @patch('twitterfeed.management.commands.fetch_tweets.requests.get')
    def test_command_verbose_output_existing_tweet(self, mock_get):
        mock_get.return_value = self.mock_response
        self.command.handle_tweet({
            'id': 815,
            'created_at': formatdate(),
            'text': 'A test tweet',
            'user': {
                'profile_image_url_https': 'https://www.example.org/test_normal.jpg',
                'name': 'Test Tweeter',
                'screen_name': 'tester',
            },
            'entities': {},
        }, 2)
        self.assertEqual(self.mock_stdout.write.call_count, 1)
        self.mock_stdout.write.assert_called_with('add profile with url https://www.example.org/test_normal.jpg\n')
