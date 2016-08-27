from __future__ import print_function, unicode_literals

from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views.generic import TemplateView
from registration import signals
from registration.backends.hmac.views import RegistrationView

from attendee.models import Attendee
from talk.forms import CreateTalkWithSpeakerForm
from talk.models import Speaker

User = get_user_model()


class TalkSubmittedView(TemplateView):
    template_name = "talk/submitted.html"


class CreateTalkWithSpeakerView(RegistrationView):
    template_name = "talk/create_with_speaker.html"
    email_body_template = "talk/speaker_activation_email.txt"
    email_subject_template = "talk/speaker_activation_email_subject.txt"
    form_class = CreateTalkWithSpeakerForm

    def get_success_url(self):
        return 'talk_submitted'

    def form_valid(self, form):
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

        try:
            attendee = Attendee.objects.get(user=user)
            attendee.shirt_size = form.attendeeform.instance.shirt_size
        except Attendee.DoesNotExist:
            attendee = form.attendeeform.instance
            attendee.user = user
        attendee.save()

        try:
            speaker = Speaker.objects.get(user=attendee)
            speaker.portrait = form.speakerform.instance.portrait
            speaker.shortbio = form.speakerform.instance.shortbio
            speaker.videopermission = form.speakerform.instance.videopermission
        except Speaker.DoesNotExist:
            speaker = form.speakerform.instance
            speaker.user = attendee
        speaker.save()

        talk = form.talkform.instance
        talk.speaker = speaker
        talk.save()

        return redirect(self.get_success_url())