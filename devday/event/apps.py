from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _


class EventsConfig(AppConfig):
    name = 'event'

    verbose_name = _("Events")
