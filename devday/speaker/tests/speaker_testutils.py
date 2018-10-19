import shutil
import tempfile

from django.conf import settings
from django.test import override_settings, TestCase

from attendee.tests import attendee_testutils
from speaker.models import Speaker


def create_test_speaker(
        email='speaker@example.org', name='Test Speaker', **kwargs):
    user, password = attendee_testutils.create_test_user(email)
    speaker = Speaker.objects.create(
        user=user, name=name, video_permission=True, shirt_size=1,
        **kwargs)
    return speaker, user, password


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TemporaryMediaTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
