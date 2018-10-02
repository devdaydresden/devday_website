from __future__ import unicode_literals

import logging
import hashlib
import os
import random
from mimetypes import MimeTypes

from PIL import Image
from PIL import ImageOps
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from six import BytesIO

from attendee.models import Attendee
from devday.extras import ValidatedImageField
from event.models import Event

T_SHIRT_SIZES = (
    (1, _("XS")),
    (2, _("S")),
    (3, _("M")),
    (4, _("L")),
    (5, _("XL")),
    (6, _("XXL")),
    (7, _("XXXL")),
)

log = logging.getLogger(__name__)


@python_2_unicode_compatible
class Speaker(models.Model):
    user = models.OneToOneField(Attendee, related_name="speaker")
    shirt_size = models\
        .PositiveSmallIntegerField(verbose_name=_("T-shirt size"),
                                   choices=T_SHIRT_SIZES)
    videopermission = models.BooleanField(
        verbose_name=_("Video permitted"),
        help_text=_("I hereby agree that audio and visual recordings of "
                    "me and my session can be published on the social media "
                    "channels of the event organizer and the website "
                    "devday.de.")
    )
    shortbio = models.TextField(verbose_name=_("Short biography"))
    portrait = ValidatedImageField(verbose_name=_("Speaker image"),
                                   upload_to='speakers')
    thumbnail = models.ImageField(
        verbose_name=_("Speaker image thumbnail"),
        upload_to='speaker_thumbs',
        max_length=500, null=True, blank=True)
    public_image = models.ImageField(
        verbose_name=_("Public speaker image"),
        upload_to='speaker_public',
        max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")

    def __str__(self):
        return "%s" % self.user

    def _get_pil_type_and_extension(self):
        mime = MimeTypes()
        django_type = mime.guess_type(self.portrait.name)[0]

        if django_type == 'image/jpeg':
            return 'jpeg', 'jpg', django_type
        elif django_type == 'image/png':
            return 'png', 'png', django_type
        raise ValueError("unsupported file type")

    def create_public_image(self):
        """
        This method creates a public version of the speaker image for display on the speaker lineup page. Speaker
        images with inappropriate aspect ratio may be cropped unfavourably.
        """
        if not self.portrait:
            return

        public_image_width = settings.TALK_PUBLIC_SPEAKER_IMAGE_WIDTH
        public_image_height = settings.TALK_PUBLIC_SPEAKER_IMAGE_HEIGHT
        pil_type, file_extension, django_type = self._get_pil_type_and_extension()

        self.portrait.seek(0)
        image = Image.open(BytesIO(self.portrait.read()))
        scaled = ImageOps.fit(image, (public_image_width, public_image_height))

        temp_handle = BytesIO()
        scaled.save(temp_handle, pil_type)
        temp_handle.seek(0)

        suf = SimpleUploadedFile(os.path.split(self.portrait.name)[-1],
                                 temp_handle.read(), content_type=django_type)
        self.public_image.save("%s_public.%s" % (os.path.splitext(suf.name)[0], file_extension), suf, save=False)

    def create_thumbnail(self):
        if not self.portrait:
            return

        thumbnail_height = settings.TALK_THUMBNAIL_HEIGHT
        pil_type, file_extension, django_type = self._get_pil_type_and_extension()

        self.portrait.seek(0)
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
        try:
            self.create_thumbnail()
            self.create_public_image()
        except ValueError:
            log.debug("unsupported image type for speaker portrait")
        force_update = False
        if self.id:
            force_update = True
        super(Speaker, self).save(force_update=force_update, **kwargs)


@python_2_unicode_compatible
class Track(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False)
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')
        ordering = ['name']
        unique_together = ('name', 'event')

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


@python_2_unicode_compatible
class Talk(models.Model):
    speaker = models.ForeignKey(Speaker)
    title = models.CharField(verbose_name=_('Session title'), max_length=255)
    slug = models.SlugField(verbose_name=_('Slug'))
    abstract = models.TextField(verbose_name=_('Abstract'))
    remarks = models.TextField(verbose_name=_('Remarks'), blank=True)
    track = models.ForeignKey(Track, null=True, blank=True)
    talkformat = models.ManyToManyField('TalkFormat',
                                        verbose_name=_('Talk Formats'))

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ['title']

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.slug is None or self.slug.strip() == '':
            self.slug = slugify(self.title)
        super(Talk, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return "%s - %s" % (self.speaker, self.title)


class TalkMedia(models.Model):
    talk = models.OneToOneField(Talk, related_name='media')
    youtube = models.CharField(verbose_name=_("Youtube video id"), max_length=64, blank=True)
    slideshare = models.CharField(verbose_name=_("Slideshare id"), max_length=64, blank=True)
    codelink = models.CharField(verbose_name=_("Source code"), max_length=255, blank=True)


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


@python_2_unicode_compatible
class Room(TimeStampedModel):
    name = models.CharField(verbose_name=_('Name'), max_length=100, unique=True, blank=False)
    priority = models.PositiveSmallIntegerField(verbose_name=_('Priority'), default=0)
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)

    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['priority', 'name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class TimeSlot(TimeStampedModel):
    name = models.CharField(max_length=40, blank=False)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    text_body = models.TextField(blank=True, default="")
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)

    class Meta:
        verbose_name = _('Time slot')
        verbose_name_plural = _('Time slots')
        ordering = ['start_time', 'end_time', 'name']
        unique_together = ('name', 'event')

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


@python_2_unicode_compatible
class TalkSlot(TimeStampedModel):
    talk = models.OneToOneField(Talk)
    room = models.ForeignKey(Room)
    time = models.ForeignKey(TimeSlot)

    class Meta:
        unique_together = (('room', 'time'),)

    def __str__(self):
        return "{} {}".format(self.room, self.time)


@python_2_unicode_compatible
class TalkFormat(models.Model):
    name = models.CharField(max_length=40, blank=False)
    duration = models.PositiveSmallIntegerField(verbose_name=_('Duration'),
                                                default=60)

    class Meta:
        unique_together = (('name', 'duration'),)
        verbose_name = _('Talk Format')
        verbose_name_plural = _('Talk Format')

    def __str__(self):
        h, m = divmod(self.duration, 60)
        return '{} ({:d}:{:02d}h)'.format(self.name, h, m)
