from django.conf.urls import url

from talk.views import (
    CreateTalkView, TalkSubmittedView, handle_upload, ExistingFileView, EditTalkView, CreateSpeakerView,
    submit_session_view,
    SpeakerRegisteredView, TalkOverview, SpeakerDetails, TalkDetails)

urlpatterns = [
    url(r'^submit-session/$', submit_session_view, name='submit_session'),
    url(r'^new-speaker/$', CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'^speaker-registered/$', SpeakerRegisteredView.as_view(), name='speaker_registered'),
    url(r'^create-session/$', CreateTalkView.as_view(), name='create_session'),
    url(r'^submitted/$', TalkSubmittedView.as_view(), name='talk_submitted'),
    url(r'^existing/(?P<id>\d+)/$', ExistingFileView.as_view(), name='talk_existing'),
    url(r'^handle_upload/$', handle_upload, name='talk_handle_upload'),
    url(r'^edit-session/(?P<pk>\d+)/$', EditTalkView.as_view(), name='edit_session'),
    url(r'^committee/talks/$', TalkOverview.as_view(), name='talk_overview'),
    url(r'^committee/speaker/(?P<pk>\d+)/$', SpeakerDetails.as_view(), name='speaker_details'),
    url(r'^committee/talks/(?P<pk>\d+)/$', TalkDetails.as_view(), name='talk_details'),
]
