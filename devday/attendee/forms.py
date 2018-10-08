from __future__ import unicode_literals

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit, Hidden, HTML
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from django_registration.forms import RegistrationFormUniqueEmail

from attendee.models import DevDayUser, Attendee
from devday.forms import AuthenticationForm
from devday.utils.forms import (
    CombinedFormBase, DevDayFormHelper, DevDayField, DevDayContactField)
from talk.models import Talk

User = get_user_model()


class DevDayRegistrationForm(RegistrationFormUniqueEmail):
    accept_devday_contact = forms.BooleanField(
        label=_('Accept Dev Day contact'),
        help_text=_(
            'I would like to receive updates about Dev Day by email.'
        ),
        required=False
    )
    accept_general_contact = forms.BooleanField(
        label=_('Contact for other events'),
        help_text=_(
            'I would like to receive updates about T-Systems Multimedia '
            'Solutions GmbH Software Engineering Community by email.'
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


class AttendeeSourceForm(ModelForm):
    class Meta:
        model = Attendee
        fields = ['source']


class DevDayUserForm(ModelForm):
    class Meta:
        model = DevDayUser
        fields = [
            'first_name',
            'last_name',
            'twitter_handle',
            'phone',
            'position',
            'organization'
        ]


class AttendeeProfileForm(ModelForm):
    class Meta:
        model = DevDayUser
        fields = [
            'first_name',
            'last_name',
            'twitter_handle',
            'phone',
            'position',
            'organization',
            'contact_permission_date',
            'date_joined'
        ]

    def __init__(self, *args, **kwargs):
        super(AttendeeProfileForm, self).__init__(*args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_action = 'user_profile'
        self.helper.form_method = 'post'
        buttons = Div(css_class='col-12 col-sm-6 order-2 order-sm-1')
        if Talk.objects.filter(speaker__user__user=self.instance).count() == 0:
            buttons.append(
                HTML('<a href={} class="btn btn-outline-danger">{}</a>'.format(
                    reverse('attendee_delete'),
                    _('Delete your account')
                ))
            )
        buttons.append(
            HTML(
                '<a href="{}" class="btn btn-outline-secondary">{}</a>'.format(
                    reverse('auth_password_change'),
                    _('Change password'))), )
        self.helper.layout = Layout(
            Div(
                DevDayField('first_name', autofocus='autofocus',
                            wrapper_class='col-12 col-sm-6'),
                Field('last_name', wrapper_class='col-12 col-sm-6'),
                css_class='form-row'
            ),
            Div(
                Field('twitter_handle', wrapper_class='col-12 col-sm-6'),
                Field('phone', wrapper_class='col-12 col-sm-6'),
                css_class='form-row',
            ),
            HTML('<hr/>'),
            Div(
                Field('position', wrapper_class='col-12 col-sm-6'),
                Field('organization', wrapper_class='col-12 col-sm-6'),
                css_class='form-row',
            ),
            HTML('<hr/>'),
            Div(
                DevDayField('contact_permission_date', readonly="readonly",
                            wrapper_class='col-12 col-sm-6'),
                DevDayField('date_joined', readonly="readonly",
                            wrapper_class='col-12 col-sm-6'),
                css_class='form-row',
            ),
            Div(
                buttons,
                Div(
                    Submit(
                        'submit', _('Update your profile'),
                        css_class='btn btn-primary float-left float-sm-right'),
                    css_class='col-12 col-sm-6 order-1 order-sm-2'
                ),
                css_class='form-row',
            ),
        )
        self.helper.html5_required = True


class EventRegistrationForm(FormView):
    def __init__(self, *args, **kwargs):
        super(EventRegistrationForm, self).__init__(*args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_action = 'registration_register'
        self.helper.form_method = 'post'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(_('<label><p class="help-block">By registering as an'
                           ' attendee, I agree to be contacted by the Dev Day'
                           ' organizers about conference details.'
                           '</p></label>')),
                    css_class='checkbox'
                ),
                Submit('submit', _('Register as attendee')),
                css_class='col-md-12 offset-lg-2 col-lg-8 text-center',
            )
        )

    def _get_form_by_class(self, clazz):
        return getattr(self, clazz.__name__.lower())

    def get_user_form(self):
        return self._get_form_by_class(DevDayRegistrationForm)


class RegistrationAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(RegistrationAuthenticationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'login_or_register_attendee'
        self.helper.form_method = 'post'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Hidden('next', value=reverse('registration_register')),
                Field('username', template='devday/form/field.html',
                      autofocus='autofocus'),
                Field('password', template='devday/form/field.html'),
            ),
            Div(
                Submit('submit', _('Login'), css_class='btn-default'),
                css_class='text-center'
            )
        )


class AttendeeRegistrationForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, AttendeeSourceForm]

    def _get_form_by_class(self, clazz):
        return getattr(self, clazz.__name__.lower())

    def get_user_form(self):
        return self._get_form_by_class(DevDayRegistrationForm)

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
        self.fields['accept_devday_contact'].initial = True
        self.fields['accept_general_contact'].initial = False

        self.helper.layout = Layout(
            Div(
                DevDayField('email', autofocus='autofocus',
                            wrapper_class='col-12 col-md-6'),
                Field('twitter_handle', wrapper_class='col-12 col-md-6'),
                css_class='form-row'
            ),
            Div(
                Field('first_name', wrapper_class='col-12 col-md-6'),
                Field('last_name', wrapper_class='col-12 col-md-6'),
                css_class='form-row'
            ),
            Div(
                Field('password1', wrapper_class='col-12 col-md-6'),
                Field('password2', wrapper_class='col-12 col-md-6'),
                css_class='form-row'
            ),
            Div(
                Field('position', wrapper_class='col-12 col-md-6'),
                Field('organization', wrapper_class='col-12 col-md-6'),
                css_class='form-row'
            ),
            Div(
                DevDayField('source', rows=1, wrapper_class='col-12'),
                css_class='form-row',
            ),
            Div(
                Div(
                    HTML(_(
                        '<label><p class="help-block">By registering as an'
                        ' attendee, I agree to be contacted by the Dev Day'
                        ' organizers about conference details.</p></label>')),
                    css_class='checkbox'
                ),
                Hidden('accept_devday_contact', value='1'),
                DevDayContactField('accept_general_contact'),
                Submit('submit', _('Register as attendee')),
                css_class='col-12 text-center',
            )
        )
