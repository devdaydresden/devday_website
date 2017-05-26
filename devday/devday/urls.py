# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls import *  # NOQA
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve as serve_static

from attendee.views import AttendeeProfileView
from devday.views import ImprintView, exception_test_view
from talk.views import SpeakerProfileView, SpeakerListView, TalkListView, InfoBeamerXMLView, TalkVideoView

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),  # NOQA
    url(r'^sitemap\.xml$', sitemap_view,
        {'sitemaps': {'cmspages': CMSSitemap}}),
    url(r'^select2/', include('django_select2.urls')),
    url(r'^accounts/', include('devday.registration_urls')),
    url(r'^accounts/profile/$', AttendeeProfileView.as_view(), name='user_profile'),
    url(r'^speakers/$', SpeakerListView.as_view(), name='speaker_list'),
    url(r'^schedule/$', TalkListView.as_view(), name='session_list'),
    url(r'^schedule.xml$', InfoBeamerXMLView.as_view()),
    url(r'^videos/$', TalkVideoView.as_view(), name='video_list'),
    url(r'^speaker/profile/(?P<pk>\d+)/$', SpeakerProfileView.as_view(), name='speaker_profile'),
    url(r'^upload/', include('django_file_form.urls')),
    url(r'^session/', include('talk.urls')),
    url(r'^imprint/$', ImprintView.as_view(), name='imprint'),
    url(r'^synthetic_server_error/$', exception_test_view),
    url(r'^', include('cms.urls')),
]

# This is only needed when using runserver.
if settings.DEBUG:  # pragma: nocover
    import debug_toolbar

    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),
                      url(r'^media/(?P<path>.*)$', serve_static,  # NOQA
                          {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
                  ] + staticfiles_urlpatterns() + urlpatterns  # NOQA
