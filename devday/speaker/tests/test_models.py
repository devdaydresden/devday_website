import os
from datetime import timedelta

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from attendee.tests import attendee_testutils
from event.tests import event_testutils
from speaker.models import (
    PublishedSpeaker, Speaker, get_pil_type_and_extension, create_public_image,
    create_thumbnail)
from speaker.tests.speaker_testutils import TemporaryMediaTestCase


def copy_speaker_image(field):
    speaker_placeholder_source_path = finders.find(
        os.path.join('img', 'speaker-dummy.png'))
    with open(speaker_placeholder_source_path, 'rb') as source:
        field.save('speaker-dummy.png', source, save=False)


class TestSpeaker(TestCase):
    def setUp(self):
        self.user, _ = attendee_testutils.create_test_user()

    def test___str__(self):
        speaker = Speaker(
            user=self.user,
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(str(speaker), 'Test Speaker')

    def test_auto_slug(self):
        speaker = Speaker(
            user=self.user,
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(speaker.slug, slugify('Test Speaker'))

    def test_manual_slug(self):
        speaker = Speaker(
            user=self.user,
            name='Test Speaker',
            slug='a-slugger-by-heart',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        speaker.save()
        self.assertEqual(speaker.slug, 'a-slugger-by-heart')

    def test_publish(self):
        event = event_testutils.create_test_event()
        speaker = Speaker.objects.create(
            user=self.user,
            name='Test Speaker',
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.'
        )
        published_speaker = speaker.publish(event)
        self.assertIsInstance(published_speaker, PublishedSpeaker)
        self.assertEqual(published_speaker.name, speaker.name)
        self.assertEqual(published_speaker.speaker, speaker)
        self.assertEqual(published_speaker.event, event)

        published_speaker2 = speaker.publish(event)
        self.assertEqual(published_speaker2, published_speaker)


class TestPublishedSpeaker(TestCase):
    def test___str__(self):
        event = event_testutils.create_test_event(
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
        self.assertEqual(
            str(published_speaker), 'Test Speaker ({})'.format(event.title))


class TestPublishedSpeakerManager(TemporaryMediaTestCase):
    def test_copy_from_speaker(self):
        user, _ = attendee_testutils.create_test_user()
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

        event = event_testutils.create_test_event()
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
        user, _ = attendee_testutils.create_test_user()
        speaker = Speaker(
            video_permission=True,
            shirt_size=3,
            short_biography='My short and lucky biography.',
            user=user,
        )
        speaker.save()

        event = event_testutils.create_test_event()
        published = PublishedSpeaker.objects.copy_from_speaker(speaker, event)
        self.assertIs(published.speaker, speaker)
        self.assertIs(published.event, event)
        self.assertEqual(published.video_permission, speaker.video_permission)
        self.assertEqual(published.short_biography, speaker.short_biography)


class TestGetPILTypeAndExtension(TestCase):
    def test_jpeg(self):
        result = get_pil_type_and_extension(
            os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'))
        self.assertEqual(result, ('jpeg', 'jpg'))

    def test_png(self):
        result = get_pil_type_and_extension(
            os.path.join(
                os.path.dirname(__file__), '..', '..', 'devday', 'static',
                'img', 'speaker-dummy.png'))
        self.assertEqual(result, ('png', 'png'))

    def test_unsupported(self):
        with self.assertRaisesMessage(ValueError, 'unsupported file type'):
            get_pil_type_and_extension(
                os.path.join(
                    os.path.dirname(__file__), '..', '..', 'devday', 'static',
                    'img', 'speaker-at-a-conference-svgrepo-com.svg'))


class TestCreatePublicImage(TestCase):
    def setUp(self):
        user, _ = attendee_testutils.create_test_user()
        self.speaker = Speaker.objects.create(
            user=user,
            name='Test speaker',
            shirt_size=3,
            video_permission=False,
        )

    def test_create_public_image_no_image(self):
        create_public_image(self.speaker.portrait, self.speaker.public_image)
        self.assertFalse(self.speaker.public_image)


class TestCreateThumbnail(TestCase):
    def setUp(self):
        user, _ = attendee_testutils.create_test_user()
        self.speaker = Speaker.objects.create(
            user=user,
            name='Test speaker',
            shirt_size=3,
            video_permission=False,
        )

    def test_create_thumbnail_no_image(self):
        create_thumbnail(self.speaker.portrait, self.speaker.thumbnail)
        self.assertFalse(self.speaker.thumbnail)


class TestCreateDerivedSpeakerImages(TemporaryMediaTestCase):
    def setUp(self):
        user, _ = attendee_testutils.create_test_user()
        self.speaker = Speaker.objects.create(
            user=user,
            name='Test speaker',
            shirt_size=3,
            video_permission=False,
        )

    def test_no_images(self):
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

    def test_set_portrait_sets_public_image_and_thumbnail(self):
        copy_speaker_image(self.speaker.portrait)
        self.speaker.save()
        self.assertTrue(self.speaker.portrait)
        self.assertTrue(self.speaker.public_image)
        self.assertTrue(self.speaker.thumbnail)

    def test_no_portrait_deletes_other_fields(self):
        copy_speaker_image(self.speaker.public_image)
        copy_speaker_image(self.speaker.thumbnail)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

        copy_speaker_image(self.speaker.public_image)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

        copy_speaker_image(self.speaker.thumbnail)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)


class TestCreateDerivedPublishedSpeakerImages(TemporaryMediaTestCase):
    def setUp(self):
        user, _ = attendee_testutils.create_test_user()
        event = event_testutils.create_test_event()
        self.speaker = Speaker.objects.create(
            user=user,
            name='Test speaker',
            shirt_size=3,
            video_permission=False,
        ).publish(event)

    def test_no_images(self):
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

    def test_set_portrait_sets_public_image_and_thumbnail(self):
        copy_speaker_image(self.speaker.portrait)
        self.speaker.save()
        self.assertTrue(self.speaker.portrait)
        self.assertTrue(self.speaker.public_image)
        self.assertTrue(self.speaker.thumbnail)

    def test_no_portrait_deletes_other_fields(self):
        copy_speaker_image(self.speaker.public_image)
        copy_speaker_image(self.speaker.thumbnail)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

        copy_speaker_image(self.speaker.public_image)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)

        copy_speaker_image(self.speaker.thumbnail)
        self.speaker.save()
        self.assertFalse(self.speaker.portrait)
        self.assertFalse(self.speaker.public_image)
        self.assertFalse(self.speaker.thumbnail)
