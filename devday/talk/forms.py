from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django_file_form.forms import FileFormMixin, UploadedFileField

from registration.forms import RegistrationFormUniqueEmail

from devday.utils.forms import CombinedFormBase
from talk.models import Talk, Speaker

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Field, Submit

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
        speaker.portrait = self.cleaned_data['uploaded_image']
        result = super().save(commit)
        if commit:
            self.delete_temporary_files()
        return result


class ExistingFileForm(SpeakerForm):
    def get_upload_url(self):
        return reverse('talk_handle_upload')


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


class CreateTalkForSpeakerForm(CombinedFormBase):
    form_classes = [TalkForm]

    def __init__(self, *args, **kwargs):
        super(CreateTalkForSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'submit_session'
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'talk/form/field.html'
        self.helper.html5_required = True


class CreateTalkForUserForm(CombinedFormBase):
    form_classes = [SpeakerForm, TalkForm]

    def __init__(self, *args, **kwargs):
        super(CreateTalkForUserForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'submit_session'
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'talk/form/field.html'
        self.helper.html5_required = True

        self.helper.layout = Layout(
            "upload_url",
            "delete_url",
            "form_id",
            Div(
                "firstname",
                "lastname",
                "shirt_size",
                "shortbio",
                Field("videopermission", template="talk/form/videopermission-field.html"),
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-6"
            ),
            Div(
                Field("uploaded_image", template="talk/form/speakerportrait-field.html"),
                "title",
                "abstract",
                "remarks",
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-6"
            ),
            Div(
                Submit('submit', _('Submit'), css_class="btn-default"),
                css_class="col-xs-12 col-sm-12 col-lg-6 col-lg-offset-4"
            )
        )


class CreateTalkWithSpeakerForm(CombinedFormBase):
    form_classes = [DevDayRegistrationForm, SpeakerForm, TalkForm]

    def __init__(self, *args, **kwargs):
        super(CreateTalkWithSpeakerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'submit_session'
        self.helper.form_method = 'post'
        self.helper.form_id = 'create-talk-form'
        self.helper.field_template = 'talk/form/field.html'
        self.helper.html5_required = True
        self.fields['email'].help_text = None
        self.fields['email'].label = _('E-Mail')
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        self.helper.layout = Layout(
            "upload_url",
            "delete_url",
            "form_id",
            Div(
                "email",
                "firstname",
                "lastname",
                "password1",
                "password2",
                "shirt_size",
                Field("videopermission", template="talk/form/videopermission-field.html"),
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                Field("uploaded_image", template="talk/form/speakerportrait-field.html"),
                "shortbio",
                "title",
                "abstract",
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                "remarks",
                css_class="col-xs-12 col-sm-6 col-md-6 col-lg-4"
            ),
            Div(
                Submit('submit', _('Submit'), css_class="btn-default"),
                css_class="col-xs-12 col-sm-12 col-lg-6 col-lg-offset-4"
            )
        )
