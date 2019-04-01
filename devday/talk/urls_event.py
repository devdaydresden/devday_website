from django.conf.urls import url
from django.views.generic import RedirectView

from talk.views import (
    AttendeeVotingView,
    InfoBeamerXMLView,
    RedirectVideoView,
    TalkDetails,
    TalkListPreviewView,
    TalkListView,
    TalkVideoView,
    AttendeeTalkVote,
    AttendeeTalkClearVote,
    TalkAddReservation,
    TalkCancelReservation,
    TalkConfirmReservation,
    TalkResendReservationConfirmation, TalkReservationConfirmationSent)


urlpatterns = [
    url(r"^schedule\.xml$", InfoBeamerXMLView.as_view()),
    url(
        r"^(?P<event>[^/]+)/schedule\.xml$",
        InfoBeamerXMLView.as_view(),
        name="infobeamer",
    ),
    url(r"^videos/$", RedirectVideoView.as_view()),
    url(
        r"^(?P<event>[^/]+)/talk-preview/$",
        TalkListPreviewView.as_view(),
        name="session_list_preview",
    ),
    url(r"^(?P<event>[^/]+)/sessions/$", TalkListView.as_view(), name="session_list"),
    url(
        r"^(?P<event>[^/]+)/talk/$",
        RedirectView.as_view(pattern_name="session_list"),
        name="session_list_legacy",
    ),
    url(r"^(?P<event>[^/]+)/videos/$", TalkVideoView.as_view(), name="video_list"),
    url(
        r"^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/$",
        TalkDetails.as_view(),
        name="talk_details",
    ),
    url(
        r"^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/reservation/$",
        TalkAddReservation.as_view(),
        name="talk_reservation",
    ),
    url(
        r"^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/resend-confirmation-mail/$",
        TalkResendReservationConfirmation.as_view(),
        name="talk_resend_confirmation",
    ),
    url(
        r"^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/confirmation-sent/$",
        TalkReservationConfirmationSent.as_view(),
        name="talk_reservation_confirmation_sent",
    ),
    url(
        r"^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/cancel-reservation/$",
        TalkCancelReservation.as_view(),
        name="talk_cancel_reservation",
    ),
    url(
        r"^(?P<event>[^/]+)/confirm-reservation/(?P<confirmation_key>[-:\w]+)/$",
        TalkConfirmReservation.as_view(),
        name="talk_confirm_reservation",
    ),
    url(
        r"^(?P<event>[^/]+)/voting/$",
        AttendeeVotingView.as_view(),
        name="attendee_voting",
    ),
    url(
        r"^(?P<event>[^/]+)/clear-vote/$",
        AttendeeTalkClearVote.as_view(),
        name="attendee_vote_clear",
    ),
    url(
        r"^(?P<event>[^/]+)/submit-vote/$",
        AttendeeTalkVote.as_view(),
        name="attendee_vote_change",
    ),
]
