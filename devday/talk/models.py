import logging
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import m2m_changed, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from attendee.models import Attendee
from event.models import Event
from ordered_model.models import OrderedModel
from psqlextra.manager import PostgresManager
from speaker import models as speaker_models
from speaker.models import PublishedSpeaker, Speaker

log = logging.getLogger(__name__)


class Track(TimeStampedModel):
    name = models.CharField(max_length=100, blank=False)
    event = models.ForeignKey(
        Event, verbose_name=_("Event"), null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Track")
        verbose_name_plural = _("Tracks")
        ordering = ["name"]
        unique_together = ("name", "event")

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


class ReservableTalkManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(event__start_time__gt=timezone.now(), spots__gt=0)
        )


class TalkManager(models.Manager):
    def create(self, **kwargs):
        draft_speaker = kwargs.pop("draft_speaker")
        talk = super().create(**kwargs)
        TalkDraftSpeaker.objects.create(talk=talk, draft_speaker=draft_speaker, order=1)
        return talk


class Talk(models.Model):
    draft_speakers = models.ManyToManyField(
        speaker_models.Speaker,
        verbose_name=_("Speaker (draft)"),
        blank=True,
        through="TalkDraftSpeaker",
        through_fields=("talk", "draft_speaker"),
    )
    published_speakers = models.ManyToManyField(
        speaker_models.PublishedSpeaker,
        verbose_name=_("Speaker (public)"),
        blank=True,
        through="TalkPublishedSpeaker",
        through_fields=("talk", "published_speaker"),
    )
    submission_timestamp = models.DateTimeField(auto_now_add=True)
    title = models.CharField(verbose_name=_("Session title"), max_length=255)
    slug = models.SlugField(verbose_name=_("Slug"), max_length=255)
    abstract = models.TextField(verbose_name=_("Abstract"))
    remarks = models.TextField(verbose_name=_("Remarks"), blank=True)
    track = models.ForeignKey(Track, null=True, blank=True, on_delete=models.CASCADE)
    talkformat = models.ManyToManyField("TalkFormat", verbose_name=_("Talk Formats"))
    event = models.ForeignKey(
        Event,
        verbose_name=_("Event"),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    spots = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Spots"),
        help_text=_("Maximum number of attendees for this talk"),
    )

    objects = TalkManager()
    reservable = ReservableTalkManager()

    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ["title"]

    def publish(self, track):
        self.track = track
        for draft_speaker in TalkDraftSpeaker.objects.filter(talk=self):
            published_speaker = draft_speaker.draft_speaker.publish(self.event)
            TalkPublishedSpeaker.objects.update_or_create(
                talk=self,
                published_speaker=published_speaker,
                order=draft_speaker.order,
            )
        self.save()

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Talk, self).save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if TalkPublishedSpeaker.objects.filter(talk=self).exists():
            return "{} - {}".format(
                ", ".join(
                    [
                        str(speaker.published_speaker)
                        for speaker in TalkPublishedSpeaker.objects.filter(talk=self)
                    ]
                ),
                self.title,
            )
        else:
            return "{} - {}".format(
                ", ".join(
                    [
                        str(speaker.draft_speaker)
                        for speaker in TalkDraftSpeaker.objects.filter(talk=self)
                    ]
                ),
                self.title,
            )

    @property
    def is_limited(self):
        return self.spots > 0

    @property
    def is_reservation_available(self):
        return self.is_limited and not self.event.is_started()

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


class TalkDraftSpeaker(OrderedModel, TimeStampedModel):
    talk = models.ForeignKey(Talk, verbose_name=_("Talk"), on_delete=models.CASCADE)
    draft_speaker = models.ForeignKey(
        speaker_models.Speaker, verbose_name=_("Speaker"), on_delete=models.CASCADE
    )

    class Meta(OrderedModel.Meta, TimeStampedModel.Meta):
        unique_together = ("talk", "draft_speaker")
        verbose_name = _("Talk draft speaker")
        verbose_name_plural = _("Talk draft speakers")


class TalkPublishedSpeaker(OrderedModel, TimeStampedModel):
    talk = models.ForeignKey(Talk, verbose_name=_("Talk"), on_delete=models.CASCADE)
    published_speaker = models.ForeignKey(
        speaker_models.PublishedSpeaker,
        verbose_name=_("Published speaker"),
        on_delete=models.CASCADE,
    )

    class Meta(OrderedModel.Meta, TimeStampedModel.Meta):
        unique_together = ("talk", "published_speaker")
        verbose_name = _("Talk published speaker")
        verbose_name_plural = _("Talk published speakers")


@receiver(post_delete, sender=TalkDraftSpeaker)
def remove_talks_without_speakers(sender, instance, **kwargs):
    talk = instance.talk
    if not talk.published_speakers.exists() and not talk.draft_speakers.exists():
        talk.delete()


@receiver(m2m_changed, sender=Talk.draft_speakers.through)
def prevent_removal_of_last_draft_speaker(sender, instance, action, **kwargs):
    if kwargs["reverse"]:
        return
    if action == "pre_remove":
        draft_speaker_count = (
            TalkDraftSpeaker.objects.using(kwargs["using"])
            .filter(talk=instance)
            .count()
        )
        if draft_speaker_count - len(kwargs["pk_set"]) == 0:
            if (
                not TalkPublishedSpeaker.objects.using(kwargs["using"])
                .filter(talk=instance)
                .exists()
            ):
                raise ValidationError(
                    _(
                        "Cannot delete last draft speaker from talk without published speaker"
                    ),
                    "cannot_delete_last_speaker_from_talk",
                )
    elif action == "pre_clear":
        if (
            not TalkPublishedSpeaker.objects.using(kwargs["using"])
            .filter(talk=instance)
            .exists()
        ):
            raise ValidationError(
                _(
                    "Cannot delete last draft speaker from talk without published speaker"
                ),
                "cannot_delete_last_speaker_from_talk",
            )


@receiver(m2m_changed, sender=TalkPublishedSpeaker)
def prevent_removal_of_last_published_speaker(sender, instance, action, **kwargs):
    if kwargs["reverse"]:
        return
    if action == "pre_remove":
        published_speaker_count = (
            TalkPublishedSpeaker.objects.using(kwargs["using"])
            .filter(talk=instance)
            .count()
        )
        if published_speaker_count - len(kwargs["pk_set"]) == 0:
            if (
                not TalkDraftSpeaker.objects.using(kwargs["using"])
                .filter(talk=instance)
                .exists()
            ):
                raise ValidationError(
                    _(
                        "Cannot delete last published speaker from talk without draft speaker"
                    ),
                    "cannot_delete_last_speaker_from_talk",
                )
    elif action == "pre_clear":
        if (
            not TalkDraftSpeaker.objects.using(kwargs["using"])
            .filter(talk=instance)
            .exists()
        ):
            raise ValidationError(
                _(
                    "Cannot delete last published speaker from talk without draft speaker"
                ),
                "cannot_delete_last_speaker_from_talk",
            )


class TalkMedia(models.Model):
    talk = models.OneToOneField(Talk, related_name="media", on_delete=models.CASCADE)
    youtube = models.CharField(
        verbose_name=_("Youtube video id"), max_length=64, blank=True
    )
    slideshare = models.CharField(
        verbose_name=_("Slideshare id"), max_length=64, blank=True
    )
    codelink = models.CharField(
        verbose_name=_("Source code"), max_length=255, blank=True
    )


class Vote(models.Model):
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ["voter", "talk"]

    def __str__(self):
        return "{} voted {} for {} by {}".format(
            self.voter,
            self.score,
            self.talk.title,
            ", ".join([str(speaker) for speaker in self.talk.draft_speakers.all()]),
        )


class TalkComment(TimeStampedModel):
    commenter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name=_("Comment"))
    is_visible = models.BooleanField(
        verbose_name=_("Visible for Speaker"),
        default=False,
        help_text=_("Indicates whether the comment is visible to the speaker."),
    )

    def __str__(self):
        return "{} commented {} for {} by {}".format(
            self.commenter,
            self.comment,
            self.talk.title,
            ", ".join(
                [str(draft_speaker) for draft_speaker in self.talk.draft_speakers.all()]
            ),
        )


class RoomManager(models.Manager):
    def for_event(self, event):
        return self.filter(event=event)


class Room(TimeStampedModel):
    name = models.CharField(verbose_name=_("Name"), max_length=100, blank=False)
    priority = models.PositiveSmallIntegerField(verbose_name=_("Priority"), default=0)
    event = models.ForeignKey(
        Event, verbose_name=_("Event"), null=True, on_delete=models.CASCADE
    )

    objects = RoomManager()

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["event", "priority", "name"]
        unique_together = (("name", "event"),)

    def __str__(self):
        return self.name


class TimeSlot(TimeStampedModel):
    name = models.CharField(max_length=40, blank=False)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    text_body = models.TextField(blank=True, default="")
    event = models.ForeignKey(
        Event, verbose_name=_("Event"), null=True, on_delete=models.CASCADE
    )
    block = models.PositiveSmallIntegerField(verbose_name=_("Block"), default=0)

    class Meta:
        verbose_name = _("Time slot")
        verbose_name_plural = _("Time slots")
        ordering = ["start_time", "end_time", "name"]
        unique_together = ("name", "event")

    def __str__(self):
        return "{} ({})".format(self.name, self.event)


class TalkSlot(TimeStampedModel):
    talk = models.OneToOneField(Talk, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    time = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Talk slot")
        verbose_name_plural = _("Talk slots")

    def __str__(self):
        return "{} {}".format(self.room, self.time)


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
            self.attendee,
            self.score,
            self.talk.title,
            ", ".join(self.talk.published_speakers.all()),
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
            ", ".join(
                [
                    str(published_speaker)
                    for published_speaker in self.talk.published_speakers.all()
                ]
            ),
            self.score,
            self.comment,
        )
