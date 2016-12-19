from django.test import SimpleTestCase

from devday.contextprocessors import devdaysettings_contextprocessor


class TestDevDaySettingsContextProcessor(SimpleTestCase):
    def test_twitter_url_in_context(self):
        context = devdaysettings_contextprocessor(None)
        self.assertIn('twitter_url', context)
