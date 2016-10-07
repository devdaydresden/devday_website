from django.conf.urls import url

from talk.views import (
    CreateTalkView, TalkSubmittedView, handle_upload, ExistingFileView, EditTalkView, CreateSpeakerView,
    submit_session_view
)

urlpatterns = [
    url(r'^submit-session', submit_session_view, name='submit_session'),
    url(r'^new-speaker', CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'^create-session', CreateTalkView.as_view(), name='create_session'),
    url(r'^submitted', TalkSubmittedView.as_view(), name='talk_submitted'),
    url(r'^existing/(?P<id>\d+)$', ExistingFileView.as_view(), name='talk_existing'),
    url(r'^handle_upload$', handle_upload, name='talk_handle_upload'),
    url(r'^edit-session/(?P<pk>\d+)$', EditTalkView.as_view(), name='edit_session'),
]
