from crispy_forms.layout import Layout, Submit
from django.contrib.auth import forms as auth_forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from devday.utils.forms import DevDayField, DevDayFormHelper


class AuthenticationForm(auth_forms.AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthenticationForm, self).__init__(request, *args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            DevDayField('username', autofocus='autofocus'),
            'password',
        )


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(user, *args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            DevDayField('old_password', autofocus='autofocus'),
            'new_password1',
            'new_password2',
            Submit('submit', _('Change my password'))
        )


class PasswordResetForm(auth_forms.PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_action = reverse('auth_password_reset')
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            DevDayField('email', autofocus='autofocus'),
            Submit('submit', _('Reset my password')),
        )


class SetPasswordForm(auth_forms.SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super(SetPasswordForm, self).__init__(user, *args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            DevDayField('new_password1', autofocus='autofocus'),
            'new_password2',
            Submit('submit', _('Change my password')),
        )
