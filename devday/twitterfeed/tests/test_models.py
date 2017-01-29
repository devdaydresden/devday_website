from django.test import TestCase

from twitterfeed.models import Tweet, TwitterSetting, TwitterProfileImage


class TestTwitterSetting(TestCase):
    def test_str(self):
        twitter_setting = TwitterSetting(name=u'test')
        self.assertEqual(u"{}".format(twitter_setting), u"test")


class TestTwitterProfileImage(TestCase):
    def test_str(self):
        twitter_profile_image = TwitterProfileImage(user_profile_image_url=u'http://test.example.org/userimage.jpg')
        self.assertEqual(u"{}".format(twitter_profile_image), u'http://test.example.org/userimage.jpg')


class TestTweet(TestCase):
    def test_str(self):
        tweet = Tweet(plain_text=u'Test data', user_screen_name=u'Tester')
        self.assertEqual(u"{}".format(tweet), u"Test data by Tester")
