from django.conf.urls import url

from talk.views import (
    CreateTalkView, TalkSubmittedView, handle_upload, ExistingFileView, EditTalkView, CreateSpeakerView,
    submit_session_view,
    SpeakerRegisteredView, TalkOverview, SpeakerDetails, TalkDetails, TalkVote, SubmitTalkComment, TalkVoteClear,
    TalkCommentDelete, SpeakerTalkDetails, TalkSpeakerCommentDelete, SubmitTalkSpeakerComment)

urlpatterns = [
    url(r'^submit-session/$', submit_session_view, name='submit_session'),
    url(r'^new-speaker/$', CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'^speaker-registered/$', SpeakerRegisteredView.as_view(), name='speaker_registered'),
    url(r'^create-session/$', CreateTalkView.as_view(), name='create_session'),
    url(r'^submitted/$', TalkSubmittedView.as_view(), name='talk_submitted'),
    url(r'^existing/(?P<id>\d+)/$', ExistingFileView.as_view(), name='talk_existing'),
    url(r'^handle_upload/$', handle_upload, name='talk_handle_upload'),
    url(r'^edit-session/(?P<pk>\d+)/$', EditTalkView.as_view(), name='edit_session'),
    url(r'^speaker/talks/(?P<pk>\d+)/$', SpeakerTalkDetails.as_view(), name='speaker_talk_details'),
    url(r'^speaker/talks/(?P<pk>\d+)/comment/$', SubmitTalkSpeakerComment.as_view(), name='talk_speaker_comment'),
    url(r'^speaker/talks/delete_comment/(?P<pk>\d+)/$', TalkSpeakerCommentDelete.as_view(),
        name='delete_talk_speaker_comment'),
    url(r'^committee/talks/$', TalkOverview.as_view(), name='talk_overview'),
    url(r'^committee/speaker/(?P<pk>\d+)/$', SpeakerDetails.as_view(), name='speaker_details'),
    url(r'^committee/talks/(?P<pk>\d+)/$', TalkDetails.as_view(), name='talk_details'),
    url(r'^committee/talks/(?P<pk>\d+)/comment/$', SubmitTalkComment.as_view(), name='talk_comment'),
    url(r'^committee/talks/(?P<pk>\d+)/vote/$', TalkVote.as_view(), name='talk_vote'),
    url(r'^committee/talks/(?P<pk>\d+)/vote/clear/$', TalkVoteClear.as_view(), name='talk_vote_clear'),
    url(r'^committee/talks/delete_comment/(?P<pk>\d+)/$', TalkCommentDelete.as_view(), name='delete_talk_comment'),
]
