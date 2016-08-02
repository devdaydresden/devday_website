from django import forms
from django.utils.translation import ugettext_lazy as _

from attendee.forms import AttendeeForm
from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker


class TalkForm(forms.models.ModelForm):
    class Meta:
        model = Talk
        fields = ["title", "abstract"]


class SpeakerForm(forms.models.ModelForm):
    firstname = forms.fields.CharField(label=_("Firstname"), max_length=64)
    lastname = forms.fields.CharField(label=_("Lastname"), max_length=64)
    email = forms.fields.EmailField(label=_("Email"))

    class Meta:
        model = Speaker
        fields = ["portrait", "shortbio", "videopermission"]


class CreateTalkWithSpeakerForm(CombinedFormBase):
    form_classes = [AttendeeForm, SpeakerForm, TalkForm]