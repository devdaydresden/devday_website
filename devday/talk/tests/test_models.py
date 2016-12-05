from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from attendee.models import Attendee
from talk.models import Speaker, Talk

User = get_user_model()


class SpeakerTest(TransactionTestCase):
    def setUp(self):
        user = User.objects.create_user(email='test@example.org')
        self.attendee = Attendee.objects.create(user=user)

    def test_str(self):
        speaker = Speaker.objects.create(
            user=self.attendee, videopermission=True, shirt_size=1)
        self.assertEqual("{}".format(speaker), "{}".format(self.attendee))


class TalkTest(TransactionTestCase):
    def setUp(self):
        user = User.objects.create_user(email='test@example.org')
        attendee = Attendee.objects.create(user=user)
        self.speaker = Speaker.objects.create(
            user=attendee, videopermission=True, shirt_size=1)

    def test_str(self):
        talk = Talk.objects.create(
            speaker=self.speaker, title='Test', abstract='Test abstract',
            remarks='Test remarks',
        )
        self.assertEqual('{}'.format(talk), '{} - {}'.format(self.speaker, 'Test'))
