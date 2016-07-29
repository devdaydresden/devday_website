from django.conf.urls import url

from talk.views import CreateTalkWithSpeakerView

urlpatterns = [
    url('^submit-session', CreateTalkWithSpeakerView.as_view(), name="submit_session")
]