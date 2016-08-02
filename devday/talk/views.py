from django.shortcuts import redirect
from django.views.generic import FormView
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from attendee.models import Attendee
from talk.forms import CreateTalkWithSpeakerForm
from talk.models import Speaker

User = get_user_model()


class TalkSubmittedView(TemplateView):
    template_name = "talk_submitted.html"


class CreateTalkWithSpeakerView(FormView):
    template_name = "create_talk_with_speaker.html"
    form_class = CreateTalkWithSpeakerForm
    success_url = 'talk_submitted'

    def form_valid(self, form):
        firstname = form.cleaned_data['firstname']
        lastname = form.cleaned_data['lastname']
        email = form.cleaned_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create_user(firstname=firstname, lastname=lastname, email=email)
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