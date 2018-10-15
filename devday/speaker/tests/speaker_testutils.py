from speaker.models import Speaker

from attendee.tests import attendee_testutils


def create_test_speaker(
        email='speaker@example.org', name='Test Speaker', **kwargs):
    user, password = attendee_testutils.create_test_user(email)
    speaker = Speaker.objects.create(
        user=user, name=name, video_permission=True, shirt_size=1,
        **kwargs)
    return speaker, user, password
