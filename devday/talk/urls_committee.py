from django.conf.urls import url

from talk.views import (
    CreateTalkView, TalkSubmittedView, handle_upload, ExistingFileView, CreateSpeakerView,
    submit_session_view,
    TalkDetails,
    SpeakerRegisteredView, CommitteeTalkOverview, CommitteeSpeakerDetails, CommitteeTalkDetails, CommitteeTalkVote, CommitteeSubmitTalkComment, CommitteeTalkVoteClear,
    CommitteeTalkCommentDelete, SpeakerTalkDetails, TalkSpeakerCommentDelete, SubmitTalkSpeakerComment, TalkSubmissionClosed,
    SpeakerPublic)

urlpatterns = [
    url(r'^speaker/(?P<pk>\d+)/$', CommitteeSpeakerDetails.as_view(), name='speaker_details'),
    url(r'^talks/$', CommitteeTalkOverview.as_view(), name='talk_overview'),
    url(r'^talks/(?P<pk>\d+)/$', CommitteeTalkDetails.as_view(), name='talk_details'),
    url(r'^talks/(?P<pk>\d+)/comment/$', CommitteeSubmitTalkComment.as_view(), name='talk_comment'),
    url(r'^talks/(?P<pk>\d+)/vote/$', CommitteeTalkVote.as_view(), name='talk_vote'),
    url(r'^talks/(?P<pk>\d+)/vote/clear/$', CommitteeTalkVoteClear.as_view(), name='talk_vote_clear'),
    url(r'^talks/(?P<pk>\d+)/delete_comment/$', CommitteeTalkCommentDelete.as_view(), name='delete_talk_comment'),
]
