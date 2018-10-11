from __future__ import unicode_literals

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


class EventManager(models.Manager):
    def current_event(self):
        return self.filter(published=True) \
            .order_by('-start_time').first()

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


@python_2_unicode_compatible
class Event(models.Model):
    title = models.CharField(verbose_name=_("Event title"), max_length=256,
                             null=False, unique=True)
    slug = models.SlugField(verbose_name=_("Short name for URLs"), unique=True)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    location = models.TextField(verbose_name=_("Location"), blank=True)
    full_day = models.BooleanField(verbose_name=_("Full day event"),
                                   default=False)
    start_time = models.DateTimeField(verbose_name=_("Start time"))
    end_time = models.DateTimeField(verbose_name=_("End time"))
    published = models.BooleanField(
        verbose_name=_('Published'), default=True)
    registration_open = models.BooleanField(
        verbose_name=_('Registration Open'), default=False)
    submission_open = models.BooleanField(
        verbose_name=_('Submission Open'), default=False)
    sessions_published = models.BooleanField(
        verbose_name=_('Grid Published'), default=False)
    talkformat = models.ManyToManyField('talk.TalkFormat',
                                        verbose_name=_('Talk Formats'))

    objects = EventManager()

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def registration_count(self):
        "Returns the count of registered attendees."
        a = apps.get_app_config('attendee').get_model('Attendee')
        return a.objects.filter(event=self).count()

    registration_count.short_description = _("Registration Count")

    def get_absolute_url(self):
        return reverse('session_list', kwargs={'event': self.slug})

    def __str__(self):
        return self.title
