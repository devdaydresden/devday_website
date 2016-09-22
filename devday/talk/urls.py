from django.conf.urls import url

from talk.views import CreateTalkWithSpeakerView, TalkSubmittedView, handle_upload, ExistingFileView

urlpatterns = [
    url(r'^submit-session', CreateTalkWithSpeakerView.as_view(), name="submit_session"),
    url(r'^submitted', TalkSubmittedView.as_view(), name="talk_submitted"),
    url(r'^existing/(?P<id>\d+)$', ExistingFileView.as_view(), name='talk_existing'),
    url(r'^handle_upload$', handle_upload, name='talk_handle_upload'),
]
