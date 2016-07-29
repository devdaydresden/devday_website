from django import forms

from attendee.forms import AttendeeForm
from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker


class TalkForm(forms.models.ModelForm):
    class Meta:
        model = Talk
        fields = ["title", "abstract"]


class SpeakerForm(forms.models.ModelForm):
    class Meta:
        model = Speaker
        fields = ["portrait", "shortbio", "videopermission"]


class CreateTalkWithSpeakerForm(CombinedFormBase):
    form_classes = [AttendeeForm, SpeakerForm, TalkForm]