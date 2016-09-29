from __future__ import unicode_literals

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView, UpdateView
from django_file_form.forms import ExistingFile
from django_file_form.uploader import FileFormUploader
from django.utils.translation import ugettext_lazy as _
from pathlib import Path
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from talk.forms import CreateTalkWithSpeakerForm, CreateTalkForSpeakerForm, \
    CreateTalkForUserForm, ExistingFileForm
from talk.models import Speaker, Talk

User = get_user_model()


class TalkSubmittedView(TemplateView):
    template_name = "talk/submitted.html"


class CreateTalkWithSpeakerView(RegistrationView):
    template_name = "talk/create_talk.html"
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_classes = {
        'anonymous': CreateTalkWithSpeakerForm,
        'user': CreateTalkForUserForm,
        'attendee': CreateTalkForUserForm,
        'speaker': CreateTalkForSpeakerForm,
    }

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            try:
                attendee = user.attendee
                try:
                    # noinspection PyStatementEffect
                    attendee.speaker
                    self.auth_level = 'speaker'
                except Speaker.DoesNotExist:
                    self.auth_level = 'attendee'
            except Attendee.DoesNotExist:
                self.auth_level = 'user'
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(CreateTalkWithSpeakerView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return self.form_classes.get(self.auth_level, None)

    def get_success_url(self, **kwargs):
        return 'talk_submitted'

    def form_valid(self, form):
        if self.auth_level == 'anonymous':
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['firstname']
            last_name = form.cleaned_data['lastname']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email, first_name=first_name, last_name=last_name, is_active=False)
                user.set_password(form.cleaned_data['password1'])
                signals.user_registered.send(sender=self.__class__,
                                             user=user,
                                             request=self.request)
                self.send_activation_email(user)
        else:
            user = self.request.user

        if self.auth_level in ('user', 'anonymous'):
            user.first_name = form.cleaned_data['firstname']
            user.last_name = form.cleaned_data['lastname']
            user.save()
            try:
                attendee = Attendee.objects.get(user=user)
                attendee.shirt_size = form.attendeeform.instance.shirt_size
            except Attendee.DoesNotExist:
                attendee = Attendee.objects.create(user=user)
        else:
            attendee = user.attendee

        if self.auth_level in ('attendee', 'user', 'anonymous'):
            try:
                speaker = Speaker.objects.get(user=attendee)
                speaker.portrait = form.speakerform.instance.portrait
                speaker.shortbio = form.speakerform.instance.shortbio
                speaker.videopermission = form.speakerform.instance.videopermission
            except Speaker.DoesNotExist:
                speaker = form.speakerform.save(commit=False)
                speaker.user = attendee
            speaker.save()
            form.speakerform.delete_temporary_files()
        else:
            speaker = attendee.speaker

        talk = form.talkform.instance
        talk.speaker = speaker
        talk.save()

        return redirect(self.get_success_url())


class EditTalkView(LoginRequiredMixin, UpdateView):
    fields = ['title', 'abstract', 'remarks']

    def get_queryset(self):
        return Talk.objects.filter(speaker__user=self.request.user.attendee)

    def get_form(self, form_class=None):
        form = super(EditTalkView, self).get_form(form_class)
        form.helper = FormHelper()
        form.helper.layout = Layout(
            Div(
                "title",
                Field("abstract", rows=3),
                Field("remarks", rows=3),
                css_class="col-xs-12 col-sm-12 col-md-12 col-lg-6 col-lg-offset-3"
            ),
            Div(
                Submit('submit', _('Submit'), css_class="btn-default"),
                css_class="col-xs-12 col-sm-12 col-lg-6 col-lg-offset-3"
            )
        )
        return form

    def get_success_url(self):
        return reverse('speaker_profile')


class ExistingFileView(BaseFormView):
    form_class = ExistingFileForm

    def get_form_kwargs(self):
        form_kwargs = super(ExistingFileView, self).get_form_kwargs()

        speaker = Speaker.objects.get(id=self.kwargs['id'])

        if speaker.portrait:
            name = Path(speaker.portrait.name).name
            form_kwargs['initial'] = dict(
                uploaded_image=ExistingFile(name)
            )

        return form_kwargs


class SpeakerProfileView(LoginRequiredMixin, TemplateView):
    template_name = "talk/speaker_profile.html"

    def get(self, request, *args, **kwargs):
        try:
            self.get_context_data()
        except AttributeError:
            return redirect('/')
        return super(SpeakerProfileView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SpeakerProfileView, self).get_context_data(**kwargs)
        attendee = Attendee.objects.filter(user=self.request.user).select_related('speaker').get()
        context.update({
            'attendee': attendee,
            'speaker': attendee.speaker,
            'talks': attendee.speaker.talk_set.all(),
        })
        return context


handle_upload = FileFormUploader()
