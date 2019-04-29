import logging
from datetime import timedelta

from attendee.models import Attendee
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from event.models import Event
from model_utils.models import TimeStampedModel
from psqlextra.manager import PostgresManager
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
        verbose_name = _("Track")
        verbose_name_plural = _("Tracks")
        ordering = ["name"]
        unique_together = ("name", "event")

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


@python_2_unicode_compatible
class Talk(models.Model):
    draft_speaker = models.ForeignKey(
        speaker_models.Speaker,
        verbose_name=_("Speaker (draft)"),
        null=True,
        on_delete=models.SET_NULL,
        blank=True,
    )
    published_speaker = models.ForeignKey(
        speaker_models.PublishedSpeaker,
        verbose_name=_("Speaker (public)"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    submission_timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(verbose_name=_("Session title"), max_length=255)
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255)
    abstract = models.TextField(verbose_name=_("Abstract"))
    remarks = models.TextField(verbose_name=_("Remarks"), blank=True)
    track = models.ForeignKey(Track, null=True, blank=True)
    talkformat = models.ManyToManyField("TalkFormat", verbose_name=_("Talk Formats"))
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=False, blank=False)
    spots = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Spots"),
        help_text=_("Maximum number of attendees for this talk"),
    )

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ["title"]

    def clean(self):
        super().clean()
        if not self.draft_speaker and not self.published_speaker:
            raise ValidationError(
                _("A draft speaker or a published speaker is required.")
            )

    def publish(self, track):
        self.track = track
        self.published_speaker = self.draft_speaker.publish(self.event)
        self.save()

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Talk, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if self.published_speaker_id:
            return "{} - {}".format(self.published_speaker, self.title)
        else:
            return "{} - {}".format(self.draft_speaker, self.title)

    @property
    def is_limited(self):
        return self.spots > 0

    @property
    def is_feedback_allowed(self):
        return (
            TalkSlot.objects.filter(talk=self).exists()
            and (
                self.talkslot.time.start_time
                + timedelta(minutes=settings.TALK_FEEDBACK_ALLOWED_MINUTES)
            )
            <= timezone.now()
        )


class TalkMedia(models.Model):
    talk = models.OneToOneField(Talk, related_name="media")
    youtube = models.CharField(
        verbose_name=_("Youtube video id"), max_length=64, blank=True
    )
    slideshare = models.CharField(
        verbose_name=_("Slideshare id"), max_length=64, blank=True
    )
    codelink = models.CharField(
        verbose_name=_("Source code"), max_length=255, blank=True
    )


@python_2_unicode_compatible
class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    talk = models.ForeignKey(Talk)
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ["voter", "talk"]

    def __str__(self):
        return "{} voted {} for {} by {}".format(
            self.voter, self.score, self.talk.title, self.talk.draft_speaker
        )


@python_2_unicode_compatible
class TalkComment(TimeStampedModel):
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL)
    talk = models.ForeignKey(Talk)
    comment = models.TextField(verbose_name=_("Comment"))
    is_visible = models.BooleanField(
        verbose_name=_("Visible for Speaker"),
        default=False,
        help_text=_("Indicates whether the comment is visible to the speaker."),
    )

    def __str__(self):
        return "{} commented {} for {} by {}".format(
            self.commenter, self.comment, self.talk.title, self.talk.draft_speaker
        )


class RoomManager(models.Manager):
    def for_event(self, event):
        return self.filter(event=event)


@python_2_unicode_compatible
class Room(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=100, blank=False)
    priority = models.PositiveSmallIntegerField(verbose_name=_("Priority"), default=0)
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)

    objects = RoomManager()

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["event", "priority", "name"]
        unique_together = (("name", "event"),)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class TimeSlot(TimeStampedModel):
    name = models.CharField(max_length=40, blank=False)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    text_body = models.TextField(blank=True, default="")
    event = models.ForeignKey(Event, verbose_name=_("Event"), null=True)
    block = models.PositiveSmallIntegerField(verbose_name=_("Block"), default=0)

    class Meta:
        verbose_name = _("Time slot")
        verbose_name_plural = _("Time slots")
        ordering = ["start_time", "end_time", "name"]
        unique_together = ("name", "event")

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


@python_2_unicode_compatible
class TalkSlot(TimeStampedModel):
    talk = models.OneToOneField(Talk)
    room = models.ForeignKey(Room)
    time = models.ForeignKey(TimeSlot)

    class Meta:
        verbose_name = _("Talk slot")
        verbose_name_plural = _("Talk slots")

    def __str__(self):
        return "{} {}".format(self.room, self.time)


@python_2_unicode_compatible
class TalkFormat(models.Model):
    name = models.CharField(max_length=40, blank=False)
    duration = models.PositiveSmallIntegerField(verbose_name=_("Duration"), default=60)

    class Meta:
        ordering = ["duration", "name"]
        unique_together = (("name", "duration"),)
        verbose_name = _("Talk Format")
        verbose_name_plural = _("Talk Format")

    def __str__(self):
        h, m = divmod(self.duration, 60)
        return "{} ({:d}:{:02d}h)".format(self.name, h, m)


class SessionReservation(TimeStampedModel):
    attendee = models.ForeignKey(
        Attendee,
        verbose_name=_("Attendee"),
        null=False,
        limit_choices_to={"event__published": True},
        on_delete=models.CASCADE,
    )
    talk = models.ForeignKey(
        Talk,
        verbose_name=_("Talk"),
        null=False,
        limit_choices_to={"spots__gt": 0},
        on_delete=models.CASCADE,
    )
    is_confirmed = models.BooleanField(verbose_name=_("Confirmed"), default=False)
    is_waiting = models.BooleanField(verbose_name=_("On waiting list"), default=False)

    class Meta:
        verbose_name = _("Session reservation")
        verbose_name_plural = _("Session reservations")
        unique_together = [("attendee", "talk")]

    def get_confirmation_key(self):
        return signing.dumps(
            obj="{}:{}".format(self.attendee.user.get_username(), self.talk_id),
            salt=settings.CONFIRMATION_SALT,
        )


class AttendeeVote(TimeStampedModel):
    attendee = models.ForeignKey(
        Attendee,
        verbose_name=_("Attendee"),
        null=False,
        limit_choices_to={"event__published": True},
        on_delete=models.CASCADE,
    )
    talk = models.ForeignKey(
        Talk,
        verbose_name=_("Talk"),
        null=False,
        limit_choices_to={"track__is_null": False},
        on_delete=models.CASCADE,
    )
    score = models.PositiveSmallIntegerField()

    objects = PostgresManager()

    class Meta:
        verbose_name = _("Attendee vote")
        verbose_name_plural = _("Attendee votes")
        unique_together = ["attendee", "talk"]

    def __str__(self):
        return "{} voted {} for {} by {}".format(
            self.attendee, self.score, self.talk.title, self.talk.published_speaker
        )


class AttendeeFeedback(TimeStampedModel):
    attendee = models.ForeignKey(
        Attendee,
        verbose_name=_("Attendee"),
        null=True,
        blank=True,
        limit_choices_to={"event__published": True},
        on_delete=models.CASCADE,
    )
    talk = models.ForeignKey(
        Talk,
        verbose_name=_("Talk"),
        null=False,
        limit_choices_to={"track__is_null": False},
        on_delete=models.CASCADE,
    )
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(verbose_name=_("Comment"), blank=True)

    class Meta:
        verbose_name = pgettext_lazy(
            "attendee feedback singular form", "Attendee feedback"
        )
        verbose_name_plural = pgettext_lazy(
            "attendee feedback plural form", "Attendee feedback"
        )
        unique_together = ["attendee", "talk"]

    def __str__(self):
        return "{} gave feedback for {} by {}: score={}, comment={}".format(
            self.attendee,
            self.talk.title,
            self.talk.published_speaker,
            self.score,
            self.comment,
        )


class AttendeeEventFeedback(TimeStampedModel):
    attendee = models.ForeignKey(
        Attendee,
        verbose_name=_("Attendee"),
        null=True,
        blank=True,
        limit_choices_to={"event__published": True},
        on_delete=models.SET_NULL,
    )
    event = models.ForeignKey(
        Event,
        verbose_name=_("Event"),
        null=False,
        limit_choices_to={"published": True},
        on_delete=models.CASCADE,
    )
    overall_score = models.PositiveSmallIntegerField(verbose_name=_("Event score"))
    organisation_score = models.PositiveSmallIntegerField(
        verbose_name=_("Organisation score")
    )
    session_score = models.PositiveSmallIntegerField(verbose_name=_("Session score"))
    comment = models.TextField(verbose_name=_("Comment"), blank=True)

    class Meta:
        verbose_name = pgettext_lazy(
            "attendee event feedback singular form", "Attendee event feedback"
        )
        verbose_name_plural = pgettext_lazy(
            "attendee event feedback plural form", "Attendee event feedback"
        )
        unique_together = ["attendee", "event"]

    def __str__(self):
        return "{} gave feedback for {}: scores=event {}, organisation {}, sessions {}, comment={}".format(
            self.attendee,
            self.event.title,
            self.overall_score,
            self.organisation_score,
            self.session_score,
            self.comment,
        )
