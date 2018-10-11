from django.test import TestCase

from event.contextprocessors import current_event_contextprocessor

from .testutils import unpublish_all_events


class TestCurrentEventContextProcessor(TestCase):
    def test_current_event_in_context(self):
        context = current_event_contextprocessor(None)
        self.assertIn('current_event', context)

    def test_current_event_not_in_context(self):
        unpublish_all_events()
        context = current_event_contextprocessor(None)
        self.assertIsNone(context)

    def test_talk_submission_open_in_context(self):
        context = current_event_contextprocessor(None)
        self.assertIn('talk_submission_open', context)

    def test_attendee_registration_in_context(self):
        context = current_event_contextprocessor(None)
        self.assertIn('attendee_registration_open', context)
