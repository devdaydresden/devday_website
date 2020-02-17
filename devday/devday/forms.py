from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from ckeditor.widgets import CKEditorWidget


class AuthenticationForm(auth_forms.AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("username", autofocus="autofocus"), "password"
        )


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                Field("old_password", autofocus="autofocus", wrapper_class="col-12"),
                css_class="form-row",
            ),
            Div(Field("new_password1", wrapper_class="col-12"), css_class="form-row"),
            Div(Field("new_password2", wrapper_class="col-12"), css_class="form-row"),
            Div(
                Div(
                    Submit("submit", _("Change my password")),
                    css_class="col-12 text-center",
                ),
                css_class="form-row",
            ),
        )


class PasswordResetForm(auth_forms.PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse("auth_password_reset")
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("email", autofocus="autofocus"),
            Submit("submit", _("Reset my password")),
        )


class SetPasswordForm(auth_forms.SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super(SetPasswordForm, self).__init__(user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("new_password1", autofocus="autofocus"),
            "new_password2",
            Submit("submit", _("Change my password")),
        )


def validate_email_address_file(address_file):
    errors = []
    for address in [line.strip().decode("ascii") for line in address_file.readlines()]:
        try:
            validate_email(address)
        except ValidationError as e:
            errors.append(
                ValidationError(
                    message=_("invalid email address {}").format(address), code=e.code
                )
            )
    address_file.seek(0)
    if errors:
        raise ValidationError(errors)


class SendEmailForm(forms.Form):
    recipients = forms.ChoiceField(label=_("Recipient Group"), choices=[])
    recipients_file = forms.FileField(
        label=_("Recipient List"),
        required=False,
        help_text=_("a list of recipient email addresses (one address on each line)"),
        validators=[validate_email_address_file],
    )
    subject = forms.CharField(label=_("Email Subject"), max_length=100)
    body = forms.CharField(label="Email Body", widget=CKEditorWidget())

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop("recipients")
        super().__init__(*args, **kwargs)
        self.fields["recipients"].choices = choices
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy("send_email")
        self.helper.form_method = "post"
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Field("recipients", help_text=_("Recipients for this email")),
                Field("recipients_file"),
                Field(
                    "subject",
                    autofocus="autofocus",
                    help_text=_("Email Subject"),
                    wrapper_class="col-12 col-md-6",
                ),
                Field("body", help_text=_("Email Body")),
                css_class="form-row",
            ),
            Div(
                Submit("sendself", _("Send Test Email To Myself"), css_class="default"),
                Submit(
                    "sendreal",
                    _("Send Email To Selected Recipients"),
                    style=(
                        "color: #fff !important;" "background-color:#f00 !important"
                    ),
                ),
            ),
        )

    def clean(self):
        super().clean()
        self.cleaned_data["sendreal"] = "sendreal" in self.data
