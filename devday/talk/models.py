from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from attendee.models import Attendee

T_SHIRT_SIZES = (
    (1, _("XS")),
    (2, _("S")),
    (3, _("M")),
    (4, _("L")),
    (5, _("XL")),
    (6, _("XXL")),
    (7, _("XXXL")),
)


class Speaker(models.Model):
    user = models.OneToOneField(Attendee, related_name="speaker")
    shirt_size = models.PositiveSmallIntegerField(verbose_name=_("T-shirt size"), choices=T_SHIRT_SIZES)
    videopermission = models.BooleanField(
        verbose_name=_("Video permitted"),
        help_text=_("I hereby agree that audio and visual recordings of "
                    "me and my session can be published on the social media "
                    "channels of the event organizer and the website "
                    "devday.de.")
    )
    shortbio = models.TextField(verbose_name=_("Short biography"))
    portrait = models.ImageField(verbose_name=_("Speaker image"), upload_to='speakers')

    class Meta:
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")

    def __str__(self):
        return str(self.user)


class Talk(models.Model):
    speaker = models.ForeignKey(Speaker)
    title = models.CharField(verbose_name=_("Session title"), max_length=255)
    abstract = models.TextField(verbose_name=_("Abstract"))
    remarks = models.TextField(verbose_name=_("Remarks"), blank=True)

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

    def __str__(self):
        return "%s - %s" % (str(self.speaker), self.title)
