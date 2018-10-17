import os
import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.text import slugify

from event.models import Event
from speaker.models import PublishedSpeaker, Speaker

User = get_user_model()


def copy_speaker_image(field):
    speaker_placeholder_source_path = finders.find(
        os.path.join('img', 'speaker-dummy.png'))
    with open(speaker_placeholder_source_path, 'rb') as source:
        field.save('speaker-dummy.png', source, save=False)


class TestSpeaker(TestCase):
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


class TestPublishedSpeaker(TestCase):
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
class TestPublishedSpeakerManager(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_copy_from_speaker(self):
        user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')
        speaker = Speaker(
            name='Mr. Speaker',
            twitter_handle='speakbaer',
            organization='Acme Inc.',
            position='Lead PoC engineer',
            phone='+1-234-1234567',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.',
            user=user,
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
        self.assertEqual(published.name, speaker.name)
        self.assertEqual(published.slug, speaker.slug)
        self.assertEqual(published.twitter_handle, speaker.twitter_handle)
        self.assertEqual(published.phone, speaker.phone)
        self.assertEqual(published.position, speaker.position)
        self.assertEqual(published.organization, speaker.organization)
        self.assertEqual(published.video_permission, speaker.video_permission)
        self.assertEqual(published.short_biography, speaker.short_biography)
        self.assertTrue(os.path.dirname(published.portrait.path).endswith(
            'speaker/test-event/original'))
        self.assertTrue(os.path.dirname(published.thumbnail.path).endswith(
            'speaker/test-event/thumbs'))
        self.assertTrue(os.path.dirname(published.public_image.path).endswith(
            'speaker/test-event/public'))

    def test_copy_from_speaker_without_images(self):
        user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')
        speaker = Speaker(
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.',
            user=user,
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
