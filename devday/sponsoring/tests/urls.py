from django.contrib import admin
from django.conf.urls import url, include

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('devday.registration_urls')),
    url(r'^sponsoring/', include('sponsoring.urls')),
    url(r'', include('cms.urls')),
]