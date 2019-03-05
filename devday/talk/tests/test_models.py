from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import TestCase
from django.utils.translation import ugettext as _

from event.tests.event_testutils import create_test_event
from speaker.models import PublishedSpeaker, Speaker
from speaker.tests import speaker_testutils
from talk.models import Room, Talk, TalkComment, TalkSlot, TimeSlot, Track, Vote

User = get_user_model()


class TalkTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.org')
        self.event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=self.user, video_permission=True, shirt_size=1)

    def test_str_draft_speaker(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Test', abstract='Test abstract',
            remarks='Test remarks', event=self.event
        )
        self.assertEqual('{}'.format(talk), '{} - {}'.format(
            self.speaker, 'Test'))

    def test_str_published_speaker(self):
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            self.speaker, self.event)
        talk = Talk.objects.create(
            draft_speaker=self.speaker, published_speaker=published_speaker,
            title='Test', abstract='Test abstract',
            remarks='Test remarks', event=self.event
        )
        self.assertEqual('{}'.format(talk), '{} - {}'.format(
            published_speaker, 'Test'))

    def test_str_published_speaker_after_user_deletion(self):
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            self.speaker, self.event)
        talk = Talk.objects.create(
            draft_speaker=self.speaker, published_speaker=published_speaker,
            title='Test', abstract='Test abstract',
            remarks='Test remarks', event=self.event
        )
        self.user.delete()
        with self.assertRaises(ObjectDoesNotExist):
            self.speaker.refresh_from_db()
        published_speaker.refresh_from_db()
        talk.refresh_from_db()
        self.assertIsNone(talk.draft_speaker_id)
        self.assertEqual('{}'.format(talk), '{} - {}'.format(
            published_speaker, 'Test'))

    def test_publish(self):
        track = Track.objects.create(name='Test track', event=self.event)
        talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Test', abstract='Test abstract',
            event=self.event)
        talk.publish(track)
        published_speaker = PublishedSpeaker.objects.get(
            speaker=self.speaker, event=self.event)
        self.assertIsInstance(published_speaker, PublishedSpeaker)
        self.assertEqual(talk.published_speaker, published_speaker)
        self.assertEqual(talk.track, track)

    def test_clean(self):
        talk = Talk.objects.create(
            title='Test', abstract='Test abstract', event=self.event)
        with self.assertRaisesMessage(
                ValidationError,
                _('A draft speaker or a published speaker is required.')):
            talk.clean()

    def test_is_limited_default(self):
        talk = Talk.objects.create(
            title='Test', abstract='Test abstract', event=self.event)
        self.assertFalse(talk.is_limited)

    def test_is_limited_with_spots(self):
        talk = Talk.objects.create(
            title='Test', abstract='Test abstract', event=self.event,
            spots=10)
        self.assertTrue(talk.is_limited)


class VoteTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email='speaker@example.org')
        event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=user, video_permission=True, shirt_size=1)
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Test', abstract='Test abstract',
            remarks='Test remarks', event=event)
        self.voter = User.objects.create_user(email='voter@example.org')

    def test_str(self):
        vote = Vote.objects.create(voter=self.voter, talk=self.talk, score=5)
        self.assertEqual(
            '{}'.format(vote),
            '{} voted {} for {} by {}'.format(
                self.voter, 5, 'Test', self.speaker))


class TalkCommentTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email='speaker@example.org')
        event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=user, video_permission=True, shirt_size=1)
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker, title='Test', abstract='Test abstract',
            remarks='Test remarks', event=event)
        self.commenter = User.objects.create_user(email='voter@example.org')

    def test_str(self):
        talk_comment = TalkComment.objects.create(
            commenter=self.commenter, talk=self.talk,
            comment='A Test comment')
        self.assertEqual(
            "{}".format(talk_comment),
            "{} commented {} for {} by {}".format(
                self.commenter, 'A Test comment', 'Test', self.speaker))


class TalkSlotTest(TestCase):
    def test___str__(self):
        event = create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(
            draft_speaker=speaker, title='Test', abstract='Test abstract',
            event=event)
        room = Room.objects.create(name='Test Room', event=event)
        time_slot = TimeSlot.objects.create(name='Morning', event=event)
        talk_slot = TalkSlot.objects.create(
            room=room, time=time_slot, talk=talk)
        self.assertEqual(
            str(talk_slot), '{} {} ({})'.format(room, time_slot.name, event))
