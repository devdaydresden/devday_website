import os

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from devday.extras import ValidatedImageField
from event.models import Event

T_SHIRT_SIZES = (
    (1, _('XS')),
    (2, _('S')),
    (3, _('M')),
    (4, _('L')),
    (5, _('XL')),
    (6, _('XXL')),
    (7, _('XXXL')),
)


class SpeakerBase(models.Model):
    name = models.CharField(_('speaker name'), max_length=128, blank=False)
    slug = models.SlugField(_('slug'), max_length=128)
    twitter_handle = models.CharField(
        _('twitter handle'), blank=True, max_length=64)
    phone = models.CharField(_("Phone"), blank=True, max_length=32)
    position = models.CharField(
        _('job or study subject'), blank=True, max_length=128)
    organization = models.CharField(
        _('company or institution'), blank=True, max_length=128)

    video_permission = models.BooleanField(
        verbose_name=_('Video permitted'),
        help_text=_('I hereby agree that audio and visual recordings of '
                    'me and my session can be published on the social media '
                    'channels of the event organizer and the website '
                    'devday.de.')
    )
    short_biography = models.TextField(verbose_name=_('Short biography'))

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.slug is None or self.slug.strip() == '':
            self.slug = slugify(self.name)
        super(SpeakerBase, self).save(**kwargs)


class Speaker(SpeakerBase):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='speaker', on_delete=models.CASCADE)
    date_registered = models.DateTimeField(
        _('registered as speaker'), default=timezone.now)
    portrait = ValidatedImageField(
        verbose_name=_('Speaker image'), upload_to='speaker_original')
    thumbnail = models.ImageField(
        verbose_name=_("Speaker image thumbnail"),
        upload_to='speaker_thumbs',
        max_length=500, null=True, blank=True)
    public_image = models.ImageField(
        verbose_name=_("Public speaker image"),
        upload_to='speaker_public',
        max_length=500, null=True, blank=True)
    shirt_size = models \
        .PositiveSmallIntegerField(verbose_name=_('T-shirt size'),
                                   choices=T_SHIRT_SIZES)

    class Meta:
        verbose_name = _('speaker')
        verbose_name_plural = _('speakers')
        abstract = False

    def __str__(self):
        return self.name


class PublishedSpeakerManager(models.Manager):

    def copy_from_speaker(self, speaker, event):
        published_speaker = self.model(
            speaker=speaker,
            date_published=timezone.now(),
            event=event,
            twitter_handle=speaker.twitter_handle,
            phone=speaker.phone,
            position=speaker.position,
            organization=speaker.organization,
            video_permission=speaker.video_permission,
            short_biography=speaker.short_biography,
        )
        if speaker.portrait:
            published_speaker.portrait.save(
                os.path.basename(speaker.portrait.name),
                speaker.portrait.file, save=False)
        if speaker.thumbnail:
            published_speaker.thumbnail.save(
                os.path.basename(speaker.thumbnail.name),
                speaker.thumbnail.file, save=False)
        if speaker.public_image:
            published_speaker.public_image.save(
                os.path.basename(speaker.public_image.name),
                speaker.public_image.file, save=False)
        published_speaker.save()
        return published_speaker


def event_speaker_image_directory(instance, filename):
    return 'speaker/{0}/original/{1}'.format(instance.event.slug, filename)


def event_speaker_thumbnail_directory(instance, filename):
    return 'speaker/{0}/thumbs/{1}'.format(instance.event.slug, filename)


def event_public_speaker_image_directory(instance, filename):
    return 'speaker/{0}/public/{1}'.format(instance.event.slug, filename)


class PublishedSpeaker(SpeakerBase):
    speaker = models.ForeignKey(
        Speaker, null=True, blank=True, on_delete=models.SET_NULL)
    date_published = models.DateTimeField(
        _('published as speaker'), default=timezone.now)
    event = models.ForeignKey(Event, null=False)
    portrait = ValidatedImageField(
        verbose_name=_('Speaker image'),
        upload_to=event_speaker_image_directory)
    thumbnail = models.ImageField(
        verbose_name=_("Speaker image thumbnail"),
        upload_to=event_speaker_thumbnail_directory,
        max_length=500, null=True, blank=True)
    public_image = models.ImageField(
        verbose_name=_("Public speaker image"),
        upload_to=event_public_speaker_image_directory,
        max_length=500, null=True, blank=True)

    objects = PublishedSpeakerManager()

    class Meta:
        verbose_name = _('published speaker')
        verbose_name_plural = _('published speakers')
        abstract = False
        unique_together = [('slug', 'event')]

    def __str__(self):
        return '{0} ({1})'.format(self.name, self.event.title)
