from django.core import mail
from django.http import HttpRequest
from django.test import TestCase
from django.utils import timezone

from attendee.forms import AttendeeRegistrationForm
from attendee.models import DevDayUser, Attendee
from attendee.views import AttendeeRegistrationView


class AttendeeProfileViewTest(TestCase):
    """
    Tests for attendee.views.AttendeeProfileView

    """

    def test_needs_login(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/accounts/profile/')

    def test_used_template(self):
        DevDayUser.objects.create_user('test@example.org', 's3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'attendee/profile.html')


class AttendeeRegistrationViewTest(TestCase):
    def test_get_email_context(self):
        request = HttpRequest()
        context = AttendeeRegistrationView(request=request).get_email_context('testkey')
        self.assertIn('request', context)
        self.assertEqual(context.get('request'), request)

    def test_register_minimum_fields(self):
        form = AttendeeRegistrationForm(
            data={'email': 'test@example.org', 'password1': 's3cr3t', 'password2': 's3cr3t'})
        valid = form.is_valid()
        self.assertTrue(valid, form.errors)

        request = HttpRequest()
        view = AttendeeRegistrationView(request=request)
        user = view.register(form)

        self.assertIsInstance(user, DevDayUser)
        self.assertIsNone(user.contact_permission_date)
        self.assertFalse(user.is_active)

        attendee = user.attendee
        self.assertIsInstance(attendee, Attendee)
        self.assertIsNone(attendee.contact_permission_date)

        self.assertEqual(len(mail.outbox), 1)

    def test_register_permit_contact(self):
        form = AttendeeRegistrationForm(
            data={'email': 'test@example.org', 'password1': 's3cr3t', 'password2': 's3cr3t',
                  'accept_general_contact': 'checked', 'accept_devday_contact': 'checked'})
        valid = form.is_valid()
        self.assertTrue(valid, form.errors)

        request = HttpRequest()
        view = AttendeeRegistrationView(request=request)
        user = view.register(form)
        now = timezone.now()

        self.assertIsInstance(user, DevDayUser)
        self.assertIsNotNone(user.contact_permission_date)
        self.assertLessEqual(user.contact_permission_date, now)
        self.assertFalse(user.is_active)

        attendee = user.attendee
        self.assertIsInstance(attendee, Attendee)
        self.assertIsNotNone(attendee.contact_permission_date)
        self.assertLessEqual(attendee.contact_permission_date, now)

        self.assertEqual(len(mail.outbox), 1)
