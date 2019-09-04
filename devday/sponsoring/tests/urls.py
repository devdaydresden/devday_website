from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^accounts/", include("devday.registration_urls")),
    url(r"^sponsoring/", include("sponsoring.urls")),
    url(r"", include("cms.urls")),
]
