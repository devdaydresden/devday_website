import os
import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import override_settings, TransactionTestCase
from django.utils import timezone
from django.utils.text import slugify

from event.models import Event
from speaker.models import Speaker, PublishedSpeaker


def copy_speaker_image(field):
    speaker_placeholder_source_path = finders.find(
        os.path.join('img', 'speaker-dummy.png'))
    with open(speaker_placeholder_source_path, 'rb') as source:
        field.save('speaker-dummy.png', source, save=False)


class TestSpeaker(TransactionTestCase):
    def test___str__(self):
        speaker = Speaker(
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(str(speaker), 'Test Speaker')

    def test_auto_slug(self):
        speaker = Speaker(
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(speaker.slug, slugify('Test Speaker'))

    def test_manual_slug(self):
        speaker = Speaker(
            name='Test Speaker',
            slug='a-slugger-by-heart',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(speaker.slug, 'a-slugger-by-heart')


class TestPublishedSpeaker(TransactionTestCase):
    def test___str__(self):
        event = Event.objects.create(
            title='Test event', slug='test-event', submission_open=True,
            description='This escalated quickly',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
        published_speaker = PublishedSpeaker(
            name='Test Speaker',
            video_permission=True,
            short_biography='My short and lucky biography.',
            event=event
        )
        self.assertEqual(str(published_speaker), 'Test Speaker (Test event)')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestPublishedSpeakerManager(TransactionTestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT)

    def test_copy_from_speaker(self):
        speaker = Speaker(
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        copy_speaker_image(speaker.portrait)
        copy_speaker_image(speaker.thumbnail)
        copy_speaker_image(speaker.public_image)
        speaker.save()

        event = Event.objects.create(
            title='Test event', slug='test-event', submission_open=True,
            description='This escalated quickly',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
        published = PublishedSpeaker.objects.copy_from_speaker(speaker, event)
        self.assertIs(published.speaker, speaker)
        self.assertIs(published.event, event)
        self.assertEqual(published.video_permission, speaker.video_permission)
        self.assertEqual(published.short_biography, speaker.short_biography)
        self.assertTrue(os.path.dirname(published.portrait.path).endswith(
            'speaker/test-event/original'))
        self.assertTrue(os.path.dirname(published.thumbnail.path).endswith(
            'speaker/test-event/thumbs'))
        self.assertTrue(os.path.dirname(published.public_image.path).endswith(
            'speaker/test-event/public'))

    def test_copy_from_speaker_without_images(self):
        speaker = Speaker(
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()

        event = Event.objects.create(
            title='Test event', slug='test-event', submission_open=True,
            description='This escalated quickly',
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1)
        )
        published = PublishedSpeaker.objects.copy_from_speaker(speaker, event)
        self.assertIs(published.speaker, speaker)
        self.assertIs(published.event, event)
        self.assertEqual(published.video_permission, speaker.video_permission)
        self.assertEqual(published.short_biography, speaker.short_biography)
