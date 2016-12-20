from django.apps import AppConfig
from django.apps import apps
from django.test import SimpleTestCase


class AppConfigTest(SimpleTestCase):
    def test_app_config(self):
        config = apps.get_app_config('talk')
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.verbose_name, 'Talk')
