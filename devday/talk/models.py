import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from attendee.models import Attendee
from event.models import Event
from speaker import models as speaker_models
from speaker.models import PublishedSpeaker

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
    draft_speaker = models.ForeignKey(
        speaker_models.Speaker, verbose_name=_('Speaker (draft)'), null=True,
        on_delete=models.SET_NULL, blank=True)
    published_speaker = models.ForeignKey(
        speaker_models.PublishedSpeaker, verbose_name=_('Speaker (public)'),
        null=True, blank=True, on_delete=models.CASCADE)
    submission_timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(verbose_name=_('Session title'), max_length=255)
    slug = models.SlugField(verbose_name=_('Slug'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'))
    remarks = models.TextField(verbose_name=_('Remarks'), blank=True)
    track = models.ForeignKey(Track, null=True, blank=True)
    talkformat = models.ManyToManyField(
        'TalkFormat', verbose_name=_('Talk Formats'))
    event = models.ForeignKey(
        Event, verbose_name=_('Event'), null=False, blank=False)

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ['title']

    def clean(self):
        super().clean()
        if not self.draft_speaker and not self.published_speaker:
            raise ValidationError(
                _('A draft speaker or a published speaker is required.'))

    def publish(self, track):
        self.track = track
        self.published_speaker = self.draft_speaker.publish(self.event)
        self.save()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Talk, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if self.published_speaker_id:
            return "{} - {}".format(self.published_speaker, self.title)
        else:
            return "{} - {}".format(self.draft_speaker, self.title)


class TalkMedia(models.Model):
    talk = models.OneToOneField(Talk, related_name='media')
    youtube = models.CharField(
        verbose_name=_("Youtube video id"), max_length=64, blank=True)
    slideshare = models.CharField(
        verbose_name=_("Slideshare id"), max_length=64, blank=True)
    codelink = models.CharField(
        verbose_name=_("Source code"), max_length=255, blank=True)


@python_2_unicode_compatible
class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    talk = models.ForeignKey(Talk)
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ['voter', 'talk']

    def __str__(self):
        return '{} voted {} for {} by {}'.format(
            self.voter, self.score, self.talk.title, self.talk.draft_speaker)


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
            self.commenter, self.comment, self.talk.title,
            self.talk.draft_speaker)


@python_2_unicode_compatible
class Room(TimeStampedModel):
    name = models.CharField(
        verbose_name=_('Name'), max_length=100, blank=False)
    priority = models.PositiveSmallIntegerField(
        verbose_name=_('Priority'), default=0)
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)

    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        ordering = ['event', 'priority', 'name']
        unique_together = (('name', 'event'),)

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
    duration = models.PositiveSmallIntegerField(
        verbose_name=_('Duration'), default=60)

    class Meta:
        unique_together = (('name', 'duration'),)
        verbose_name = _('Talk Format')
        verbose_name_plural = _('Talk Format')

    def __str__(self):
        h, m = divmod(self.duration, 60)
        return '{} ({:d}:{:02d}h)'.format(self.name, h, m)
