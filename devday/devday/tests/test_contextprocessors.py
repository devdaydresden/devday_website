from django.test import SimpleTestCase

from devday.contextprocessors import devdaysettings_contextprocessor


class TestDevDaySettingsContextProcessor(SimpleTestCase):
    def test_twitter_url_in_context(self):
        context = devdaysettings_contextprocessor(None)
        self.assertIn('twitter_url', context)

    def test_xing_url_in_context(self):
        context = devdaysettings_contextprocessor(None)
        self.assertIn('xing_url', context)

    def test_facebook_url_in_context(self):
        context = devdaysettings_contextprocessor(None)
        self.assertIn('facebook_url', context)

    def test_talk_submission_open_in_context(self):
        context = devdaysettings_contextprocessor(None)
        self.assertIn('talk_submission_open', context)
