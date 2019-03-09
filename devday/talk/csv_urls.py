from django.conf.urls import url

from talk.views import EventSessionSummaryView

urlpatterns = [
    url(r'^session-summary', EventSessionSummaryView.as_view(),
        name='admin_csv_session_summary')
]