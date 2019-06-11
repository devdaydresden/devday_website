from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from attendee.models import Attendee
from attendee.tests import attendee_testutils
from event.models import Event
from event.tests import event_testutils
from speaker.tests import speaker_testutils
from talk import COMMITTEE_GROUP
from talk.models import Track
from talk.tests import talk_testutils

User = get_user_model()


class TestCommitteeMemberContextProcessor(TestCase):
    def test_is_committee_member_is_false_for_anonymous(self):
        response = self.client.get("/")
        self.assertFalse(response.context["is_committee_member"])

    def test_is_committee_member_is_false_for_attendee(self):
        user, password = attendee_testutils.create_test_user()
        event = event_testutils.create_test_event()
        Attendee.objects.create(user=user, event=event)
        self.client.login(username=user.email, password=password)
        response = self.client.get("/")
        self.assertFalse(response.context["is_committee_member"])

    def test_is_committee_member_is_false_for_speaker(self):
        speaker, user, password = speaker_testutils.create_test_speaker()
        self.client.login(username=user.email, password=password)
        response = self.client.get("/")
        self.assertFalse(response.context["is_committee_member"])

    def test_is_committee_member_is_true_for_committee_member(self):
        user, password = attendee_testutils.create_test_user()
        user.groups.add(Group.objects.get(name=COMMITTEE_GROUP))
        self.client.login(username=user.email, password=password)
        response = self.client.get("/")
        self.assertTrue(response.context["is_committee_member"])


class TestReservationContextProcessor(TestCase):
    def setUp(self) -> None:
        self.event = Event.objects.current_event()

    def test_reservable_sessions_false_for_event_with_no_published_sessions(self):
        self.event.sessions_published = False
        self.event.save()
        response = self.client.get("/")
        self.assertFalse(response.context["reservable_sessions"])

    def test_reservable_sessions_false_if_no_talks_with_spots(self):
        self.event.sessions_published = True
        self.event.save()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = talk_testutils.create_test_talk(
            speaker=speaker, event=self.event, title="Test talk", spots=0
        )
        track = Track.objects.create(name="Test track")
        talk.publish(track)
        response = self.client.get("/")
        self.assertFalse(response.context["reservable_sessions"])

    def test_reservable_sessions_true_if_talks_with_spots(self):
        self.event.sessions_published = True
        self.event.start_time = timezone.now() + timedelta(hours=1)
        self.event.end_time = timezone.now() + timedelta(hours=2)
        self.event.save()
        speaker, _, _ = speaker_testutils.create_test_speaker()
        talk = talk_testutils.create_test_talk(
            speaker=speaker, event=self.event, title="Test talk", spots=10
        )
        track = Track.objects.create(name="Test track")
        talk.publish(track)
        response = self.client.get("/")
        self.assertTrue(response.context["reservable_sessions"])
