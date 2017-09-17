from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models.signals import post_migrate

from event.management import create_default_event


class EventsConfig(AppConfig):
    name = 'event'

    def ready(self):
        post_migrate.connect(create_default_event, sender=self)
