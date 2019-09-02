from django.apps import apps
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _


class EventManager(models.Manager):
    def current_event(self):
        return self.filter(published=True).order_by("-start_time").first()

    def current_event_id(self):
        e = self.current_event()
        if e:
            return e.id
        return None

    def current_registration_open(self):
        e = self.current_event()
        if e:
            return e.registration_open
        return False

    def current_submission_open(self):
        e = self.current_event()
        if e:
            return e.submission_open
        return False

    def all_but_current(self):
        return self.exclude(id=self.current_event_id())

    def create_event(self, title, **kwargs):
        event = self.model(title=title, **kwargs)
        event.save()
        return event


@python_2_unicode_compatible
class Event(models.Model):
    title = models.CharField(verbose_name=_("Event title"), max_length=256, unique=True)
    slug = models.SlugField(verbose_name=_("Short name for URLs"), unique=True)
    description = models.TextField(verbose_name=_("Description"))
    location = models.TextField(verbose_name=_("Location"), blank=True)
    full_day = models.BooleanField(verbose_name=_("Full day event"), default=False)
    start_time = models.DateTimeField(verbose_name=_("Start time"))
    end_time = models.DateTimeField(verbose_name=_("End time"))
    published = models.BooleanField(verbose_name=_("Published"), default=True)
    registration_open = models.BooleanField(
        verbose_name=_("Registration Open"), default=False
    )
    submission_open = models.BooleanField(
        verbose_name=_("Submission Open"), default=False
    )
    voting_open = models.BooleanField(
        verbose_name=_("Voting Open"),
        default=False,
        help_text=_("Attendees can vote for their preferred sessions"),
    )
    sessions_published = models.BooleanField(
        verbose_name=_("Grid Published"), default=False
    )
    talkformat = models.ManyToManyField(
        "talk.TalkFormat", verbose_name=_("Talk Formats")
    )

    objects = EventManager()

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def registration_count(self):
        """Returns the count of registered attendees."""
        a = apps.get_app_config("attendee").get_model("Attendee")
        return a.objects.filter(event=self).count()

    registration_count.short_description = _("Registration Count")

    @property
    def feedback_open(self):
        """
        :return: True if the event has started and feedback is allowed
        """
        return (
            self.published
            and self.start_time is not None
            and self.start_time <= timezone.now()
        )

    def is_started(self):
        return self.start_time < timezone.now()

    def is_running(self):
        return self.start_time < timezone.now() < self.end_time

    def has_ended(self):
        return self.end_time < timezone.now()

    def is_raffle_available(self):
        return not self.has_ended()

    def get_absolute_url(self):
        return reverse("session_list", kwargs={"event": self.slug})

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.title
