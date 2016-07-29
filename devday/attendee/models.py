from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _, ugettext_lazy


T_SHIRT_SIZES = (
    (1, ugettext_lazy("XS")),
    (2, ugettext_lazy("S")),
    (3, ugettext_lazy("M")),
    (4, ugettext_lazy("L")),
    (5, ugettext_lazy("XL")),
    (6, ugettext_lazy("XXL")),
    (7, ugettext_lazy("XXXL")),
)


class Attendee(models.Model):
    """
    This is a model class for an attendee.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    shirt_size = models.PositiveSmallIntegerField(verbose_name=_("T-shirt size"), choices=T_SHIRT_SIZES)

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")