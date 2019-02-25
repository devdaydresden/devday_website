from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from attendee.models import Attendee
from event.models import Event
from talk.models import Talk, TalkFormat, TalkComment, Vote, SessionReservation, \
    TalkSlot, TimeSlot, Room

User = get_user_model()


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TalkForm, self).__init__(*args, **kwargs)
        self.fields['talkformat'].initial = TalkFormat.objects.all()

    class Meta:
        model = Talk
        fields = ['title', 'abstract', 'remarks', 'talkformat']
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'talkformat': forms.CheckboxSelectMultiple(),
        }


class CreateTalkForm(TalkForm):
    class Meta(TalkForm.Meta):
        fields = (
            'title', 'abstract', 'remarks', 'talkformat', 'draft_speaker',
            'event')
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'talkformat': forms.CheckboxSelectMultiple(),
            'draft_speaker': forms.HiddenInput,
            'event': forms.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        super(CreateTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            'submit_session', kwargs={'event': self.initial.get('event').slug})
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True

        self.helper.layout = Layout(
            Field('draft_speaker'),
            Field('event'),
            Div(
                Field("title", autofocus='autofocus'),
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                Field('talkformat'),
                css_class="form-group"
            ),
            Div(
                Div(
                    Submit('submit', _('Submit'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form-group"
            )
        )


class EditTalkForm(TalkForm):
    def __init__(self, *args, **kwargs):
        super(EditTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Field(
                    "title", autofocus='autofocus'),
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                Field('talkformat'),
                css_class="form-group"
            ),
            Div(
                Div(
                    Submit('submit', _('Update session'),
                           css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form-group"
            )
        )


class TalkCommentForm(forms.ModelForm):
    class Meta:
        model = TalkComment
        fields = ['comment', 'is_visible']

    def __init__(self, *args, **kwargs):
        super(TalkCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs['rows'] = 2
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'talk_comment', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Field('comment', rows=2),
                Field('is_visible', template='talk/form/is_visible-field.html'),
                css_class="form-group",
            ),
            Div(
                Div(
                    Submit(
                        'submit', _('Add comment'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form_group",
            ),
        )


class TalkSpeakerCommentForm(forms.ModelForm):
    class Meta:
        model = TalkComment
        fields = ['comment']

    def __init__(self, *args, **kwargs):
        super(TalkSpeakerCommentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'talk_speaker_comment', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            Div(
                Field('comment', rows=2),
                css_class="form-group",
            ),
            Div(
                Div(
                    Submit(
                        'submit', _('Add comment'), css_class="btn-default"),
                    css_class="text-center"
                ),
                css_class="form_group",
            )
        )


class TalkVoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ["score"]


class SessionReservationForm(forms.ModelForm):
    attendee = forms.ModelChoiceField(queryset=Attendee.objects.select_related(
        'user', 'event').distinct())

    class Meta:
        model = SessionReservation
        fields = ['talk_slot', 'attendee']


class TalkSlotForm(forms.ModelForm):
    talk = forms.ModelChoiceField(queryset=Talk.objects.select_related(
        'event', 'draft_speaker', 'published_speaker',
        'published_speaker__event').distinct())
    time = forms.ModelChoiceField(queryset=TimeSlot.objects.select_related(
        'event'))

    class Meta:
        model = TalkSlot
        fields = ["talk", "room", "time", "spots"]


class AddTalkSlotFormStep1(forms.Form):
    event = forms.ModelChoiceField(
        queryset=Event.objects.order_by('start_time'))


class AddTalkSlotFormStep2(forms.ModelForm):
    class Meta:
        model = TalkSlot
        fields = ('talk', 'spots', 'room', 'time')

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None,
                 use_required_attribute=None, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix,
            empty_permitted, instance, use_required_attribute)
        self.fields['talk'].queryset = Talk.objects.filter(
            event=self.event, track_id__isnull=False, talkslot__isnull=True
        ).select_related(
            'event', 'draft_speaker', 'published_speaker',
            'published_speaker__event').distinct()
        self.fields['time'].queryset = TimeSlot.objects.filter(
            event=self.event).select_related(
            'event')
        self.fields['room'].queryset = Room.objects.filter(
            event=self.event)
