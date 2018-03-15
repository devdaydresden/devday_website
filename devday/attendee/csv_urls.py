from django.conf.urls import url

from .views import InactiveAttendeeView, ContactableAttendeeView, AttendeeListView

urlpatterns = [
    url(r'^inactive', InactiveAttendeeView.as_view(), name="admin_csv_inactive"),
    url(r'^maycontact', ContactableAttendeeView.as_view(), name="admin_csv_maycontact"),
    url(r'^attendees', AttendeeListView.as_view(), name="admin_csv_attendees"),
]
