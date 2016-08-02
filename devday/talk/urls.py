from django.conf.urls import url

from talk.views import CreateTalkWithSpeakerView, TalkSubmittedView

urlpatterns = [
    url('^submit-session', CreateTalkWithSpeakerView.as_view(), name="submit_session"),
    url('^submitted', TalkSubmittedView.as_view(), name="talk_submitted")
]