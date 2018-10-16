from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _

from talk.models import Talk, TalkFormat, TalkComment, Vote

User = get_user_model()


class TalkForm(forms.models.ModelForm):
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
    def __init__(self, *args, **kwargs):
        self.speaker = kwargs.pop('speaker')
        self.event = kwargs.pop('event')
        super(CreateTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse_lazy(
            'submit_session', kwargs={'event': self.event.slug})
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True

        self.helper.layout = Layout(
            Div(
                Field("title", autofocus='autofocus'),
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                Field('talkformat'),
            ),
            Div(
                Div(
                    Submit('submit', _('Submit'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="form-group"
            )
        )

    def save(self, commit=True):
        self.instance.speaker = self.speaker
        return super(CreateTalkForm, self).save(commit=commit)


class EditTalkForm(TalkForm):
    def __init__(self, *args, **kwargs):
        super(EditTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Field(
                    "title", template='devday/form/field.html',
                    autofocus='autofocus'),
                Field("abstract", template='devday/form/field.html', rows=2),
                Field("remarks", template='devday/form/field.html', rows=2),
                Field('talkformat'),
                css_class="col-xs-12 col-sm-12 col-md-12 col-lg-8 offset-lg-2"
            ),
            Div(
                Div(
                    Submit('submit', _('Update session'),
                           css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="col-xs-12 col-sm-12 col-lg-8 offset-lg-2"
            )
        )


class TalkCommentForm(forms.models.ModelForm):
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
            'comment',
            Field('is_visible', template='talk/form/is_visible-field.html'),
            Submit('submit', _('Add comment'))
        )


class TalkSpeakerCommentForm(forms.models.ModelForm):
    class Meta:
        model = TalkComment
        fields = ['comment']

    def __init__(self, *args, **kwargs):
        super(TalkSpeakerCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs['rows'] = 2
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'talk_speaker_comment', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            'comment',
            Submit('submit', _('Add comment'))
        )


class TalkVoteForm(forms.models.ModelForm):
    class Meta:
        model = Vote
        fields = ["score"]
