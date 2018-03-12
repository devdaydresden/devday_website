from django.conf.urls import url

from .views import InactiveAttendeeView, ContactableAttendeeView, AttendeeListView

urlpatterns = [
    url(r'^inactive', InactiveAttendeeView.as_view()),
    url(r'^maycontact', ContactableAttendeeView.as_view()),
    url(r'^attendees', AttendeeListView.as_view()),
]
