from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _


class Attendee(models.Model):
    """
    This is a model class for an attendee.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    shirt_size = models.PositiveSmallIntegerField(verbose_name=_("T-shirt size"))

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")