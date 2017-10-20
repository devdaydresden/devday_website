from django.conf.urls import url

from talk.views import (
    CreateTalkView, TalkSubmittedView, handle_upload, ExistingFileView, CreateSpeakerView,
    submit_session_view,
    TalkDetails,
    SpeakerRegisteredView, CommitteeTalkOverview, CommitteeSpeakerDetails, CommitteeTalkDetails, CommitteeTalkVote, CommitteeSubmitTalkComment, CommitteeTalkVoteClear,
    CommitteeTalkCommentDelete, SpeakerTalkDetails, TalkSpeakerCommentDelete, SubmitTalkSpeakerComment, TalkSubmissionClosed,
    SpeakerPublic)

urlpatterns = [
    url(r'^submit-session/$', submit_session_view, name='submit_session'),
    url(r'^new-speaker/$', CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'^speaker-registered/$', SpeakerRegisteredView.as_view(), name='speaker_registered'),
    url(r'^submission-closed/$', TalkSubmissionClosed.as_view(), name='talk_submission_closed'),
    url(r'^create-session/$', CreateTalkView.as_view(), name='create_session'),
    url(r'^submitted/$', TalkSubmittedView.as_view(), name='talk_submitted'),
    url(r'^existing/(?P<id>\d+)/$', ExistingFileView.as_view(), name='talk_existing'),
    url(r'^handle_upload/$', handle_upload, name='talk_handle_upload'),
    url(r'^speaker/(?P<pk>\d+)/$', SpeakerPublic.as_view(), name='public_speaker_profile'),
    url(r'^speaker/talks/(?P<pk>\d+)/$', SpeakerTalkDetails.as_view(), name='speaker_talk_details'),
    url(r'^speaker/talks/(?P<pk>\d+)/comment/$', SubmitTalkSpeakerComment.as_view(), name='talk_speaker_comment'),
    url(r'^speaker/talks/delete_comment/(?P<pk>\d+)/$', TalkSpeakerCommentDelete.as_view(),
        name='delete_talk_speaker_comment'),
]
