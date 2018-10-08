from __future__ import unicode_literals

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.test import TestCase

from attendee.forms import DevDayRegistrationForm, AttendeeRegistrationForm
from attendee.models import Attendee, DevDayUser


class DevDayRegistrationFormTest(TestCase):
    def test_fields(self):
        form = DevDayRegistrationForm()
        self.assertListEqual(
            list(form.fields.keys()),
            ['email', 'password1', 'password2', 'first_name', 'last_name',
             'twitter_handle', 'phone', 'position', 'organization', 'accept_devday_contact',
             'accept_general_contact']
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
        self.assertEqual(form.cleaned_data[DevDayUser.USERNAME_FIELD], form.cleaned_data['email'])


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
