# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve as serve_static

from attendee.views import (AttendeeCancelView, AttendeeProfileView,
                            AttendeeRegistrationView, RegisterSuccessView,
                            login_or_register_attendee_view, AttendeeDeleteView)
from devday.views import ImprintView, exception_test_view
from talk.views import (SpeakerProfileView, SpeakerListView, TalkDetails,
                        TalkListView, InfoBeamerXMLView, TalkVideoView, TalkListPreviewView, RedirectVideoView)

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^sitemap\.xml$', sitemap_view, {'sitemaps': {'cmspages': CMSSitemap}}),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^attendee/register/$', AttendeeRegistrationView.as_view(), name='registration_register'),
    url(r'^attendee/cancel/(?P<event>\d+)$', AttendeeCancelView.as_view(), name='attendee_cancel'),
    url(r'^register/$', login_or_register_attendee_view, name='login_or_register_attendee'),
    url(r'^register/success/$', RegisterSuccessView.as_view(), name='register_success'),
    url(r'^accounts/', include('devday.registration_urls')),
    url(r'^accounts/delete/$', AttendeeDeleteView.as_view(), name='attendee_delete'),
    url(r'^accounts/profile/$', AttendeeProfileView.as_view(), name='user_profile'),
    url(r'^speakers/$', SpeakerListView.as_view(), name='speaker_list'),
    url(r'^schedule\.xml$', InfoBeamerXMLView.as_view()),
    url(r'^(?P<event>[^/]+)/schedule\.xml$', InfoBeamerXMLView.as_view()),
    url(r'^videos/$', RedirectVideoView.as_view()),
    url(r'^speaker/profile/(?P<pk>\d+)/$', SpeakerProfileView.as_view(), name='speaker_profile'),
    url(r'^upload/', include('django_file_form.urls')),
    url(r'^session/', include('talk.urls')),
    url(r'^committee/', include('talk.urls_committee')),
    url(r'^imprint/$', ImprintView.as_view(), name='imprint'),
    url(r'^synthetic_server_error/$', exception_test_view),
    url(r'^(?P<event>[^/]+)/talk-preview/$', TalkListPreviewView.as_view(), name='session_list_preview'),
    url(r'^(?P<event>[^/]+)/talk/$', TalkListView.as_view(), name='session_list'),
    url(r'^(?P<event>[^/]+)/videos/$', TalkVideoView.as_view(), name='video_list'),
    url(r'^(?P<event>[^/]+)/talk/((?P<slug>[-\w]+)/)*(?P<pk>\d+)', TalkDetails.as_view(), name='talk_details'),
    url(r'^', include('cms.urls')),
    url(r'^csvviews/', include('attendee.csv_urls')),
]

# This is only needed when using runserver.
if settings.DEBUG:  # pragma: nocover
    import debug_toolbar

    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),
                      url(r'^media/(?P<path>.*)$', serve_static,  # NOQA
                          {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                  ] + staticfiles_urlpatterns() + urlpatterns  # NOQA
