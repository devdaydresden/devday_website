from django.shortcuts import redirect
from django.views.generic import FormView

from talk.forms import CreateTalkWithSpeakerForm


class CreateTalkWithSpeakerView(FormView):
    template_name = "create_talk_with_speaker.html"
    form_class = CreateTalkWithSpeakerForm

    def form_valid(self, form):
        # TODO: implement form processing
        return redirect(self.get_success_url())