from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit, Hidden
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django_file_form.forms import FileFormMixin, UploadedFileField
from registration.forms import RegistrationFormUniqueEmail

from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker

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
    firstname = forms.fields.CharField(label=_("Firstname"), max_length=64)
    lastname = forms.fields.CharField(label=_("Lastname"), max_length=64)
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
    accept_contact = forms.BooleanField(
        label=_('Accept contact'),
        help_text=_(
            'I hereby agree to be contacted by the DevDay organization team '  # \
            'to get informed about future events and for requests related to '  # \
            'my session proposals.'),
        required=False,
    )

    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = [
            'email',
            'password1',
            'password2'
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
    form_classes = [SpeakerForm]

    def __init__(self, *args, **kwargs):
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
                Field("firstname", template='devday/form/field.html', autofocus='autofocus'),
                "lastname",
                "shirt_size",
                css_class="col-lg-offset-2 col-lg-4 col-md-6 col-sm-12",
            ),
            Div(
                Field("uploaded_image", template="talk/form/speakerportrait-field.html"),
                Field("shortbio", rows=2, template="devday/form/field.html"),
                Field("videopermission", template="talk/form/videopermission-field.html"),
                css_class="col-lg-4 col-md-6 col-sm-12",
            ),
            Div(
                Submit('submit', _('Register as speaker')),
                css_class="col-lg-offset-2 col-lg-8 col-md-12 text-center"
            )
        )


class CreateSpeakerForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, SpeakerForm]

    def __init__(self, *args, **kwargs):
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
                'firstname',
                'lastname',
                'password1',
                'password2',
                css_class='col-md-12 col-lg-offset-2 col-lg-4'
            ),
            Div(
                Field('uploaded_image', template='talk/form/speakerportrait-field.html'),
                'shirt_size',
                Field('shortbio', rows=2, template='devday/form/field.html'),
                Field('videopermission', template='talk/form/videopermission-field.html'),
                Field('accept_contact', template='devday/form/accept_contact-field.html'),
                css_class='col-md-12 col-lg-4'
            ),
            Div(
                Submit('submit', _('Register as speaker')),
                css_class='col-md-12 col-lg-offset-2 col-lg-8 text-center'
            )
        )
