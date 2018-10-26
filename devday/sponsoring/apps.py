from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SponsoringConfig(AppConfig):
    name = 'sponsoring'
    verbose_name = _('Sponsor Management')
