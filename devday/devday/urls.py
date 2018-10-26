# -*- coding: utf-8 -*-
from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve as serve_static

from devday.views import exception_test_view, SendEmailView
from talk.views import (
    InfoBeamerXMLView, RedirectVideoView,
    TalkDetails, TalkListPreviewView, TalkListView, TalkVideoView)

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/send_email/$', SendEmailView.as_view(), name='send_email'),
    url(r'^sitemap\.xml$', sitemap_view,
        {'sitemaps': {'cmspages': CMSSitemap}}),
    url(r'^select2/', include('django_select2.urls')),
    url(r'', include('attendee.urls')),
    url(r'^accounts/', include('devday.registration_urls')),
    url(r'^schedule\.xml$', InfoBeamerXMLView.as_view()),
    url(r'^(?P<event>[^/]+)/schedule\.xml$', InfoBeamerXMLView.as_view(),
        name='infobeamer'),
    url(r'^videos/$', RedirectVideoView.as_view()),
    url(r'^upload/', include('django_file_form.urls')),
    url(r'^session/', include('talk.urls')),
    url(r'^committee/', include('talk.urls_committee')),
    url(r'^synthetic_server_error/$', exception_test_view),
    url(r'^(?P<event>[^/]+)/talk-preview/$', TalkListPreviewView.as_view(),
        name='session_list_preview'),
    url(r'^(?P<event>[^/]+)/talk/$', TalkListView.as_view(),
        name='session_list'),
    url(r'^(?P<event>[^/]+)/videos/$', TalkVideoView.as_view(),
        name='video_list'),
    url(r'^(?P<event>[^/]+)/talk/(?P<slug>[^/]+)/$', TalkDetails.as_view(),
        name='talk_details'),
    url(r'^', include('speaker.urls')),
    url(r'^', include('cms.urls')),
    url(r'^csvviews/', include('attendee.csv_urls')),
]

# This is only needed when using runserver.
if settings.DEBUG:  # pragma: no cover
    import debug_toolbar
    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),
                      url(r'^media/(?P<path>.*)$', serve_static,
                          {'document_root': settings.MEDIA_ROOT,
                           'show_indexes': True}),
                  ] + staticfiles_urlpatterns() + urlpatterns
