from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AttendeeConfig(AppConfig):
    name = 'attendee'
    verbose_name = _('Attendee management')
