from crispy_forms.helper import FormHelper
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from devday.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm)

User = get_user_model()


class AuthenticationFormTest(SimpleTestCase):
    """
    Tests for devday.forms.AuthenticationForm.

    """

    def test_base_is_django_authenticationform(self):
        form = AuthenticationForm()
        self.assertIsInstance(form, auth_forms.AuthenticationForm)

    def test_has_helper(self):
        form = AuthenticationForm()
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_tag_disabled(self):
        form = AuthenticationForm()
        self.assertFalse(form.helper.form_tag)

    def test_layout(self):
        form = AuthenticationForm()
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [
            name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 2)
        self.assertIn('username', layout_fields)
        self.assertIn('password', layout_fields)


class PasswordChangeFormTest(SimpleTestCase):
    """
    Tests for devday.forms.PasswordChangeForm.

    """

    def test_base_is_django_passwordchangeform(self):
        user = User(email='test@example.org')
        form = PasswordChangeForm(user)
        self.assertIsInstance(form, auth_forms.PasswordChangeForm)

    def test_has_helper(self):
        user = User(email='test@example.org')
        form = PasswordChangeForm(user)
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_method_is_post(self):
        user = User(email='test@example.org')
        form = PasswordChangeForm(user)
        self.assertEqual(form.helper.form_method, 'post')

    def test_layout(self):
        user = User(email='test@example.org')
        form = PasswordChangeForm(user)
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [
            name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 3)
        self.assertIn('old_password', layout_fields)
        self.assertIn('new_password1', layout_fields)
        self.assertIn('new_password2', layout_fields)


class PasswordResetFormTest(SimpleTestCase):
    """
    Tests for devday.forms.PasswordResetForm.

    """

    def test_base_is_django_passwordresetform(self):
        form = PasswordResetForm()
        self.assertIsInstance(form, auth_forms.PasswordResetForm)

    def test_has_helper(self):
        form = PasswordResetForm()
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_action_password_reset(self):
        form = PasswordResetForm()
        self.assertEqual(form.helper.form_action, '/accounts/password/reset/')

    def test_form_method_is_post(self):
        form = PasswordResetForm()
        self.assertEqual(form.helper.form_method, 'post')

    def test_layout(self):
        form = PasswordResetForm()
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [
            name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 1)
        self.assertIn('email', layout_fields)


class SetPasswordFormTest(SimpleTestCase):
    """
    Tests for devday.forms.SetPasswordForm.

    """

    def test_base_is_django_setpasswordform(self):
        user = User(email='test@example.org')
        form = SetPasswordForm(user)
        self.assertIsInstance(form, auth_forms.SetPasswordForm)

    def test_has_helper(self):
        user = User(email='test@example.org')
        form = SetPasswordForm(user)
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_method_is_post(self):
        user = User(email='test@example.org')
        form = SetPasswordForm(user)
        self.assertEqual(form.helper.form_method, 'post')

    def test_layout(self):
        user = User(email='test@example.org')
        form = SetPasswordForm(user)
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [
            name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 2)
        self.assertIn('new_password1', layout_fields)
        self.assertIn('new_password2', layout_fields)
