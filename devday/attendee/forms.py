from django import forms

from attendee.models import Attendee


class AttendeeForm(forms.models.ModelForm):
    class Meta:
        model = Attendee
        fields = ["shirt_size"]