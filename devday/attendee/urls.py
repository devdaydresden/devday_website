from django.conf.urls import url

from attendee.views import (
    AttendeeCancelView, AttendeeRegistrationView, CheckInAttendeeQRView,
    CheckInAttendeeUrlView, CheckInAttendeeView, DevDayUserDeleteView,
    DevDayUserProfileView, LoginOrRegisterAttendeeView,
    DevDayUserRegistrationView, DevDayUserActivationView,
    AttendeeActivationView, AttendeeRegisterSuccessView)

urlpatterns = [
    url(r'^register/$',
        DevDayUserRegistrationView.as_view(),
        name='registration_register'),
    url(r'^(?P<event>[^/]+)/attendee/join/$',
        LoginOrRegisterAttendeeView.as_view(),
        name='login_or_register_attendee'),
    url(r'^(?P<event>[^/]+)/attendee/register/$',
        AttendeeRegistrationView.as_view(), name='attendee_registration'),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(r'^activate/(?P<activation_key>[-:\w]+)/$',
        DevDayUserActivationView.as_view(),
        name='devdayuser_activate'),
    url(r'^(?P<event>[^/]+)/attendee/activate/(?P<activation_key>[-:\w]+)/$',
        AttendeeActivationView.as_view(),
        name='attendee_activate'),
    url(r'^(?P<event>[^/]+)/attendee/register/success/$',
        AttendeeRegisterSuccessView.as_view(),
        name='attendee_register_success'),
    url(r'^(?P<event>[^/]+)/attendee/qrcode/$',
        CheckInAttendeeQRView.as_view(), name='attendee_checkin_qrcode'),
    url(r'^(?P<event>[^/]+)/attendee/cancel/$',
        AttendeeCancelView.as_view(), name='attendee_cancel'),
    url(r'^(?P<event>[^/]+)/attendee/checkin/$',
        CheckInAttendeeView.as_view(), name='attendee_checkin'),
    url(r'^(?P<event>[^/]+)/ac/(?P<id>[^/]+)/(?P<verification>[^/]+)/$',
        CheckInAttendeeUrlView.as_view(), name='attendee_checkin_url'),
    url(r'^accounts/delete/$',
        DevDayUserDeleteView.as_view(), name='attendee_delete'),
    url(r'^accounts/profile/$',
        DevDayUserProfileView.as_view(), name='user_profile'),
]
