from django.conf.urls import url

from .views import InactiveAttendeeView

urlpatterns = [
    url(r'^inactive', InactiveAttendeeView.as_view()),
]
