from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.forms.utils import ErrorList
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from attendee.models import Attendee
from event.models import Event
from talk.models import (
    AttendeeFeedback,
    AttendeeVote,
    Room,
    SessionReservation,
    Talk,
    TalkComment,
    TalkFormat,
    TalkSlot,
    TimeSlot,
    Vote,
    TalkDraftSpeaker,
)

User = get_user_model()


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TalkForm, self).__init__(*args, **kwargs)
        self.fields["talkformat"].initial = TalkFormat.objects.all()

    class Meta:
        model = Talk
        fields = ["title", "abstract", "remarks", "talkformat"]
        widgets = {
            "abstract": forms.Textarea(attrs={"rows": 3}),
            "remarks": forms.Textarea(attrs={"rows": 3}),
            "talkformat": forms.CheckboxSelectMultiple(),
        }


class CreateTalkForm(TalkForm):
    class Meta(TalkForm.Meta):
        fields = ("title", "abstract", "remarks", "talkformat", "event")
        widgets = {
            "abstract": forms.Textarea(attrs={"rows": 3}),
            "remarks": forms.Textarea(attrs={"rows": 3}),
            "talkformat": forms.CheckboxSelectMultiple(),
            "event": forms.HiddenInput,
        }

    def __init__(self, *args, **kwargs):
        self.draft_speaker = kwargs.pop("draft_speaker")
        super(CreateTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            "submit_session", kwargs={"event": self.initial.get("event").slug}
        )
        self.helper.form_id = "create-talk-form"
        self.helper.field_template = "devday/form/field.html"
        self.helper.html5_required = True

        self.helper.layout = Layout(
            Field("draft_speakers"),
            Field("event"),
            Div(
                Field("title", autofocus="autofocus"),
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                Field("talkformat"),
                css_class="form-group",
            ),
            Div(
                Div(
                    Submit("submit", _("Submit"), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form-group",
            ),
        )

    def save(self, commit=True):
        talk = super().save(commit)
        draft_speaker = TalkDraftSpeaker(
            talk=talk, draft_speaker=self.draft_speaker, order=1
        )
        if commit:
            draft_speaker.save()
        return talk


class EditTalkForm(TalkForm):
    def __init__(self, *args, **kwargs):
        super(EditTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.field_template = "devday/form/field.html"
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Field("title", autofocus="autofocus"),
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                Field("talkformat"),
                css_class="form-group",
            ),
            Div(
                Div(
                    Submit("submit", _("Update session"), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form-group",
            ),
        )


class TalkCommentForm(forms.ModelForm):
    class Meta:
        model = TalkComment
        fields = ["comment", "is_visible"]

    def __init__(self, *args, **kwargs):
        super(TalkCommentForm, self).__init__(*args, **kwargs)
        self.fields["comment"].widget.attrs["rows"] = 2
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            "talk_comment", kwargs={"pk": self.instance.pk}
        )
        self.helper.layout = Layout(
            Div(
                Field("comment", rows=2),
                Field("is_visible", template="talk/form/is_visible-field.html"),
                css_class="form-group",
            ),
            Div(
                Div(
                    Submit("submit", _("Add comment"), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form_group",
            ),
        )


class TalkSpeakerCommentForm(forms.ModelForm):
    class Meta:
        model = TalkComment
        fields = ["comment"]

    def __init__(self, *args, **kwargs):
        super(TalkSpeakerCommentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            "talk_speaker_comment", kwargs={"pk": self.instance.pk}
        )
        self.helper.layout = Layout(
            Div(Field("comment", rows=2), css_class="form-group"),
            Div(
                Div(
                    Submit("submit", _("Add comment"), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form_group",
            ),
        )


class TalkVoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = ["score"]


class SessionReservationForm(forms.ModelForm):
    attendee = forms.ModelChoiceField(
        queryset=Attendee.objects.select_related("user", "event").distinct()
    )

    class Meta:
        model = SessionReservation
        fields = ["talk", "attendee", "is_confirmed", "is_waiting"]


class TalkSlotForm(forms.ModelForm):
    talk = forms.ModelChoiceField(
        queryset=Talk.objects.select_related("event").distinct()
    )
    time = forms.ModelChoiceField(queryset=TimeSlot.objects.select_related("event"))

    class Meta:
        model = TalkSlot
        fields = ["talk", "room", "time"]


class AddTalkSlotFormStep1(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.order_by("start_time"))


class AddTalkSlotFormStep2(forms.ModelForm):
    class Meta:
        model = TalkSlot
        fields = ("talk", "room", "time")

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        instance=None,
        use_required_attribute=None,
        **kwargs
    ):
        self.event = kwargs.pop("event")
        super().__init__(
            data,
            files,
            auto_id,
            prefix,
            initial,
            error_class,
            label_suffix,
            empty_permitted,
            instance,
            use_required_attribute,
        )
        self.fields["talk"].queryset = (
            Talk.objects.filter(
                event=self.event, track_id__isnull=False, talkslot__isnull=True
            )
            .select_related("event")
            .distinct()
        )
        self.fields["time"].queryset = TimeSlot.objects.filter(
            event=self.event
        ).select_related("event")
        self.fields["room"].queryset = Room.objects.filter(event=self.event)


class AttendeeTalkVoteForm(forms.ModelForm):
    class Meta:
        model = AttendeeVote
        fields = ["score"]


class TalkAddReservationForm(forms.ModelForm):
    class Meta:
        model = SessionReservation
        fields = []

    def __init__(self, **kwargs):
        self.attendee = kwargs.pop("attendee")
        self.talk = kwargs.pop("talk")
        super().__init__(**kwargs)

    def save(self, commit=True):
        self.instance.attendee = self.attendee
        self.instance.talk = self.talk
        self.instance.is_confirmed = False
        if (
            self.instance.talk.sessionreservation_set.filter(is_confirmed=True).count()
            >= self.instance.talk.spots
        ):
            self.instance.is_waiting = True
        return super().save(commit)


class AttendeeTalkFeedbackForm(forms.ModelForm):
    class Meta:
        model = AttendeeFeedback
        fields = ["score", "comment"]

    talk = None
    attendee = None

    def __init__(self, *args, **kwargs):
        self.talk = kwargs.pop("talk")
        self.attendee = kwargs.pop("attendee")
        super().__init__(*args, **kwargs)
        self.fields["comment"].widget.attrs["rows"] = 2

        self.helper = FormHelper()
        self.helper.html5_required = True
        self.helper.form_id = "talk-feedback-form"
        self.helper.form_method = "post"
        self.helper.form_action = reverse(
            "talk_feedback",
            kwargs={"event": self.talk.event.slug, "slug": self.talk.slug},
        )
        self.helper.layout = Layout(
            Div(
                Field(
                    "score",
                    css_class="rating-loading",
                    data_size="xs",
                    wrapper_class="col-12",
                ),
                css_class="form-row",
            ),
            Div(Field("comment", wrapper_class="col-12"), css_class="form-row"),
            Div(
                Submit("submit", _("Submit your feedback")),
                css_class="col-12 text-center",
            ),
        )

    def clean_score(self):
        return max(0, min(self.cleaned_data["score"], 5))

    def save(self, commit=True):
        if self.instance.talk_id is None:
            self.instance.talk_id = self.talk.id
        if self.instance.attendee_id is None:
            self.instance.attendee_id = self.attendee.id
        return super().save(commit)
