from datetime import timedelta
from unittest.mock import MagicMock

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.test import TestCase
from django.utils import timezone

from attendee.forms import (
    AttendeeEventFeedbackForm,
    AttendeeProfileForm,
    AttendeeRegistrationForm,
    BadgeDataForm,
    CheckInAttendeeForm,
    DevDayRegistrationForm,
    DevDayUserCreationForm,
    DevDayUserRegistrationForm,
    EventRegistrationForm,
    RegistrationAuthenticationForm,
)
from attendee.models import Attendee, AttendeeEventFeedback, BadgeData, DevDayUser
from attendee.tests import attendee_testutils
from event.models import Event
from event.tests import event_testutils

ADMIN_EMAIL = "admin@example.org"
ADMIN_PASSWORD = "sUp3rS3cr3t"
USER_EMAIL = "test@example.org"
USER_PASSWORD = "s3cr3t"


class DevDayRegistrationFormTest(TestCase):
    def test_fields(self):
        form = DevDayRegistrationForm()
        self.assertListEqual(
            list(form.fields.keys()),
            ["email", "password1", "password2", "accept_general_contact"],
        )

    def test_model(self):
        form = DevDayRegistrationForm()
        form.cleaned_data = {"password1": "dummy"}
        user = form.save(commit=False)
        self.assertIsInstance(user, DevDayUser)

    def test_clean_sets_username(self):
        form = DevDayRegistrationForm()
        form.cleaned_data = {"email": "dummy@example.org"}
        form.clean()
        self.assertEqual(
            form.cleaned_data[DevDayUser.USERNAME_FIELD], form.cleaned_data["email"]
        )


class DevDayUserCreationFormTest(TestCase):
    def test_get_user_form(self):
        form = DevDayUserCreationForm()
        self.assertIsNotNone(form)

    def test_form_save_commit(self):
        form = DevDayUserCreationForm(
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            }
        )
        user = form.save(commit=True)
        self.assertIsNotNone(user.id)
        self.assertTrue(user.check_password("s3cr3t"))

    def test_form_save_no_commit(self):
        form = DevDayUserCreationForm(
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            }
        )
        user = form.save(commit=False)
        self.assertIsNone(user.id)
        self.assertTrue(user.check_password("s3cr3t"))


class RegistrationAuthenticationFormTest(TestCase):
    def test_get_user_form(self):
        event = event_testutils.create_test_event()
        form = RegistrationAuthenticationForm(event=event)
        self.assertIsNotNone(form)

    def test_form_helper_action_url(self):
        event = event_testutils.create_test_event()
        form = RegistrationAuthenticationForm(event=event)
        self.assertEqual(
            form.helper.form_action, "/{}/attendee/join/".format(event.slug)
        )


class DevDayUserRegistrationFormTest(TestCase):
    def test_form_save_commit(self):
        form = DevDayUserRegistrationForm(
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            }
        )
        user = form.save(commit=True)
        self.assertIsNotNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))

    def test_form_save_no_commit(self):
        form = DevDayUserRegistrationForm(
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            }
        )
        user = form.save(commit=False)
        self.assertIsNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))

    def test_form_save_with_contact_permission(self):
        form = DevDayUserRegistrationForm(
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
                "accept_general_contact": "checked",
            }
        )
        user = form.save(commit=True)
        self.assertIsNotNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))


class AttendeeRegistrationFormTest(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()

    def test_init_creates_form_helper(self):
        form = AttendeeRegistrationForm(event=self.event)
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(
            form.helper.form_action, "/{}/attendee/register/".format(self.event.slug)
        )
        self.assertEqual(form.helper.form_method, "post")
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        form = AttendeeRegistrationForm(event=self.event)
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertListEqual(
            layout_fields, ["email", "password1", "password2", "accept_general_contact"]
        )

    def test_form_save_commit(self):
        form = AttendeeRegistrationForm(
            event=self.event,
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            },
        )
        user = form.save(commit=True)
        self.assertIsNotNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))

    def test_form_save_contact_permission(self):
        form = AttendeeRegistrationForm(
            event=self.event,
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
                "accept_general_contact": "checked",
            },
        )
        user = form.save(commit=True)
        self.assertIsNotNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))

    def test_form_save_no_commit(self):
        form = AttendeeRegistrationForm(
            event=self.event,
            data={
                "email": "test@example.org",
                "password1": "s3cr3t",
                "password2": "s3cr3t",
            },
        )
        user = form.save(commit=False)
        self.assertIsNone(user.id)
        self.assertFalse(user.is_active)
        self.assertIsNone(user.contact_permission_date)
        self.assertTrue(user.check_password("s3cr3t"))


class AttendeeProfileFormTest(TestCase):
    def test_form_save_no_commit(self):
        user, _ = attendee_testutils.create_test_user()
        user.save = MagicMock(return_value=None)

        form = AttendeeProfileForm(instance=user, data={})
        form.save(commit=False)
        user.save.assert_not_called()

    def test_form_save_accept_general_contact(self):
        user, _ = attendee_testutils.create_test_user()
        form = AttendeeProfileForm(
            instance=user,
            data={
                "accept_general_contact": "checked",
                "contact_permission_date": "",
                "date_joined": user.date_joined.isoformat(),
            },
        )
        user = form.save()
        self.assertIsNotNone(user.contact_permission_date)

    def test_form_save_accept_general_contact_again(self):
        user, _ = attendee_testutils.create_test_user()
        user.contact_permission_date = timezone.now() - timedelta(days=1)
        user.save()
        user.refresh_from_db()
        permission_date = user.contact_permission_date
        form = AttendeeProfileForm(
            instance=user,
            data={
                "accept_general_contact": "checked",
                "contact_permission_date": user.contact_permission_date.isoformat(),
                "date_joined": user.date_joined.isoformat(),
            },
        )
        user = form.save()
        self.assertIsNotNone(user.contact_permission_date)
        self.assertEqual(user.contact_permission_date, permission_date)

    def test_form_save_no_accept_general_contact(self):
        user, _ = attendee_testutils.create_test_user()
        user.contact_permission_date = timezone.now()
        user.save()
        form = AttendeeProfileForm(
            instance=user,
            data={
                "accept_general_contact": "",
                "contact_permission_date": user.contact_permission_date.isoformat(),
                "date_joined": user.date_joined.isoformat(),
            },
        )
        user = form.save()
        self.assertIsNone(user.contact_permission_date)


class EventRegistrationFormTest(TestCase):
    def test_form_save_no_commit(self):
        event = event_testutils.create_test_event()
        user, _ = attendee_testutils.create_test_user()

        form = EventRegistrationForm(event=event, user=user, data={})
        attendee = form.save(commit=False)
        self.assertIsNone(attendee.id)
        self.assertEqual(attendee.event, event)
        self.assertEqual(attendee.user, user)

    def test_save_with_commit(self):
        event = event_testutils.create_test_event()
        user, _ = attendee_testutils.create_test_user()

        form = EventRegistrationForm(event=event, user=user, data={})
        attendee = form.save()
        self.assertIsNotNone(attendee.id)
        self.assertEqual(attendee.event, event)
        self.assertEqual(attendee.user, user)


class CheckInAttendeeFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.current_event()
        cls.user_password = "test"
        cls.user = DevDayUser.objects.create_user(
            "testqrcode@example.org", cls.user_password
        )
        cls.attendee = Attendee.objects.create(user=cls.user, event=cls.event)

    def test_form_valid_code(self):
        form = CheckInAttendeeForm(
            data={"attendee": self.attendee.checkin_code}, event=self.event
        )
        self.assertIsInstance(form.helper, FormHelper)
        self.assertTrue(form.is_valid(), "should be valid because code matches")

    def test_form_valid_email(self):
        form = CheckInAttendeeForm(
            data={"attendee": self.attendee.user.email}, event=self.event
        )
        self.assertTrue(form.is_valid(), "should be valid because email matches")

    def test_form_invalid_no_data(self):
        form = CheckInAttendeeForm(data={}, event=self.event)
        self.assertFalse(form.is_valid(), "should invalid because no code was entered")

    def test_form_invalid_code(self):
        form = CheckInAttendeeForm(data={"attendee": "12345678"}, event=self.event)
        self.assertFalse(form.is_valid(), "should be invalid because the code is wrong")

    def test_form_invalid_already(self):
        self.attendee.check_in()
        self.attendee.save()
        form = CheckInAttendeeForm(
            data={"attendee": self.attendee.user.email}, event=self.event
        )
        self.assertFalse(
            form.is_valid(), "should be invalid because attendee is already checked in"
        )


class AttendeeEventFeedbackFormTest(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event("Test event")
        user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=user, event=self.event)

    def test_form_has_helper(self):
        form = AttendeeEventFeedbackForm(
            initial={"event": self.event, "attendee": self.attendee}
        )
        self.assertTrue(hasattr(form, "helper"))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertTrue(form.helper.html5_required)

    def test_form_has_layout(self):
        form = AttendeeEventFeedbackForm(
            initial={"event": self.event, "attendee": self.attendee}
        )
        self.assertTrue(hasattr(form, "helper"))
        self.assertTrue(hasattr(form.helper, "layout"))
        self.assertIsInstance(form.helper.layout, Layout)

    def test_save_creates_new_feedback_if_missing(self):
        self.assertFalse(
            AttendeeEventFeedback.objects.filter(
                attendee=self.attendee, event=self.event
            ).exists()
        )
        form = AttendeeEventFeedbackForm(
            initial={"event": self.event, "attendee": self.attendee},
            instance=AttendeeEventFeedback.objects.filter(
                attendee=self.attendee, event=self.event
            ).first(),
            data={
                "overall_score": "3",
                "session_score": "5",
                "organisation_score": "4",
            },
        )
        form.save()
        self.assertTrue(
            AttendeeEventFeedback.objects.filter(
                attendee=self.attendee, event=self.event
            ).exists()
        )

    def test_save_updates_feedback_if_exists(self):
        AttendeeEventFeedback.objects.create(
            attendee=self.attendee,
            event=self.event,
            overall_score=5,
            session_score=3,
            organisation_score=1,
        )
        form = AttendeeEventFeedbackForm(
            initial={"event": self.event, "attendee": self.attendee},
            instance=AttendeeEventFeedback.objects.filter(
                attendee=self.attendee, event=self.event
            ).first(),
            data={
                "overall_score": "3",
                "session_score": "5",
                "organisation_score": "4",
            },
        )
        form.save()
        self.assertTrue(
            AttendeeEventFeedback.objects.filter(
                attendee=self.attendee, event=self.event
            ).exists()
        )
        feedback = AttendeeEventFeedback.objects.get(
            attendee=self.attendee, event=self.event
        )
        self.assertEqual(feedback.overall_score, 3)
        self.assertEqual(feedback.organisation_score, 4)
        self.assertEqual(feedback.session_score, 5)


class BadgeDataFormTest(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event("Test event")
        user, _ = attendee_testutils.create_test_user()
        self.attendee = Attendee.objects.create(user=user, event=self.event)

    def test_form_has_helper(self):
        form = BadgeDataForm(attendee=self.attendee)
        self.assertTrue(hasattr(form, "helper"))
        self.assertIsInstance(form.helper, FormHelper)
        self.assertTrue(form.helper.html5_required)

    def test_form_has_layout(self):
        form = BadgeDataForm(attendee=self.attendee)
        self.assertTrue(hasattr(form, "helper"))
        self.assertTrue(hasattr(form.helper, "layout"))
        self.assertIsInstance(form.helper.layout, Layout)

    def test_save_with_no_commit(self):
        test_topics = "- attend events\n- talk\n- food"
        form = BadgeDataForm(
            attendee=self.attendee,
            data={
                "title": "The Attendee",
                "contact": "@attendee",
                "topics": test_topics,
            },
        )
        badge_data = form.save(commit=False)
        self.assertIsNone(badge_data.id)
        self.assertEqual(badge_data.attendee, self.attendee)
        self.assertEqual(badge_data.title, "The Attendee")
        self.assertEqual(badge_data.contact, "@attendee")
        self.assertEqual(badge_data.topics, test_topics)

    def test_save_with_commit(self):
        test_topics = "- attend events\n- talk\n- food"
        form = BadgeDataForm(
            attendee=self.attendee,
            data={
                "title": "The Attendee",
                "contact": "@attendee",
                "topics": test_topics,
            },
        )
        badge_data = form.save()
        self.assertIsNotNone(badge_data.id)
        self.assertEqual(badge_data.attendee, self.attendee)
        self.assertEqual(badge_data.title, "The Attendee")
        self.assertEqual(badge_data.contact, "@attendee")
        self.assertEqual(badge_data.topics, test_topics)

    def test_save_with_commit_existing(self):
        test_topics = "- attend events\n- talk\n- food"
        original_badge_data = BadgeData.objects.create(
            attendee=self.attendee, title="Mr. Attendee"
        )
        form = BadgeDataForm(
            attendee=self.attendee,
            instance=original_badge_data,
            data={
                "title": "The Attendee",
                "contact": "@attendee",
                "topics": test_topics,
            },
        )
        badge_data = form.save()
        self.assertIsNotNone(badge_data.id)
        self.assertEqual(badge_data.id, original_badge_data.id)
        self.assertEqual(badge_data.attendee, self.attendee)
        self.assertEqual(badge_data.title, "The Attendee")
        self.assertEqual(badge_data.contact, "@attendee")
        self.assertEqual(badge_data.topics, test_topics)
