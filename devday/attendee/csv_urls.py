from django.conf.urls import url

from .views import InactiveAttendeeView, ContactableAttendeeView

urlpatterns = [
    url(r'^inactive', InactiveAttendeeView.as_view()),
    url(r'^maycontact', ContactableAttendeeView.as_view()),
]
