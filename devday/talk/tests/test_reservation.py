from unittest import mock

from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.test import TestCase, override_settings

from talk.reservation import get_reservation_email_context


class ReservationEmailContextTest(TestCase):
    @override_settings(
        SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"),
        TALK_RESERVATION_CONFIRMATION_DAYS=3,
    )
    def test_get_reservation_email_context(self):
        reservation = mock.Mock()
        reservation.attendee = mock.Mock()
        reservation.attendee.user = "fakeuser"
        reservation.talk = mock.Mock("talk")
        reservation.talk.event = "Test event"
        request = HttpRequest()
        request.META["HTTP_X_FORWARDED_PROTO"] = "https"
        data = get_reservation_email_context(reservation, request, "test-key")
        self.assertIsNotNone(data)
        self.assertIn("scheme", data)
        self.assertEqual(data["scheme"], "https")
        self.assertIn("confirmation_key", data)
        self.assertEqual(data["confirmation_key"], "test-key")
        self.assertIn("expiration_days", data)
        self.assertEqual(data["expiration_days"], 3)
        self.assertIn("site", data)
        self.assertEqual(data["site"], Site.objects.get_current())
        self.assertIn("talk", data)
        self.assertEqual(data["talk"], reservation.talk)
        self.assertIn("event", data)
        self.assertEqual(data["event"], "Test event")
        self.assertIn("user", data)
        self.assertEqual(data["user"], "fakeuser")
