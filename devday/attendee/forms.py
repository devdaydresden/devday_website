from __future__ import unicode_literals

from crispy_forms.layout import Layout, Div, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationFormUniqueEmail

from attendee.models import Attendee, DevDayUser
from devday.utils.forms import CombinedFormBase, DevDayFormHelper, DevDayField, DevDayContactField

User = get_user_model()


class AttendeeInformationForm(ModelForm):
    accept_devday_contact = forms.BooleanField(
        label=_('Accept DevDay contact'),
        help_text=_(
            'I hereby agree to be contacted by the DevDay 17 organization team.'
        ),
        required=False
    )

    class Meta:
        model = Attendee
        fields = ['source']


class DevDayRegistrationForm(RegistrationFormUniqueEmail):
    accept_general_contact = forms.BooleanField(
        label=_('Contact for other events'),
        help_text=_(
            'I hereby agree to be contacted for other SECO events.'
        ),
        required=False
    )

    class Meta(RegistrationFormUniqueEmail.Meta):
        model = User
        fields = [
            'email',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'twitter_handle',
            'phone',
            'position',
            'organization',
        ]


class DevDayUserForm(ModelForm):
    class Meta:
        model = DevDayUser
        fields = ['first_name',
            'last_name',
            'twitter_handle',
            'phone',
            'position',
            'organization'
        ]


class AttendeeRegistrationForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, AttendeeInformationForm]

    def _get_form_by_class(self, clazz):
        return getattr(self, clazz.__name__.lower())

    def get_user_form(self):
        return self._get_form_by_class(DevDayRegistrationForm)

    def get_attendee_form(self):
        return self._get_form_by_class(AttendeeInformationForm)

    def __init__(self, *args, **kwargs):
        super(AttendeeRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_action = 'registration_register'
        self.helper.form_method = 'post'
        self.helper.html5_required = True
        self.fields['email'].help_text = None
        self.fields['email'].label = _('E-Mail')
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        self.helper.layout = Layout(
            Div(
                DevDayField('email', autofocus='autofocus'),
                'first_name',
                'last_name',
                'password1',
                'password2',
                css_class='col-md-12 col-lg-offset-2 col-lg-4'
            ),
            Div(
                'position',
                'organization',
                'twitter_handle',
                DevDayField('source', rows=2),
                css_class='col-md-12 col-lg-4',
            ),
            Div(
                DevDayContactField('accept_devday_contact'),
                DevDayContactField('accept_general_contact'),
                Submit('submit', _('Register as attendee')),
                css_class='col-md-12 col-lg-offset-2 col-lg-8 text-center',
            )
        )
