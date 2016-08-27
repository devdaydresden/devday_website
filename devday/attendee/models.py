from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


T_SHIRT_SIZES = (
    (1, _("XS")),
    (2, _("S")),
    (3, _("M")),
    (4, _("L")),
    (5, _("XL")),
    (6, _("XXL")),
    (7, _("XXXL")),
)


class Attendee(models.Model):
    """
    This is a model class for an attendee.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="attendee")
    shirt_size = models.PositiveSmallIntegerField(verbose_name=_("T-shirt size"), choices=T_SHIRT_SIZES)

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")

    def __str__(self):
        return self.user.get_full_name()