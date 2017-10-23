from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit, Hidden, HTML
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django_file_form.forms import FileFormMixin, UploadedFileField
from registration.forms import RegistrationFormUniqueEmail

from attendee.forms import DevDayUserForm
from devday.utils.forms import CombinedFormBase, DevDayFormHelper
from talk.models import Talk, Speaker, TalkComment, Vote

User = get_user_model()


class TalkForm(forms.models.ModelForm):
    class Meta:
        model = Talk
        fields = ["title", "abstract", "remarks"]
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 3}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
        }


class SpeakerForm(FileFormMixin, forms.models.ModelForm):
    uploaded_image = UploadedFileField(label=_("Speaker portrait"))

    class Meta:
        model = Speaker
        fields = ["shortbio", "videopermission", "shirt_size"]
        widgets = {
            'shortbio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(SpeakerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        speaker = self.instance
        assert hasattr(self, 'cleaned_data')
        speaker.portrait = self.cleaned_data.get('uploaded_image')
        result = super(SpeakerForm, self).save(commit)
        if commit:
            try:
                self.delete_temporary_files()
            except:
                pass
        return result


class ExistingFileForm(SpeakerForm):
    def get_upload_url(self):
        return reverse('talk_handle_upload')


class DevDayRegistrationForm(RegistrationFormUniqueEmail):
    phone = forms.fields.CharField(label=_("Phone"), max_length=32)
    twitter_handle = forms.fields.CharField(required=False)
    organization = forms.fields.CharField(required=False)
    position = forms.fields.CharField(required=False)

    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = [
            'email',
            'password1',
            'password2',
            'first_name',
            'last_name'
        ]

    def clean_accept_contact(self):
        value = self.cleaned_data.get('accept_contact')
        if not value:
            raise ValidationError(_('You need to agree to be contacted by us.'))
        return value

    def clean(self):
        if self.cleaned_data.get('email'):
            self.cleaned_data[User.USERNAME_FIELD] = self.cleaned_data.get('email')
        return super(RegistrationFormUniqueEmail, self).clean()


class CreateTalkForm(TalkForm):
    def __init__(self, *args, **kwargs):
        self.speaker = kwargs.pop('speaker')
        super(CreateTalkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'create_session'
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True

        self.helper.layout = Layout(
            Div(
                Field("title", template='devday/form/field.html', autofocus='autofocus'),
                "abstract",
                "remarks",
                css_class="col-md-12 col-lg-offset-2 col-lg-8"
            ),
            Div(
                Div(
                    Submit('submit', _('Submit'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="col-xs-12 col-sm-12 col-lg-8 col-lg-offset-2"
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
                Field("title", template='devday/form/field.html', autofocus='autofocus'),
                Field("abstract", template='devday/form/field.html', rows=2),
                Field("remarks", template='devday/form/field.html', rows=2),
                css_class="col-xs-12 col-sm-12 col-md-12 col-lg-8 col-lg-offset-2"
            ),
            Div(
                Div(
                    Submit('submit', _('Update session'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="col-xs-12 col-sm-12 col-lg-8 col-lg-offset-2"
            )
        )


class TalkAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(TalkAuthenticationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'submit_session'
        self.helper.form_method = 'post'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                Hidden('next', value=reverse('submit_session')),
                Field('username', template='devday/form/field.html', autofocus='autofocus'),
                Field('password', template='devday/form/field.html'),
            ),
            Div(
                Submit('submit', _('Login'), css_class='btn-default'),
                css_class='text-center'
            )
        )


class BecomeSpeakerForm(CombinedFormBase):
    form_classes = [DevDayUserForm, SpeakerForm]

    def __init__(self, *args, **kwargs):
        self.form_models = {}
        m = kwargs.pop('devdayuserform_model')
        if m:
            self.form_models['devdayuserform'] = {
                'args': [],
                'kwargs': {
                    'instance': m
                }
            }
        super(BecomeSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'create_speaker'
        self.helper.form_method = 'post'
        self.helper.form_id = 'create-speaker-form'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            "upload_url",
            "delete_url",
            "form_id",
            Div(
                Field("first_name", template='devday/form/field.html', autofocus='autofocus'),
                "last_name",
                "phone",
                "twitter_handle",
                "position",
                "organization",
                css_class="col-lg-offset-2 col-lg-4 col-md-6 col-sm-12",
            ),
            Div(
                Field("uploaded_image", template="talk/form/speakerportrait-field.html"),
                Field("shortbio", rows=2, template="devday/form/field.html"),
                "shirt_size",
                Field("videopermission", template="talk/form/videopermission-field.html"),
                Div(
                    HTML(_('<label><p class="help-block">By registering as a speaker, I agree to be contacted by the DevDay organizers about conference details and my talk submissions.</p></label>')),
                    css_class='checkbox'
                ),
                css_class="col-lg-4 col-md-6 col-sm-12",
            ),
            Div(
                Submit('submit', _('Register as speaker')),
                css_class="col-lg-offset-2 col-lg-8 col-md-12 text-center"
            )
        )


class EditSpeakerForm(forms.models.ModelForm):
    class Meta:
        model = Speaker
        fields = ['shortbio', 'videopermission', 'shirt_size']

    def __init__(self, *args, **kwargs):
        super(EditSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = DevDayFormHelper()
        self.helper.form_action = reverse('speaker_profile', kwargs={'pk': self.instance.pk})
        self.helper.form_method = 'post'
        self.helper.html5_required = True
        self.helper.layout = Layout(
            Div(
                "shortbio",
                Field("videopermission", template="talk/form/videopermission-field.html"),
                "shirt_size",
                css_class="col-lg-offset-1 col-lg-10 col-md-12"
            ),
            Div(
                Submit('submit', _('Update your speaker information')),
                css_class="col-lg-offset-1 col-lg-10 col-md-12 text-center"
            )
        )


class CreateSpeakerForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, SpeakerForm]

    def __init__(self, *args, **kwargs):
        self.form_models = {}
        m = kwargs.pop('devdayuserform_model')
        super(CreateSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'create_speaker'
        self.helper.form_method = 'post'
        self.helper.form_id = 'create-speaker-form'
        self.helper.field_template = 'devday/form/field.html'
        self.helper.html5_required = True
        self.fields['email'].help_text = None
        self.fields['email'].label = _('E-Mail')
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        self.helper.layout = Layout(
            'upload_url',
            'delete_url',
            'form_id',
            Div(
                Field('email', template='devday/form/field.html', autofocus='autofocus'),
                'first_name',
                'last_name',
                'password1',
                'password2',
                'phone',
                'twitter_handle',
                'organization',
                'position',
                css_class='col-md-12 col-lg-offset-2 col-lg-4'
            ),
            Div(
                Field('uploaded_image', template='talk/form/speakerportrait-field.html'),
                'shirt_size',
                Field('shortbio', rows=2, template='devday/form/field.html'),
                Div(
                    HTML(_('<label><p class="help-block">By registering as a speaker, I agree to be contacted by the DevDay organizers about conference details and my talk submissions.</p></label>')),
                    css_class='checkbox'
                ),
                Field('videopermission', template='talk/form/videopermission-field.html'),
                css_class='col-md-12 col-lg-4'
            ),
            Div(
                Submit('submit', _('Register as speaker')),
                css_class='col-md-12 col-lg-offset-2 col-lg-8 text-center'
            )
        )


class TalkCommentForm(forms.models.ModelForm):
    class Meta:
        model = TalkComment
        fields = ['comment', 'is_visible']

    def __init__(self, *args, **kwargs):
        super(TalkCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].widget.attrs['rows'] = 2
        self.helper = DevDayFormHelper()
        self.helper.form_action = reverse('talk_comment', kwargs={'pk': self.instance.pk})
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
        self.helper = DevDayFormHelper()
        self.helper.form_action = reverse('talk_speaker_comment', kwargs={'pk': self.instance.pk})
        self.helper.layout = Layout(
            'comment',
            Submit('submit', _('Add comment'))
        )


class TalkVoteForm(forms.models.ModelForm):
    class Meta:
        model = Vote
        fields = ["score"]
