from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _

from event.management import create_default_event


class EventsConfig(AppConfig):
    name = 'event'

    verbose_name = _("Events")

    def ready(self):
        post_migrate.connect(create_default_event, sender=self)
