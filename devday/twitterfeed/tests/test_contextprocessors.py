from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings

from twitterfeed.contextprocessors import twitter_feed_context_processor


class TwitterFeedContextProcessorTest(TestCase):
    def test_no_twitter_feed_for_arbitrary_url(self):
        request = RequestFactory().get(u'/dummy')
        result = twitter_feed_context_processor(request)
        self.assertDictEqual({}, result)

    @override_settings(TWITTERFEED_PATHS=['/twitter', '/'])
    def test_twitter_feed_for_defined_url(self):
        request = RequestFactory().get(u'/twitter')
        result = twitter_feed_context_processor(request)
        self.assertIn('twitter_feed', result)
