from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views.generic import TemplateView
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from talk.forms import CreateTalkWithSpeakerForm, CreateTalkForSpeakerForm, CreateTalkForAttendeeForm, \
    CreateTalkForUserForm
from talk.models import Speaker

User = get_user_model()


class TalkSubmittedView(TemplateView):
    template_name = "talk/submitted.html"


class CreateTalkWithSpeakerView(RegistrationView):
    template_name = "talk/create_with_speaker.html"
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_classes = {
        'anonymous': CreateTalkWithSpeakerForm,
        'user': CreateTalkForUserForm,
        'attendee': CreateTalkForAttendeeForm,
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
            firstname = form.cleaned_data['firstname']
            lastname = form.cleaned_data['lastname']
            email = form.cleaned_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=email, first_name=firstname, last_name=lastname, email=email, is_active=False)
                user.set_password(form.cleaned_data['password1'])
                signals.user_registered.send(sender=self.__class__,
                                             user=user,
                                             request=self.request)
                self.send_activation_email(user)
                user.save()
        else:
            user = self.request.user

        if self.auth_level in ('user', 'anonymous'):
            try:
                attendee = Attendee.objects.get(user=user)
                attendee.shirt_size = form.attendeeform.instance.shirt_size
            except Attendee.DoesNotExist:
                attendee = form.attendeeform.instance
                attendee.user = user
            attendee.save()
        else:
            attendee = user.attendee

        if self.auth_level in ('attendee', 'user', 'anonymous'):
            try:
                speaker = Speaker.objects.get(user=attendee)
                speaker.portrait = form.speakerform.instance.portrait
                speaker.shortbio = form.speakerform.instance.shortbio
                speaker.videopermission = form.speakerform.instance.videopermission
            except Speaker.DoesNotExist:
                speaker = form.speakerform.instance
                speaker.user = attendee
            speaker.save()
        else:
            speaker = attendee.speaker

        talk = form.talkform.instance
        talk.speaker = speaker
        talk.save()

        return redirect(self.get_success_url())
