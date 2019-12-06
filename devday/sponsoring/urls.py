from django.conf.urls import url

from sponsoring.views import (
    RedirectToCurrentEventView,
    SponsoringThanksView,
    SponsoringView,
)

urlpatterns = [
    url(r"thanks/", SponsoringThanksView.as_view(), name="sponsoring_thanks"),
    url(r"(?P<event>[^/]+)/", SponsoringView.as_view(), name="sponsoring_view"),
    url(r"", RedirectToCurrentEventView.as_view()),
]
