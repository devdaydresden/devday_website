from django.apps import AppConfig, apps
from django.test import SimpleTestCase
from django.utils.translation import ugettext as _


class AppConfigTest(SimpleTestCase):
    def test_app_config(self):
        config = apps.get_app_config('attendee')
        self.assertIsInstance(config, AppConfig)
        self.assertEqual(config.verbose_name, _('Attendee management'))
