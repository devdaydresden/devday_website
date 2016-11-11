from django.apps import AppConfig, apps
from django.test import SimpleTestCase


class appconfig_test(SimpleTestCase):
    def test_appconfig(self):
        config = apps.get_app_config('attendee')
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.verbose_name, 'Attendee management')
