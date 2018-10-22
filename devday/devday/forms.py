from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div
from django.contrib.auth import forms as auth_forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


class AuthenticationForm(auth_forms.AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('username', autofocus='autofocus'),
            'password',
        )


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field('old_password', autofocus='autofocus',
                      wrapper_class='col-12'),
                css_class='form-row'
            ),
            Div(
                Field('new_password1', wrapper_class='col-12'),
                css_class='form-row'
            ),
            Div(
                Field('new_password2', wrapper_class='col-12'),
                css_class='form-row'
            ),
            Div(
                Div(
                    Submit('submit', _('Change my password')),
                    css_class='col-12 text-center'
                ),
                css_class='form-row'
            )
        )


class PasswordResetForm(auth_forms.PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('auth_password_reset')
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', autofocus='autofocus'),
            Submit('submit', _('Reset my password')),
        )


class SetPasswordForm(auth_forms.SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super(SetPasswordForm, self).__init__(user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('new_password1', autofocus='autofocus'),
            'new_password2',
            Submit('submit', _('Change my password')),
        )
