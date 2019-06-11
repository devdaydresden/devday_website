from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from attendee.models import Attendee
from devday.utils.devdata import DevData
from event.models import Event
from event.tests import event_testutils

from .event_testutils import unpublish_all_events

User = get_user_model()


class EventManagerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()

    def test_event(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Event.objects.create(title="foo")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Event.objects.create(title="foo", start_time=timezone.now())
        with transaction.atomic():
            event = Event.objects.create(
                title="foo", start_time=timezone.now(), end_time=timezone.now()
            )
        self.assertIsNotNone(event)

    def test_registration_count(self):
        event = Event.objects.current_event()
        for i in range(10):
            user = User.objects.create_user(
                email="user{}@exanple.com".format(i), password="foo"
            )
            Attendee.objects.create(user=user, event=event)
        self.assertEquals(event.registration_count(), 10, "should have 10 attendees")

    def test_absolute_url(self):
        self.assertEquals(
            Event.objects.current_event().get_absolute_url(),
            "/devdata19/sessions/",
            "should have the right URI",
        )

    def test_current_event(self):
        event = Event.objects.current_event()
        event.registration_open = True
        event.submission_open = True
        self.assertIsNotNone(event)
        self.assertEquals(event.id, Event.objects.current_event_id())
        self.assertTrue(Event.objects.current_submission_open())
        self.assertTrue(Event.objects.current_registration_open())

    def test_current_event_none(self):
        unpublish_all_events()
        event = Event.objects.current_event()
        self.assertIsNone(event)
        self.assertIsNone(Event.objects.current_event_id())
        self.assertFalse(Event.objects.current_submission_open())
        self.assertFalse(Event.objects.current_registration_open())

    def test_feedback_open_for_running_event(self):
        event = event_testutils.create_test_event(
            "Test event", start_time=timezone.now() - timedelta(hours=1), published=True
        )
        self.assertTrue(event.feedback_open)

    def test_feedback_not_open_for_future_event(self):
        event = event_testutils.create_test_event(
            "Test event", start_time=timezone.now() + timedelta(hours=1), published=True
        )
        self.assertFalse(event.feedback_open)

    def test_feedback_not_open_for_unpublished_event(self):
        event = event_testutils.create_test_event(
            "Test event",
            start_time=timezone.now() - timedelta(hours=1),
            published=False,
        )
        self.assertFalse(event.feedback_open)


class EventTest(TestCase):
    def test_without_slug(self):
        event = Event(
            title="Test",
            description="Test Event",
            start_time=timezone.now(),
            end_time=timezone.now(),
        )
        event.save()
        self.assertEqual(event.slug, "test")

    def test_with_slug(self):
        event = Event(
            title="Test",
            description="Test Event",
            start_time=timezone.now(),
            end_time=timezone.now(),
            slug="other",
        )
        event.save()
        self.assertEqual(event.slug, "other")

    def test_is_started(self):
        now = timezone.now()
        event = Event(
            title="Test",
            description="Test Event",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )
        self.assertTrue(event.is_started())

    def test_is_running(self):
        now = timezone.now()
        event = Event(
            title="Test running",
            description="Test Event running",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )
        self.assertTrue(event.is_running())
        event = Event(
            title="Test future",
            description="Test Event not running yet",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2)
        )
        self.assertFalse(event.is_running())
        event = Event(
            title="Test past",
            description="Test Event not running anymore",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1)
        )
        self.assertFalse(event.is_running())

    def test_has_ended(self):
        now = timezone.now()
        event = Event(
            title="Test running",
            description="Test Event running",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1)
        )
        self.assertFalse(event.has_ended())
        event = Event(
            title="Test future",
            description="Test Event in the future",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2)
        )
        self.assertFalse(event.has_ended())
        event = Event(
            title="Test past",
            description="Test Event that has ended",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
        )
        self.assertTrue(event.has_ended())