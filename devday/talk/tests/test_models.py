from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from event.tests.event_testutils import create_test_event
from speaker.models import PublishedSpeaker, Speaker
from speaker.tests import speaker_testutils
from talk.models import (
    AttendeeFeedback,
    AttendeeVote,
    Room,
    SessionReservation,
    Talk,
    TalkComment,
    TalkDraftSpeaker,
    TalkSlot,
    TimeSlot,
    Track,
    Vote,
    TalkPublishedSpeaker,
)

User = get_user_model()


class TalkTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.org")
        self.event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=self.user, video_permission=True, shirt_size=1
        )

    def test_str_draft_speaker(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        self.assertEqual("{}".format(talk), "{} - {}".format(self.speaker, "Test"))

    def test_str_multiple_draft_speakers(self):
        speaker1, _, _ = speaker_testutils.create_test_speaker(
            "speaker1@example.org", "Test Speaker 1"
        )
        talk = Talk.objects.create(
            draft_speaker=speaker1,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        speaker2, _, _ = speaker_testutils.create_test_speaker(
            "speaker2@example.org", "Test Speaker 2"
        )
        TalkDraftSpeaker.objects.create(talk=talk, draft_speaker=speaker2, order=2)
        self.assertEqual(
            "{}".format(talk), "{}, {} - {}".format(speaker1, speaker2, "Test")
        )

    def test_str_published_speaker(self):
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            self.speaker, self.event
        )
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        TalkPublishedSpeaker.objects.create(
            talk=talk, published_speaker=published_speaker, order=1
        )
        self.assertEqual("{}".format(talk), "{} - {}".format(published_speaker, "Test"))

    def test_str_multiple_published_speakers(self):
        speaker1, _, _ = speaker_testutils.create_test_speaker(
            "speaker1@example.org", "Test Speaker 1"
        )
        talk = Talk.objects.create(
            draft_speaker=speaker1,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        speaker2, _, _ = speaker_testutils.create_test_speaker(
            "speaker2@example.org", "Test Speaker 2"
        )
        TalkDraftSpeaker.objects.create(talk=talk, draft_speaker=speaker2, order=2)
        published_speaker1 = PublishedSpeaker.objects.copy_from_speaker(
            speaker1, self.event
        )
        published_speaker2 = PublishedSpeaker.objects.copy_from_speaker(
            speaker2, self.event
        )
        TalkPublishedSpeaker.objects.create(
            talk=talk, published_speaker=published_speaker1, order=2
        )
        TalkPublishedSpeaker.objects.create(
            talk=talk, published_speaker=published_speaker2, order=1
        )
        self.assertEqual(
            "{}".format(talk),
            "{}, {} - {}".format(published_speaker2, published_speaker1, "Test"),
        )

    def test_str_published_speaker_after_user_deletion(self):
        published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            self.speaker, self.event
        )
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=self.event,
        )
        TalkPublishedSpeaker.objects.create(
            talk=talk, published_speaker=published_speaker, order=1
        )
        self.user.delete()
        with self.assertRaises(ObjectDoesNotExist):
            self.speaker.refresh_from_db()
        published_speaker.refresh_from_db()
        talk.refresh_from_db()
        self.assertFalse(talk.draft_speakers.exists())
        self.assertEqual("{}".format(talk), "{} - {}".format(published_speaker, "Test"))

    def test_publish(self):
        track = Track.objects.create(name="Test track", event=self.event)
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        talk.publish(track)
        published_speaker = PublishedSpeaker.objects.get(
            speaker=self.speaker, event=self.event
        )
        self.assertIsInstance(published_speaker, PublishedSpeaker)
        self.assertEqual(talk.published_speakers.count(), 1)
        self.assertEqual(talk.published_speakers.all()[0], published_speaker)
        self.assertEqual(talk.track, track)

    def test_is_limited_default(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        self.assertFalse(talk.is_limited)

    def test_is_limited_with_spots(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
            spots=10,
        )
        self.assertTrue(talk.is_limited)

    def test_is_feedback_allowed_unpublished(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        self.assertFalse(talk.is_feedback_allowed)

    def test_is_feedback_allowed_no_talkslot(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        track = Track.objects.create(name="Test track", event=self.event)
        talk.publish(track)
        self.assertFalse(talk.is_feedback_allowed)

    @override_settings(TALK_FEEDBACK_ALLOWED_MINUTES=30)
    def test_is_feedback_allowed_future_talk(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        track = Track.objects.create(name="Test track", event=self.event)
        talk.publish(track)
        now = timezone.now()
        time_slot = TimeSlot.objects.create(
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            event=self.event,
        )
        room = Room.objects.create(name="Test room", event=self.event)
        TalkSlot.objects.create(talk=talk, room=room, time=time_slot)
        talk.refresh_from_db()
        self.assertFalse(talk.is_feedback_allowed)

    @override_settings(TALK_FEEDBACK_ALLOWED_MINUTES=30)
    def test_is_feedback_allowed_current_talk(self):
        talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            event=self.event,
        )
        track = Track.objects.create(name="Test track", event=self.event)
        talk.publish(track)
        now = timezone.now()
        time_slot = TimeSlot.objects.create(
            start_time=now + timedelta(minutes=-31),
            end_time=now + timedelta(minutes=29),
            event=self.event,
        )
        room = Room.objects.create(name="Test room", event=self.event)
        TalkSlot.objects.create(talk=talk, room=room, time=time_slot)
        talk.refresh_from_db()
        self.assertTrue(talk.is_feedback_allowed)


class VoteTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="speaker@example.org")
        event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=user, video_permission=True, shirt_size=1
        )
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=event,
        )
        self.voter = User.objects.create_user(email="voter@example.org")

    def test_str(self):
        vote = Vote.objects.create(voter=self.voter, talk=self.talk, score=5)
        self.assertEqual(
            "{}".format(vote),
            "{} voted {} for {} by {}".format(self.voter, 5, "Test", self.speaker),
        )


class TalkCommentTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="speaker@example.org")
        event = create_test_event()
        self.speaker = Speaker.objects.create(
            user=user, video_permission=True, shirt_size=1
        )
        self.talk = Talk.objects.create(
            draft_speaker=self.speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=event,
        )
        self.commenter = User.objects.create_user(email="voter@example.org")

    def test_str(self):
        talk_comment = TalkComment.objects.create(
            commenter=self.commenter, talk=self.talk, comment="A Test comment"
        )
        self.assertEqual(
            "{}".format(talk_comment),
            "{} commented {} for {} by {}".format(
                self.commenter, "A Test comment", "Test", self.speaker
            ),
        )


class TalkSlotTest(TestCase):
    def test___str__(self):
        event = create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(
            draft_speaker=speaker, title="Test", abstract="Test abstract", event=event
        )
        room = Room.objects.create(name="Test Room", event=event)
        time_slot = TimeSlot.objects.create(name="Morning", event=event)
        talk_slot = TalkSlot.objects.create(room=room, time=time_slot, talk=talk)
        self.assertEqual(
            str(talk_slot), "{} {} ({})".format(room, time_slot.name, event)
        )


class AttendeeVoteTest(TestCase):
    def setUp(self):
        event = create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=event,
        )
        self.test_user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=self.test_user, event=event)

    def test_str(self):
        vote = AttendeeVote.objects.create(
            attendee=self.attendee, talk=self.talk, score=5
        )
        self.assertEqual(
            "{}".format(vote),
            "{} voted {} for {} by {}".format(
                self.attendee,
                5,
                "Test",
                ", ".join(
                    [
                        str(published_speaker)
                        for published_speaker in self.talk.published_speakers.all()
                    ]
                ),
            ),
        )


class AttendeeFeedbackTest(TestCase):
    def setUp(self):
        event = create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=event,
        )
        track = Track.objects.create(name="Test")
        self.talk.publish(track=track)
        self.test_user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=self.test_user, event=event)

    def test_str(self):
        vote = AttendeeFeedback.objects.create(
            attendee=self.attendee, talk=self.talk, score=5, comment="LGTM"
        )
        self.assertEqual(
            "{}".format(vote),
            "{} gave feedback for {} by {}: score={}, comment={}".format(
                self.attendee,
                "Test",
                ", ".join(
                    [
                        str(published_speaker)
                        for published_speaker in self.talk.published_speakers.all()
                    ]
                ),
                5,
                "LGTM",
            ),
        )


class SessionReservationTest(TestCase):
    def setUp(self):
        event = create_test_event()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = Talk.objects.create(
            draft_speaker=speaker,
            title="Test",
            abstract="Test abstract",
            remarks="Test remarks",
            event=event,
        )
        track = Track.objects.create(name="Test")
        talk.publish(track=track)
        user, _ = attendee_testutils.create_test_user()
        attendee = Attendee.objects.create(user=user, event=event)
        self.reservation = SessionReservation.objects.create(
            talk=talk, attendee=attendee
        )

    @override_settings(
        CONFIRMATION_SALT="test_salt_confirmation", TALK_RESERVATION_CONFIRMATION_DAYS=5
    )
    def test_get_confirmation_key(self):
        confirmation_key = self.reservation.get_confirmation_key()
        self.assertEqual(
            signing.loads(
                confirmation_key,
                salt=settings.CONFIRMATION_SALT,
                max_age=settings.TALK_RESERVATION_CONFIRMATION_DAYS * 86400,
            ).split(":"),
            [
                self.reservation.attendee.user.get_username(),
                str(self.reservation.talk_id),
            ],
        )
