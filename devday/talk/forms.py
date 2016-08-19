from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model

from registration.forms import RegistrationFormUniqueEmail

from attendee.forms import AttendeeForm
from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker

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


class CreateTalkWithSpeakerForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, AttendeeForm, SpeakerForm, TalkForm]
