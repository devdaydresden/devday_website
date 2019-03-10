from django.conf.urls import url

from talk.views import (
    CreateTalkView, PrepareSubmitSessionView, SpeakerTalkDetails,
    SubmitTalkSpeakerComment, TalkSpeakerCommentDelete,
    TalkSubmissionClosed, TalkSubmittedView)

urlpatterns = [
    url(r'^(?P<event>[^/]+)/submit/$', CreateTalkView.as_view(),
        name='submit_session'),
    url(r'^(?P<event>[^/]+)/prepare-submit/$',
        PrepareSubmitSessionView.as_view(),
        name='prepare_submit_session'),
    url(r'^submission-closed/$', TalkSubmissionClosed.as_view(),
        name='talk_submission_closed'),
    url(r'^(?P<event>[^/]+)/create-session/$',
        CreateTalkView.as_view(), name='create_session'),
    url(r'^(?P<event>[^/]+)/submitted/$', TalkSubmittedView.as_view(),
        name='talk_submitted'),
    url(r'^speaker/talks/(?P<pk>\d+)/$', SpeakerTalkDetails.as_view(),
        name='speaker_talk_details'),
    url(r'^speaker/talks/(?P<pk>\d+)/comment/$',
        SubmitTalkSpeakerComment.as_view(), name='talk_speaker_comment'),
    url(r'^speaker/talks/delete_comment/(?P<pk>\d+)/$',
        TalkSpeakerCommentDelete.as_view(),
        name='delete_talk_speaker_comment'),
]
