from __future__ import unicode_literals

from django.apps import apps, AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class AttendeeConfig(AppConfig):
    name = 'attendee'
    verbose_name = _('Attendee management')

    def ready(self):
        post_migrate.connect(set_default_event, sender=self)


def set_default_event(verbosity=2, **kwargs):
    Event = apps.get_model('event', 'Event')
    default_event = Event.current_event()

    Attendee = apps.get_model('attendee', 'Attendee')
    attendees = Attendee.objects.filter(event=None)
    if verbosity >= 2:
        print("Found %d attendees" % attendees.count())
    attendees.update(event=default_event)
