from __future__ import unicode_literals

from django.test import TestCase


class TestExceptionTestView(TestCase):
    def test_raises_500_error(self):
        self.assertRaises(Exception, self.client.get, u'/synthetic_server_error/')
