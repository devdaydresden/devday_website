from django.conf.urls import url

from attendee.views import (
    AttendeeCancelView, AttendeeRegistrationView, CheckInAttendeeQRView,
    CheckInAttendeeUrlView, CheckInAttendeeView, DevDayUserDeleteView,
    DevDayUserProfileView, LoginOrRegisterAttendeeView, RegisterSuccessView,
    DevDayUserRegistrationView)

urlpatterns = [
    url(r'^register/$',
        DevDayUserRegistrationView.as_view(),
        name='registration_register'),
    url(r'^(?P<event>[^/]+)/attendee/join/$',
        LoginOrRegisterAttendeeView.as_view(),
        name='login_or_register_attendee'),
    url(r'^(?P<event>[^/]+)/attendee/register/$',
        AttendeeRegistrationView.as_view(), name='attendee_registration'),
    url(r'^(?P<event>[^/]+)/attendee/qrcode/$',
        CheckInAttendeeQRView.as_view(), name='attendee_checkin_qrcode'),
    url(r'^(?P<event>[^/]+)/attendee/cancel/$',
        AttendeeCancelView.as_view(), name='attendee_cancel'),
    url(r'^(?P<event>[^/]+)/attendee/checkin/$',
        CheckInAttendeeView.as_view(), name='attendee_checkin'),
    url(r'^(?P<event>[^/]+)/ac/(?P<id>[^/]+)/(?P<verification>[^/]+)/$',
        CheckInAttendeeUrlView.as_view(), name='attendee_checkin_url'),
    url(r'^(?P<event>[^/]+)/attendee/register/success/$',
        RegisterSuccessView.as_view(), name='register_success'),
    url(r'^accounts/delete/$',
        DevDayUserDeleteView.as_view(), name='attendee_delete'),
    url(r'^accounts/profile/$',
        DevDayUserProfileView.as_view(), name='user_profile'),
]
