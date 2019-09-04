from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from attendee.forms import DevDayUserChangeForm, DevDayUserCreationForm
from attendee.models import Attendee, AttendeeEventFeedback
from attendee.tests import attendee_testutils
from devday.utils.devdata import DevData
from event.models import Event
from event.tests import event_testutils

User = get_user_model()


class AttendeeAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.get(title="devdata.18")
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()
        cls.devdata.create_users_and_attendees(amount=10, events=[cls.event])

    def setUp(self):
        self.user_password = u"s3cr3t"
        self.user = User.objects.create_superuser(
            u"admin@example.org", self.user_password
        )
        self.client.login(email=self.user.email, password=self.user_password)

    def test_attendee_admin_list(self):
        response = self.client.get(reverse("admin:attendee_attendee_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["cl"].result_count >= 8, "should list some attendees"
        )


class DevDayUserAdmin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.get(title="devdata.18")
        cls.devdata = DevData()
        cls.devdata.create_talk_formats()
        cls.devdata.update_events()
        cls.devdata.create_users_and_attendees(amount=10, events=[cls.event])

    def setUp(self):
        self.user_password = u"s3cr3t"
        self.user = User.objects.create_superuser(
            u"admin@example.org", self.user_password
        )
        self.client.login(email=self.user.email, password=self.user_password)

    def test_devdayuser_admin_list(self):
        response = self.client.get(reverse("admin:attendee_devdayuser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["cl"].result_count == 11, "should list some users"
        )

    def test_devdayuser_admin_add(self):
        response = self.client.get(reverse("admin:attendee_devdayuser_add"))
        self.assertEqual(response.status_code, 200)
        form = response.context["adminform"].form
        self.assertIsInstance(form, DevDayUserCreationForm)

        response = self.client.post(
            reverse("admin:attendee_devdayuser_add"),
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
                "attendees-TOTAL_FORMS": "0",
                "attendees-INITIAL_FORMS": "0",
                "attendees-MIN_NUM_FORMS": "0",
                "attendees-MAX_NUM_FORMS": "0",
            },
        )
        user = User.objects.get(email="test@example.org")
        self.assertIsNotNone(user.id)
        self.assertTrue(user.check_password("s3cr3t"))
        self.assertRedirects(
            response, reverse("admin:attendee_devdayuser_change", args=(user.id,))
        )

    def test_devdayuser_admin_change(self):
        user = User.objects.first()
        response = self.client.get(
            reverse("admin:attendee_devdayuser_change", args=(user.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["adminform"].form, DevDayUserChangeForm)


class AttendeeEventFeedbackAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = event_testutils.create_test_event(title="Test event")
        user1, _ = attendee_testutils.create_test_user("test1@example.org")
        user2, _ = attendee_testutils.create_test_user("test2@example.org")
        cls.attendees = [
            Attendee.objects.create(user=user1, event=cls.event),
            Attendee.objects.create(user=user2, event=cls.event),
        ]
        cls.feedback = AttendeeEventFeedback.objects.create(
            event=cls.event,
            attendee=cls.attendees[0],
            overall_score=5,
            organisation_score=3,
            session_score=4,
            comment="It rocks",
        )

    def setUp(self):
        self.user_password = u"s3cr3t"
        self.user = User.objects.create_superuser(
            u"admin@example.org", self.user_password
        )
        self.client.login(email=self.user.email, password=self.user_password)

    def test_list(self):
        response = self.client.get(
            reverse("admin:attendee_attendeeeventfeedback_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context["cl"].result_count == 1, "should list an event feedback"
        )

    def test_change(self):
        response = self.client.get(
            reverse(
                "admin:attendee_attendeeeventfeedback_change", args=(self.feedback.id,)
            )
        )
        self.assertEqual(response.status_code, 200)
