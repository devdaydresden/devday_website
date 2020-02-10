from base64 import urlsafe_b64decode, urlsafe_b64encode
from hashlib import sha1

import luhn

from django.conf import settings
from django.core import mail
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import ugettext as _

from attendee.models import Attendee, AttendeeEventFeedback, BadgeData, DevDayUser
from attendee.tests import attendee_testutils
from event.models import Event
from event.tests import event_testutils
from event.tests.event_testutils import create_test_event

ADMIN_EMAIL = "admin@example.org"
ADMIN_PASSWORD = "sUp3rS3cr3t"
USER_EMAIL = "test@example.org"
USER_PASSWORD = "s3cr3t"


class DevDayUserManagerTest(TestCase):
    """
    Tests for attendee.models.DevDayUserManager.
    """

    def test_manager_create_user(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(USER_PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_manager_create_superuser(self):
        user = DevDayUser.objects.create_superuser(ADMIN_EMAIL, ADMIN_PASSWORD)
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(ADMIN_PASSWORD))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_manager_enforce_email(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_user(None)
        self.assertEqual(str(error_context.exception), "The given email must be set")
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_user("")
        self.assertEqual(str(error_context.exception), "The given email must be set")
        user = DevDayUser.objects.create_user("noemail")
        self.assertEqual(user.get_username(), "noemail")

    def test_manager_create_superuser_force_staff(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_superuser(
                ADMIN_EMAIL, ADMIN_PASSWORD, is_staff=False
            )
        self.assertEqual(
            str(error_context.exception), "Superuser must have is_staff=True."
        )

    def test_manager_create_superuser_force_superuser(self):
        with self.assertRaises(ValueError) as error_context:
            DevDayUser.objects.create_superuser(
                ADMIN_EMAIL, ADMIN_PASSWORD, is_superuser=False
            )
        self.assertEqual(
            str(error_context.exception), "Superuser must have is_superuser=True."
        )


class DevDayUserTest(TestCase):
    """
    Tests for attendee.models.DevDayUser.

    """

    def test_get_full_name(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(user.get_full_name(), USER_EMAIL)

    def test_get_short_name(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(user.get_short_name(), USER_EMAIL)

    def test_email_user(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        user.email_user("Test mail", "Test mail body")
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(USER_EMAIL, email.recipients())
        self.assertEqual(email.subject, "Test mail")
        self.assertEqual(email.body, "Test mail body")

    def test_get_attendee(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        event = event_testutils.create_test_event("Test Event")
        attendee = Attendee.objects.create(user=user, event=event)
        self.assertEqual(user.get_attendee(event), attendee)

    def test_derive_title(self):
        user = DevDayUser.objects.create_user("tester@example.org", USER_PASSWORD)
        event = event_testutils.create_test_event("Test Event")
        attendee = Attendee.objects.create(user=user, event=event)
        self.assertEqual("Tester", attendee.derive_title())

    def test___str__(self):
        user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)
        self.assertEqual(str(user), USER_EMAIL)


class AttendeeTest(TestCase):
    """
    Tests for attendee.models.Attendee.
    """

    @classmethod
    def setUpTestData(cls):
        cls.event = event_testutils.create_test_event()
        cls.user = DevDayUser.objects.create_user(USER_EMAIL, USER_PASSWORD)

    def test___str__(self):
        attendee = Attendee.objects.create(user=self.user, event=self.event)
        self.assertEqual(
            str(attendee), _("{} at {}").format(self.user.email, self.event.title)
        )

    def test_checkin_code(self):
        attendee = Attendee.objects.create(user=self.user, event=self.event)
        self.assertEqual(str(attendee.user), USER_EMAIL)
        self.assertTrue(len(attendee.checkin_code) > 0, "has a checkin-code")
        self.assertTrue(luhn.verify(attendee.checkin_code), "checkin-code is valid")
        self.assertIsNone(attendee.checked_in, "is not checked in")

        u2 = DevDayUser.objects.create_user("another@example.com", "foo")
        a2 = Attendee.objects.create(user=u2, event=self.event)
        self.assertNotEqual(attendee.checkin_code, a2.checkin_code)
        a3 = Attendee.objects.get_by_checkin_code_or_email(
            attendee.checkin_code, self.event
        )
        self.assertEqual(attendee, a3)

        attendee.check_in()
        self.assertIsNotNone(attendee.checked_in)
        with self.assertRaises(IntegrityError):
            attendee.check_in()

    def test_get_verification(self):
        attendee = Attendee.objects.create(user=self.user, event=self.event)
        verification = attendee.get_verification()
        self.assertIsNotNone(verification)
        self.assertIsNotNone(urlsafe_b64decode(verification.encode("utf-8")))

    def test_get_checkin_url(self):
        attendee = Attendee.objects.create(user=self.user, event=self.event)
        checkin_url = attendee.get_checkin_url(event=self.event)
        self.assertIn(self.event.slug, checkin_url)
        self.assertIn(str(attendee.id), checkin_url)
        self.assertIn(attendee.get_verification(), checkin_url)


class AttendeeManagerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = create_test_event()
        cls.user, _ = attendee_testutils.create_test_user("test@example.org")

    def test_get_checkin_code_or_email_with_checkin_code(self):
        attendee = Attendee.objects.create(
            user=self.user, event=self.event, checkin_code="abcd"
        )
        self.assertEqual(
            Attendee.objects.get_by_checkin_code_or_email("abcd", self.event), attendee
        )

    def test_get_checkin_code_or_email_with_email(self):
        attendee = Attendee.objects.create(
            user=self.user, event=self.event, checkin_code="efgh"
        )
        self.assertEqual(
            Attendee.objects.get_by_checkin_code_or_email(
                "test@example.org", self.event
            ),
            attendee,
        )

    def test_is_verification_valid(self):
        attendee = Attendee.objects.create(user=self.user, event=self.event)
        m = sha1(settings.SECRET_KEY.encode())
        m.update("{:08d}".format(int(attendee.id)).encode())
        verification = urlsafe_b64encode(m.digest()).decode("utf-8")
        self.assertTrue(
            Attendee.objects.is_verification_valid(attendee.id, verification)
        )


class AttendeeEventFeedbackTest(TestCase):
    def setUp(self):
        self.event = create_test_event()
        self.test_user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=self.test_user, event=self.event)

    def test_str(self):
        feedback = AttendeeEventFeedback.objects.create(
            attendee=self.attendee,
            event=self.event,
            overall_score=5,
            organisation_score=4,
            session_score=5,
            comment="Rocked again",
        )
        self.assertEqual(
            "{}".format(feedback),
            "{} gave feedback for {}: scores=event {}, organisation {}, sessions {}, comment={}".format(
                self.attendee, self.event.title, 5, 4, 5, "Rocked again"
            ),
        )


class BadgeDataTest(TestCase):
    def setUp(self):
        self.event = create_test_event()
        self.test_user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=self.test_user, event=self.event)

    def test_create(self):
        badge_data = BadgeData.objects.create(attendee=self.attendee, title="Attendee")
        self.assertIsNotNone(badge_data)
