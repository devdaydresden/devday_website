from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.test import TestCase

from attendee.forms import (
    AttendeeRegistrationForm, CheckInAttendeeForm, DevDayRegistrationForm,
    DevDayUserCreationForm, RegistrationAuthenticationForm)
from attendee.models import Attendee, DevDayUser
from event.models import Event

ADMIN_EMAIL = 'admin@example.org'
ADMIN_PASSWORD = 'sUp3rS3cr3t'
USER_EMAIL = 'test@example.org'
USER_PASSWORD = 's3cr3t'


class DevDayRegistrationFormTest(TestCase):
    def test_fields(self):
        form = DevDayRegistrationForm()
        self.assertListEqual(
            list(form.fields.keys()),
            ['email', 'password1', 'password2', 'first_name', 'last_name',
             'twitter_handle', 'phone', 'position', 'organization',
             'accept_devday_contact', 'accept_general_contact']
        )

    def test_model(self):
        form = DevDayRegistrationForm()
        form.cleaned_data = {'password1': 'dummy'}
        user = form.save(commit=False)
        self.assertIsInstance(user, DevDayUser)

    def test_clean_sets_username(self):
        form = DevDayRegistrationForm()
        form.cleaned_data = {'email': 'dummy@example.org'}
        form.clean()
        self.assertEqual(form.cleaned_data[DevDayUser.USERNAME_FIELD],
                         form.cleaned_data['email'])


class DevDayUserCreationFormTest(TestCase):
    def test_get_user_form(self):
        form = DevDayUserCreationForm()
        self.assertIsNotNone(form)


class RegistrationAuthenticationFormTest(TestCase):
    def test_get_user_form(self):
        form = RegistrationAuthenticationForm()
        self.assertIsNotNone(form)


class AttendeeRegistrationFormTest(TestCase):
    def test_get_user_form(self):
        form = AttendeeRegistrationForm()
        self.assertIsInstance(form.get_user_form(), DevDayRegistrationForm)

    def test_init_creates_form_helper(self):
        form = AttendeeRegistrationForm()
        self.assertIsInstance(form.helper, FormHelper)
        self.assertEqual(form.helper.form_action, '/attendee/register/')
        self.assertEqual(form.helper.form_method, 'post')
        self.assertTrue(form.helper.html5_required)

    def test_init_creates_layout(self):
        form = AttendeeRegistrationForm()
        self.assertIsInstance(form.helper.layout, Layout)
        layout_fields = [name for [_, name] in
                         form.helper.layout.get_field_names()]
        self.assertListEqual(
            layout_fields,
            ['email', 'twitter_handle', 'first_name', 'last_name', 'password1',
             'password2', 'position', 'organization', 'source',
             'accept_general_contact']
        )


class CheckInAttendeeFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.current_event()
        cls.user_password = 'test'
        cls.user = DevDayUser.objects.create_user(
            'testqrcode@example.org', cls.user_password)
        cls.attendee = Attendee.objects.create(user=cls.user, event=cls.event)

    def test_form_valid_code(self):
        form = CheckInAttendeeForm(
            data={'attendee': self.attendee.checkin_code})
        self.assertIsInstance(form.helper, FormHelper)
        self.assertTrue(form.is_valid(),
                        'should be valid because code matches')

    def test_form_valid_email(self):
        form = CheckInAttendeeForm(
            data={'attendee': self.attendee.user.email})
        self.assertTrue(form.is_valid(),
                        'should be valid because email matches')

    def test_form_invalid_no_data(self):
        form = CheckInAttendeeForm(data={})
        self.assertFalse(form.is_valid(),
                         'should invalid because no code was entered')

    def test_form_invalid_code(self):
        form = CheckInAttendeeForm(data={'attendee': '12345678'})
        self.assertFalse(form.is_valid(),
                         'should be invalid because the code is wrong')

    def test_form_invalid_already(self):
        self.attendee.check_in()
        self.attendee.save()
        form = CheckInAttendeeForm(
            data={'attendee': self.attendee.user.email})
        self.assertFalse(form.is_valid(),
                         ('should be invalid because attendee is already'
                          ' checked in'))
