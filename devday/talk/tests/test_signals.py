from django.core import mail
from django.test import RequestFactory, TestCase

from attendee.models import Attendee
from attendee.signals import attendence_cancelled
from attendee.tests import attendee_testutils
from event.models import Event
from speaker.tests import speaker_testutils
from talk.models import SessionReservation, Talk, Track
from talk.signals import (
    send_reservation_confirmation_mail,
    session_reservation_cancelled,
)


class SendReservationConfirmationMailTest(TestCase):
    def setUp(self):
        self.event = Event.objects.current_event()

        speaker, _, _ = speaker_testutils.create_test_speaker()
        self.talk = Talk.objects.create(
            event=self.event, title="Test talk", draft_speaker=speaker, spots=2
        )
        track = Track.objects.create(event=self.event, name="Test track")
        self.talk.publish(track)
        user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=user, event=self.event)

    def test_send_reservation_confirmation_mail(self):
        self.client.request()
        request = RequestFactory().request()
        request.user = self.attendee.user
        reservation = SessionReservation.objects.create(
            talk=self.talk, attendee=self.attendee, is_confirmed=False, is_waiting=False
        )

        send_reservation_confirmation_mail(request, reservation, self.attendee.user)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.attendee.user.email, mail.outbox[0].recipients())
        self.assertEqual(len(mail.outbox[0].recipients()), 1)

    def test_send_confirmation_mails_to_pending_reservations(self):
        request = RequestFactory().request()
        request.user = self.attendee.user
        reservation = SessionReservation.objects.create(
            talk=self.talk, attendee=self.attendee, is_confirmed=False, is_waiting=False
        )
        session_reservation_cancelled.send(
            self.__class__, reservation=reservation, request=request
        )
        # no mails sent if there are no pending reservations
        self.assertEqual(len(mail.outbox), 0)

        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        attendee2 = Attendee.objects.create(user=user2, event=self.event)
        reservation = SessionReservation.objects.create(
            talk=self.talk, attendee=attendee2, is_confirmed=False, is_waiting=True
        )
        session_reservation_cancelled.send(
            self.__class__, reservation=reservation, request=request
        )
        # mails sent to waiting attendee
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(attendee2.user.email, mail.outbox[0].recipients())
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        reservation.refresh_from_db()
        self.assertFalse(reservation.is_waiting)

    def test_send_confirmation_mails_to_remaining_attendees(self):
        request = RequestFactory().request()
        request.user = self.attendee.user
        SessionReservation.objects.create(
            talk=self.talk, attendee=self.attendee, is_confirmed=False, is_waiting=False
        )
        speaker, _, _ = speaker_testutils.create_test_speaker(
            email="testspeaker2@example.org", name="Test Speaker 2"
        )
        talk2 = Talk.objects.create(
            event=self.event, title="Test talk 2", draft_speaker=speaker, spots=2
        )
        track = Track.objects.create(event=self.event, name="Test track 2")
        self.talk.publish(track)
        SessionReservation.objects.create(
            talk=talk2, attendee=self.attendee, is_confirmed=False, is_waiting=False
        )

        attendence_cancelled.send(
            self.__class__, attendee=self.attendee, request=request
        )
        # no mails sent if there are no pending reservations
        self.assertEqual(len(mail.outbox), 0)

        # register 2nd attendee with waiting reservations for both talks
        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        attendee2 = Attendee.objects.create(user=user2, event=self.event)
        reservation = SessionReservation.objects.create(
            talk=self.talk, attendee=attendee2, is_confirmed=False, is_waiting=True
        )
        reservation2 = SessionReservation.objects.create(
            talk=talk2, attendee=attendee2, is_confirmed=False, is_waiting=True
        )

        user3, _ = attendee_testutils.create_test_user("test3@example.org")
        attendee3 = Attendee.objects.create(user=user3, event=self.event)
        reservation3 = SessionReservation.objects.create(
            talk=talk2, attendee=attendee3, is_confirmed=False, is_waiting=True
        )

        attendence_cancelled.send(
            self.__class__, attendee=self.attendee, request=request
        )

        # mails sent to waiting attendee
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(attendee2.user.email, mail.outbox[0].recipients())
        self.assertEqual(len(mail.outbox[0].recipients()), 1)
        self.assertIn(attendee2.user.email, mail.outbox[1].recipients())
        self.assertEqual(len(mail.outbox[1].recipients()), 1)
        reservation.refresh_from_db()
        self.assertFalse(reservation.is_waiting)
        reservation2.refresh_from_db()
        self.assertFalse(reservation2.is_waiting)
        reservation3.refresh_from_db()
        self.assertTrue(reservation3.is_waiting)
