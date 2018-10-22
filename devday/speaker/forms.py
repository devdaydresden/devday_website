from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout, Submit
from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from speaker.models import Speaker


def get_edit_speaker_layout(submit_text):
    return Layout(
        Div(
            Field('name', autofocus='autofocus',
                  wrapper_class='col-12 col-md-6'),
            Field('twitter_handle', wrapper_class='col-12 col-md-6'),
            css_class='form-row'
        ),
        Div(
            Field('phone', wrapper_class='col-12 col-md-6'),
            Field('shirt_size', wrapper_class='col-12 col-md-6'),
            css_class='form-row'
        ),
        Div(
            Field('position', wrapper_class='col-12 col-md-6'),
            Field('organization', wrapper_class='col-12 col-md-6'),
            css_class='form-row'
        ),
        Div(
            Field('video_permission', wrapper_class='col-12'),
            css_class='form-row'
        ),
        Div(
            Field('short_biography', wrapper_class='col-12'),
            css_class='form-row'
        ),
        Div(
            Div(
                Submit('submit', submit_text,
                       css_class='ml-0 btn btn-primary'),
                css_class='col-12'
            ),
            css_class='form-row'
        )
    )


class CreateSpeakerForm(forms.ModelForm):
    next = forms.CharField(widget=forms.HiddenInput, required=False)

    class Meta:
        model = Speaker
        fields = (
            'name', 'twitter_handle', 'phone', 'position',
            'organization', 'video_permission', 'short_biography',
            'shirt_size')
        widgets = {
            'short_biography': forms.Textarea({'rows': 3})
        }
        help_texts = {
            'name': _('How should we present your name to the audience?'),
            'short_biography': _(
                'Tell your audience who you are and what you want people to'
                ' know about you.')
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.html5_required = True
        self.helper.layout = get_edit_speaker_layout(_('Register as speaker'))
        self.helper.layout.insert(0, Field('next'))
        self.helper.layout.append(Div(
            HTML('<p class="text-info">{}</p>'.format(
                _('By registering as a speaker, I agree to be contacted by the'
                  ' Dev Day organizers about conference details and my talk'
                  ' submissions.')))))

    def save(self, commit=True):
        self.instance.user = self.user
        return super(CreateSpeakerForm, self).save(commit)


class EditSpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = (
            'name', 'twitter_handle', 'phone', 'position',
            'organization', 'video_permission', 'short_biography',
            'shirt_size')
        widgets = {
            'short_biography': forms.Textarea({'rows': 3})
        }
        help_texts = {
            'name': _('How should we present your name to the audience?'),
            'short_biography': _(
                'Tell your audience who you are and what you want people to'
                ' know about you.')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.html5_required = True
        self.helper.layout = get_edit_speaker_layout(
            _('Change your speaker details'))


class UserSpeakerPortraitForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ('portrait',)

    def __init__(self, instance, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse_lazy('upload_user_speaker_portrait')
        self.helper.form_id = 'profile-img-upload'
        self.fields['portrait'].label = ''
        self.helper.layout = Layout(
            Div(
                HTML(
                    '<img id="portrait-image" src="{0}img/speaker-dummy.png"'
                    ' alt="{1}">'.format(
                        settings.STATIC_URL, _('Speaker image'))),
                Field(
                    'portrait', css_class='sr-only', wrapper_class='col-12',
                    accept="image/*"
                ),
                css_class='label', title=_('Change your speaker profile'),
            ),
            Div(
                Div(
                    Submit('submit', _('Submit your portrait'),
                           css_class='btn btn-primary'),
                    HTML('<a href="{}" class="btn btn-secondary">{}</a>'.format(
                        reverse_lazy('user_speaker_profile'),
                        _('Skip upload'))),
                    css_class='col-12'
                ),
                css_class='form-row'
            ),
        )
