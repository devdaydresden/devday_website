# -*- coding: utf-8 -*-
from cms.sitemaps import CMSSitemap
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap as sitemap_view
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.views.static import serve as serve_static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from devday.views import SendEmailView, exception_test_view
from rest_framework import routers
from rest_framework.authtoken import views

from event.api_views import EventDetailViewSet
from speaker.api_views import SpeakerViewSet
from talk.api_views import SessionViewSet

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r"sessions", SessionViewSet)
router.register(r"speakers", SpeakerViewSet)
router.register(r"events", EventDetailViewSet)

urlpatterns = [
    url(r"^api/", include(router.urls)),
    url(
        r"^api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    url(
        r"^api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    url(r"^api/schema/", SpectacularAPIView.as_view(), name="schema"),
    url(r"^api-auth/", include("rest_framework.urls")),
    url(r"^api-token-auth/", views.obtain_auth_token),
    url(r"^admin/", admin.site.urls),
    url(r"^admin/send_email/$", SendEmailView.as_view(), name="send_email"),
    url(r"^sitemap\.xml$", sitemap_view, {"sitemaps": {"cmspages": CMSSitemap}}),
    url(r"^select2/", include("django_select2.urls")),
    url(r"", include("attendee.urls")),
    url(r"^accounts/", include("devday.registration_urls")),
    url(r"^upload/", include("django_file_form.urls")),
    url(r"^session/", include("talk.urls")),
    url(r"^committee/", include("talk.urls_committee")),
    url(r"^synthetic_server_error/$", exception_test_view),
    url(r"^", include("talk.urls_event")),
    url(r"^", include("speaker.urls")),
    url(r"^", include("cms.urls")),
    url(r"^csvviews/", include("attendee.csv_urls")),
    url(r"^csvviews/", include("talk.csv_urls")),
]

# This is only needed when using runserver.
if settings.DEBUG:  # pragma: no cover
    import debug_toolbar

    urlpatterns = (
        [
            url(r"^__debug__/", include(debug_toolbar.urls)),
            url(
                r"^media/(?P<path>.*)$",
                serve_static,
                {"document_root": settings.MEDIA_ROOT, "show_indexes": True},
            ),
        ]
        + staticfiles_urlpatterns()
        + urlpatterns
    )
