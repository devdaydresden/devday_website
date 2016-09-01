from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from registration.forms import RegistrationFormUniqueEmail

from attendee.forms import AttendeeForm
from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit

User = get_user_model()


class TalkForm(forms.models.ModelForm):
    class Meta:
        model = Talk
        fields = ["title", "abstract"]


class SpeakerForm(forms.models.ModelForm):
    firstname = forms.fields.CharField(label=_("Firstname"), max_length=64)
    lastname = forms.fields.CharField(label=_("Lastname"), max_length=64)

    class Meta:
        model = Speaker
        fields = ["portrait", "shortbio", "videopermission"]


class DevDayRegistrationForm(RegistrationFormUniqueEmail):
    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = [
            'email',
            'password1',
            'password2'
        ]

    def clean(self):
        if self.cleaned_data.get('email'):
            self.cleaned_data[User.USERNAME_FIELD] = self.cleaned_data.get('email')
        return super(RegistrationFormUniqueEmail, self).clean()


class CreateTalkForSpeakerForm(CombinedFormBase):
    form_classes = [TalkForm]


class CreateTalkForAttendeeForm(CombinedFormBase):
    form_classes = [SpeakerForm, TalkForm]


class CreateTalkForUserForm(CombinedFormBase):
    form_classes = [AttendeeForm, SpeakerForm, TalkForm]


class CreateTalkWithSpeakerForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, AttendeeForm, SpeakerForm, TalkForm]

    def __init__(self, *args, **kwargs):
        super(CreateTalkWithSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'submit_session'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Field("email"),
                "password1",
                "password2",
                "shirt_size",
                Field("videopermission", template="talk/form/videopermission-field.html"),
                css_class = "col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                "firstname",
                "lastname",
                Field("portrait", template="talk/form/speakerportrait-field.html"),
                "shortbio",
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                "title",
                "abstract",
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                Submit('submit', _('Submit'), css_class="btn-default"),
                css_class="col-xs-12 col-sm-12 col-lg-6 col-lg-offset-4"
            )
        )