import os

from django.test import TestCase

from attendee.tests import attendee_testutils
from event.tests import event_testutils
from speaker.forms import CreateSpeakerForm, UserSpeakerPortraitForm
from speaker.models import PublishedSpeaker, Speaker
from speaker.tests import speaker_testutils
from speaker.tests.speaker_testutils import TemporaryMediaTestCase
from talk.models import Talk, Track


class TestCreateSpeakerView(TestCase):
    def setUp(self):
        self.email = "test@example.org"
        self.url = "/speaker/register/"

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next={}".format(self.url))

    def test_used_template(self):
        _, password = attendee_testutils.create_test_user(self.email)
        self.client.login(username=self.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("talk/create_speaker.html")

    def test_get_form_class(self):
        _, password = attendee_testutils.create_test_user(self.email)
        self.client.login(username=self.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], CreateSpeakerForm)

    def test_dispatch_user(self):
        _, password = attendee_testutils.create_test_user(self.email)
        self.client.login(username=self.email, password=password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("speaker/speaker_form.html")

    def test_dispatch_speaker(self):
        user, password = attendee_testutils.create_test_user(self.email)
        Speaker.objects.create(
            user=user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.client.login(username=self.email, password=password)
        response = self.client.get(self.url)
        self.assertRedirects(response, "/speaker/profile/")

    def test_form_valid(self):
        _, password = attendee_testutils.create_test_user("speaker@example.org")
        data = {
            "name": "Special Tester",
            "shirt_size": "2",
            "video_permission": "checked",
            "short_biography": "A guy from somewhere having something great",
        }
        self.client.login(email="speaker@example.org", password=password)
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, "/speaker/upload_portrait/")

    def test_redirect_form_valid(self):
        _, password = attendee_testutils.create_test_user("speaker@example.org")
        data = {
            "name": "Special Tester",
            "shirt_size": "2",
            "video_permission": "checked",
            "short_biography": "A guy from somewhere having something great",
            "next": "/foo",
        }
        self.client.login(email="speaker@example.org", password=password)
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, "/speaker/upload_portrait/?next=/foo")


class TestUserSpeakerProfileView(TestCase):
    def setUp(self):
        self.url = "/speaker/profile/"

    @classmethod
    def setUpTestData(cls):
        cls.email = "test@example.org"
        user, cls.password = attendee_testutils.create_test_user(cls.email)
        cls.speaker = Speaker.objects.create(
            user=user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next={}".format(self.url))

    def test_used_template(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("speaker/speaker_user_profile.html")

    def test_context_has_speaker(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["speaker"], self.speaker)


class TestUserSpeakerPortraitUploadView(TemporaryMediaTestCase):
    def setUp(self):
        self.url = "/speaker/upload_portrait/"

    @classmethod
    def setUpTestData(cls):
        cls.email = "test@example.org"
        cls.user, cls.password = attendee_testutils.create_test_user(email=cls.email)

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next={}".format(self.url))

    def test_used_template(self):
        Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("speaker/speaker_form.html")

    def test_context_has_speaker(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("speaker", response.context)
        self.assertEqual(response.context["speaker"], speaker)

    def test_form_class(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("speaker", response.context)
        self.assertEqual(response.context["speaker"], speaker)

    def test_post_updates_speaker_image(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.assertFalse(bool(speaker.portrait))
        with open(
            os.path.join(os.path.dirname(__file__), "mu_at_mil_house.jpg"), "rb"
        ) as image_file:
            data = {"portrait": image_file}
            self.client.login(email=self.email, password=self.password)
            response = self.client.post(self.url, data=data)
            self.assertRedirects(response, "/speaker/profile/")
            speaker.refresh_from_db()
            self.assertTrue(bool(speaker.portrait))

    def test_ajax_post_returns_json(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.assertFalse(bool(speaker.portrait))
        with open(
            os.path.join(os.path.dirname(__file__), "mu_at_mil_house.jpg"), "rb"
        ) as image_file:
            data = {"portrait": image_file}
            self.client.login(email=self.email, password=self.password)
            response = self.client.post(
                self.url, data=data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            self.assertEqual(response.status_code, 200)
            json = response.json()
            self.assertIn("image_url", json)
            speaker.refresh_from_db()
            self.assertTrue(bool(speaker.portrait))

    def test_post_error(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.assertFalse(bool(speaker.portrait))
        data = {}
        self.client.login(email=self.email, password=self.password)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], UserSpeakerPortraitForm)
        self.assertTrue(len(response.context["form"].errors) > 0)

    def test_ajax_post_error_json(self):
        speaker = Speaker.objects.create(
            user=self.user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )
        self.assertFalse(bool(speaker.portrait))
        data = {}
        self.client.login(email=self.email, password=self.password)
        response = self.client.post(
            self.url, data=data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 400)
        json = response.json()
        self.assertIn("errors", json)
        speaker.refresh_from_db()
        self.assertFalse(bool(speaker.portrait))


class TestUserSpeakerPortraitDeleteView(TemporaryMediaTestCase):
    def setUp(self):
        self.url = "/speaker/delete_portrait/"

    @classmethod
    def setUpTestData(cls):
        cls.email = "test@example.org"
        user, cls.password = attendee_testutils.create_test_user(cls.email)
        cls.speaker = Speaker.objects.create(
            user=user,
            shirt_size=2,
            video_permission=True,
            short_biography="A short biography text",
        )

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, "/accounts/login/?next={}".format(self.url))

    def test_needs_portrait(self):
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def _store_portrait_image(self):
        with open(
            os.path.join(os.path.dirname(__file__), "mu_at_mil_house.jpg"), "rb"
        ) as image:
            self.speaker.portrait.save(os.path.basename(image.name), image)

    def test_used_template(self):
        self._store_portrait_image()
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("speaker/speaker_portrait_confirm_delete.html")

    def test_form_in_context_data(self):
        self._store_portrait_image()
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_post_deletes_portrait(self):
        self._store_portrait_image()
        self.client.login(username=self.email, password=self.password)
        response = self.client.post(self.url)
        self.assertRedirects(response, "/speaker/profile/")
        self.speaker.refresh_from_db()
        self.assertFalse(bool(self.speaker.portrait))

    def test_ajax_post_deletes_portrait(self):
        self._store_portrait_image()
        self.client.login(username=self.email, password=self.password)
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 204)
        self.speaker.refresh_from_db()
        self.assertFalse(bool(self.speaker.portrait))


class PublishedSpeakerPublicView(TemporaryMediaTestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event(submission_open=False)
        self.speaker, _, _ = speaker_testutils.create_test_speaker()
        with open(
            os.path.join(os.path.dirname(__file__), "mu_at_mil_house.jpg"), "rb"
        ) as image:
            self.speaker.portrait.save(os.path.basename(image.name), image)
        self.published_speaker = PublishedSpeaker.objects.copy_from_speaker(
            self.speaker, self.event
        )
        self.track = Track.objects.create(event=self.event, name="Track 1")
        self.talk = Talk.objects.create(
            published_speaker=self.published_speaker,
            title="Something important",
            abstract="I have something important to say",
            track=self.track,
            event=self.event,
        )
        self.url = "/{}/speaker/{}/".format(
            self.event.slug, self.published_speaker.slug
        )

    def test_template_used(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "speaker/publishedspeaker_detail.html")

    def test_speaker_with_two_talks(self):
        Talk.objects.create(
            published_speaker=self.published_speaker,
            title="Some other talk",
            abstract="Been there, done that",
            event=self.event,
            track=self.track,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_has_speaker(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("publishedspeaker", response.context)
        self.assertEqual(response.context["publishedspeaker"], self.published_speaker)

    def test_context_has_talk(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("talks", response.context)
        self.assertEqual(list(response.context["talks"]), [self.talk])

    def test_context_has_all_talks(self):
        talk2 = Talk.objects.create(
            published_speaker=self.published_speaker,
            title="Some other talk",
            abstract="Been there, done that",
            track=self.track,
            event=self.event,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("talks", response.context)
        self.assertEqual(set(response.context["talks"]), {self.talk, talk2})

    def test_context_has_talks_for_deleted_draft_speaker(self):
        self.published_speaker.speaker.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("talks", response.context)
        self.assertEqual(set(response.context["talks"]), {self.talk})


class TestPublishedSpeakerListView(TestCase):
    def setUp(self):
        self.event = event_testutils.create_test_event()
        self.speakers = []
        for i in range(10):
            self.speakers.append(
                PublishedSpeaker.objects.create(
                    email="test-speaker-{}@example.org".format(i),
                    event=self.event,
                    video_permission=True,
                    name="Test Speaker {}".format(i),
                )
            )
        self.url = "/{}/speaker/".format(self.event.slug)

    def test_get_queryset_no_talks(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["publishedspeaker_list"]), 0)

    def test_get_queryset_with_talks(self):
        track = Track.objects.create(name="Hollow talk")
        Talk.objects.create(
            title="Talk 1",
            abstract="Abstract 1",
            published_speaker=self.speakers[0],
            event=self.event,
            track=track,
        )
        Talk.objects.create(
            title="Talk 2",
            abstract="Abstract 2",
            published_speaker=self.speakers[0],
            event=self.event,
            track=track,
        )
        Talk.objects.create(
            title="Talk 3",
            abstract="Abstract 3",
            published_speaker=self.speakers[1],
            event=self.event,
            track=track,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        speaker_list = response.context["publishedspeaker_list"]
        self.assertEqual(len(speaker_list), 2)
        self.assertIn(self.speakers[0], speaker_list)
        self.assertIn(self.speakers[1], speaker_list)
