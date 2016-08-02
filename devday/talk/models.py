from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext as _
from attendee.models import Attendee


class Speaker(models.Model):
    user = models.ForeignKey(Attendee)
    videopermission = models.BooleanField(verbose_name=_("Video permitted"))
    shortbio = models.TextField(verbose_name=_("Short biography"))
    portrait = models.ImageField(verbose_name=_("Speaker image"), upload_to='speakers')

    class Meta:
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")


class Talk(models.Model):
    speaker = models.ForeignKey(Speaker)
    title = models.CharField(verbose_name=_("Session title"), max_length=255)
    abstract = models.TextField(verbose_name=_("Abstract"))

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")