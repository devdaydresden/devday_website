from django.conf.urls import url

from talk.views import (
    CommitteeSpeakerDetails, CommitteeSubmitTalkComment,
    CommitteeTalkCommentDelete, CommitteeTalkDetails,
    CommitteeTalkOverview, CommitteeTalkVote,
    CommitteeTalkVoteClear)

urlpatterns = [
    # TODO: make committee URLs session aware
    url(r'^speaker/(?P<pk>\d+)/$', CommitteeSpeakerDetails.as_view(),
        name='speaker_details'),
    url(r'^talks/$', CommitteeTalkOverview.as_view(), name='talk_overview'),
    url(r'^talks/(?P<pk>\d+)/$', CommitteeTalkDetails.as_view(),
        name='talk_committee_details'),
    url(r'^talks/(?P<pk>\d+)/comment/$', CommitteeSubmitTalkComment.as_view(),
        name='talk_comment'),
    url(r'^talks/(?P<pk>\d+)/vote/$', CommitteeTalkVote.as_view(),
        name='talk_vote'),
    url(r'^talks/(?P<pk>\d+)/vote/clear/$', CommitteeTalkVoteClear.as_view(),
        name='talk_vote_clear'),
    url(r'^talks/(?P<pk>\d+)/delete_comment/$',
        CommitteeTalkCommentDelete.as_view(), name='delete_talk_comment'),
]
