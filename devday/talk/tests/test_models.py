from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from event.tests.event_testutils import create_test_event
from speaker.models import Speaker, PublishedSpeaker
from talk.models import Talk, Vote, TalkComment

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
