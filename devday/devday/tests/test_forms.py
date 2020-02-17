from unittest.mock import patch

from crispy_forms.helper import FormHelper
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from devday.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SendEmailForm,
    SetPasswordForm,
    validate_email_address_file,
)

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
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 2)
        self.assertIn("username", layout_fields)
        self.assertIn("password", layout_fields)


class PasswordChangeFormTest(SimpleTestCase):
    """
    Tests for devday.forms.PasswordChangeForm.

    """

    def test_base_is_django_passwordchangeform(self):
        user = User(email="test@example.org")
        form = PasswordChangeForm(user)
        self.assertIsInstance(form, auth_forms.PasswordChangeForm)

    def test_has_helper(self):
        user = User(email="test@example.org")
        form = PasswordChangeForm(user)
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_method_is_post(self):
        user = User(email="test@example.org")
        form = PasswordChangeForm(user)
        self.assertEqual(form.helper.form_method, "post")

    def test_layout(self):
        user = User(email="test@example.org")
        form = PasswordChangeForm(user)
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 3)
        self.assertIn("old_password", layout_fields)
        self.assertIn("new_password1", layout_fields)
        self.assertIn("new_password2", layout_fields)


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
        self.assertEqual(form.helper.form_action, "/accounts/password/reset/")

    def test_form_method_is_post(self):
        form = PasswordResetForm()
        self.assertEqual(form.helper.form_method, "post")

    def test_layout(self):
        form = PasswordResetForm()
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 1)
        self.assertIn("email", layout_fields)


class SetPasswordFormTest(SimpleTestCase):
    """
    Tests for devday.forms.SetPasswordForm.

    """

    def test_base_is_django_setpasswordform(self):
        user = User(email="test@example.org")
        form = SetPasswordForm(user)
        self.assertIsInstance(form, auth_forms.SetPasswordForm)

    def test_has_helper(self):
        user = User(email="test@example.org")
        form = SetPasswordForm(user)
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_method_is_post(self):
        user = User(email="test@example.org")
        form = SetPasswordForm(user)
        self.assertEqual(form.helper.form_method, "post")

    def test_layout(self):
        user = User(email="test@example.org")
        form = SetPasswordForm(user)
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 2)
        self.assertIn("new_password1", layout_fields)
        self.assertIn("new_password2", layout_fields)


def _get_upload_file(recipient_list):
    return SimpleUploadedFile(
        "recipients.txt", "\n".join(recipient_list).encode("UTF-8")
    )


class ValidateEmailAddressFileTest(SimpleTestCase):
    def test_validate_email_address_file_valid(self):
        test_recipients = ["recipient_a@example.org", "recipient_b@example.org"]
        validate_email_address_file(_get_upload_file(test_recipients))

    def test_validate_email_address_invalid_addresses(self):
        test_data = ["recipient_a_at_example.org", "recipient_b@example.org"]
        with self.assertRaises(ValidationError) as e:
            validate_email_address_file(_get_upload_file(test_data))
        self.assertEqual(len(e.exception.error_list), 1)


class SendEmailFormTest(SimpleTestCase):
    def test_has_helper(self):
        choices = (("foo", "Foo"), ("bar", "Bar"))
        form = SendEmailForm(recipients=choices)
        self.assertIsInstance(form.helper, FormHelper)

    def test_form_method_is_post(self):
        choices = (("foo", "Foo"), ("bar", "Bar"))
        form = SendEmailForm(recipients=choices)
        self.assertEqual(form.helper.form_method, "post")

    def test_layout(self):
        choices = (("foo", "Foo"), ("bar", "Bar"))
        form = SendEmailForm(recipients=choices)
        self.assertIsNotNone(form.helper.layout)
        layout_fields = [name for [_, name] in form.helper.layout.get_field_names()]
        self.assertEqual(len(layout_fields), 4)
        self.assertIn("recipients", layout_fields)
        self.assertIn("recipients_file", layout_fields)
        self.assertIn("subject", layout_fields)
        self.assertIn("body", layout_fields)

    def test_form_uses_validate_email_address_file(self):
        choices = (("foo", "Foo"), ("bar", "Bar"))
        test_data = ["recipient_with_no_at", "recipient_with_an@example.org"]
        form = SendEmailForm(
            recipients=choices,
            data={"recipients": "foo", "subject": "Test", "body": "A mail body"},
            files={"recipients_file": _get_upload_file(test_data)},
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("recipients_file", "invalid"))
