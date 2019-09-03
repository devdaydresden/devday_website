"""
URLconf for django_registration and activation, using django-django_registration's
HMAC activation workflow.

"""

from django.conf.urls import include, url
from django.views.generic.base import TemplateView

urlpatterns = [
    url(
        r"^activate/complete/$",
        TemplateView.as_view(
            template_name="django_registration/activation_complete.html"
        ),
        name="django_registration_activation_complete",
    ),
    url(
        r"^register/complete/$",
        TemplateView.as_view(
            template_name="django_registration/registration_complete.html"
        ),
        name="django_registration_complete",
    ),
    url(
        r"^register/closed/$",
        TemplateView.as_view(
            template_name="django_registration/registration_closed.html"
        ),
        name="django_registration_disallowed",
    ),
    url(r"", include("devday.auth_urls")),
]
