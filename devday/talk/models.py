from __future__ import unicode_literals

import os
from mimetypes import MimeTypes

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from six import BytesIO

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


@python_2_unicode_compatible
class Speaker(models.Model):
    user = models.OneToOneField(Attendee, related_name="speaker")
    shirt_size = models.PositiveSmallIntegerField(verbose_name=_("T-shirt size"), choices=T_SHIRT_SIZES)
    videopermission = models.BooleanField(
        verbose_name=_("Video permitted"),
        help_text=_("I hereby agree that audio and visual recordings of "  # \
                    "me and my session can be published on the social media "  # \
                    "channels of the event organizer and the website "  # \
                    "devday.de.")
    )
    shortbio = models.TextField(verbose_name=_("Short biography"))
    portrait = models.ImageField(verbose_name=_("Speaker image"), upload_to='speakers')
    thumbnail = models.ImageField(
        verbose_name=_("Speaker image thumbnail"), upload_to='speaker_thumbs',
        max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")

    def __str__(self):
        return "%s" % self.user

    def create_thumbnail(self):
        if not self.portrait:
            return

        thumbnail_height = settings.TALK_THUMBNAIL_HEIGHT

        mime = MimeTypes()
        django_type = mime.guess_type(self.portrait.name)[0]

        if django_type == 'image/jpeg':
            pil_type = 'jpeg'
            file_extension = 'jpg'
        elif django_type == 'image/png':
            pil_type = 'png'
            file_extension = 'png'
        else:
            return

        image = Image.open(BytesIO(self.portrait.read()))
        thumbnail_size = (int(thumbnail_height * image.width / image.height), thumbnail_height)
        image.thumbnail(thumbnail_size, Image.ANTIALIAS)

        temp_handle = BytesIO()
        image.save(temp_handle, pil_type)
        temp_handle.seek(0)

        suf = SimpleUploadedFile(os.path.split(self.portrait.name)[-1],
                                 temp_handle.read(), content_type=django_type)
        self.thumbnail.save("%s_thumbnail.%s" % (os.path.splitext(suf.name)[0], file_extension), suf, save=False)

    def save(self, **kwargs):
        self.create_thumbnail()
        force_update = False
        if self.id:
            force_update = True
        super(Speaker, self).save(force_update=force_update, **kwargs)


@python_2_unicode_compatible
class Talk(models.Model):
    speaker = models.ForeignKey(Speaker)
    title = models.CharField(verbose_name=_("Session title"), max_length=255)
    abstract = models.TextField(verbose_name=_("Abstract"))
    remarks = models.TextField(verbose_name=_("Remarks"), blank=True)

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")

    def __str__(self):
        return "%s - %s" % (self.speaker, self.title)


@python_2_unicode_compatible
class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    talk = models.ForeignKey(Talk)
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ['voter', 'talk']

    def __str__(self):
        return '{} voted {} for {} by {}'.format(
            self.voter, self.score, self.talk.title, self.talk.speaker)


@python_2_unicode_compatible
class TalkComment(TimeStampedModel):
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL)
    talk = models.ForeignKey(Talk)
    comment = models.TextField(verbose_name=_('Comment'))
    is_visible = models.BooleanField(
        verbose_name=_('Visible for Speaker'),
        default=False,
        help_text=_('Indicates whether the comment is visible to the speaker.'))

    def __str__(self):
        return '{} commented {} for {} by {}'.format(
            self.commenter, self.comment, self.talk.title, self.talk.speaker)
