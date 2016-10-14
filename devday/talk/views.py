from __future__ import unicode_literals

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import BaseFormView, UpdateView, CreateView
from django_file_form.forms import ExistingFile
from django_file_form.uploader import FileFormUploader
from pathlib import Path
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from talk.forms import CreateTalkForm, ExistingFileForm, TalkAuthenticationForm, CreateSpeakerForm, BecomeSpeakerForm
from talk.models import Speaker, Talk

User = get_user_model()


def submit_session_view(request):
    """
    This view presents a choice of links for anonymous users.

    """
    template_name = 'talk/submit_session.html'

    if not request.user.is_anonymous():
        try:
            request.user.attendee and request.user.attendee.speaker
            return redirect(reverse('create_session'))
        except (Attendee.DoesNotExist, Speaker.DoesNotExist):
            pass

    return login(request, template_name=template_name, authentication_form=TalkAuthenticationForm)


class TalkSubmittedView(TemplateView):
    template_name = "talk/submitted.html"


class CreateTalkView(LoginRequiredMixin, CreateView):
    template_name = "talk/create_talk.html"
    form_class = CreateTalkForm
    success_url = reverse_lazy('talk_submitted')

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.attendee or not user.attendee.speaker:
            return HttpResponseBadRequest(_('Authenticated user must be a registered speaker'))
        return super(CreateTalkView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super(CreateTalkView, self).get_form_kwargs()
        form_kwargs['speaker'] = self.request.user.attendee.speaker
        return form_kwargs


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
                Field("abstract", rows=2),
                Field("remarks", rows=2),
                css_class="col-xs-12 col-sm-12 col-md-12 col-lg-8 col-lg-offset-2"
            ),
            Div(
                Div(
                    Submit('submit', _('Submit'), css_class="btn-default"),
                    css_class="text-center",
                ),
                css_class="col-xs-12 col-sm-12 col-lg-8 col-lg-offset-2"
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


class CreateSpeakerView(RegistrationView):
    template_name = 'talk/create_speaker.html'
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_classes = {
        'anonymous': CreateSpeakerForm,
        'user': BecomeSpeakerForm,
        'attendee': BecomeSpeakerForm,
    }
    success_url = reverse_lazy('create_session')

    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated():
            try:
                if user.attendee:
                    if user.attendee.speaker:
                        return redirect(self.success_url)
            except Speaker.DoesNotExist:
                self.auth_level = 'attendee'
            except Attendee.DoesNotExist:
                self.auth_level = 'user'
        else:
            # noinspection PyAttributeOutsideInit
            self.auth_level = 'anonymous'
        return super(CreateSpeakerView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        return self.form_classes.get(self.auth_level, None)

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

        speaker = form.save(commit=False)
        speaker.user = attendee
        speaker.save()
        form.delete_temporary_files()

        return redirect(self.success_url)
