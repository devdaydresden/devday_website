import os

from django.contrib.auth import get_user_model
from django.test import TestCase

from speaker.forms import CreateSpeakerForm, UserSpeakerPortraitForm
from speaker.models import Speaker

User = get_user_model()


class TestCreateSpeakerView(TestCase):
    def setUp(self):
        self.url = '/speaker/register/'

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_used_template(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/create_speaker.html')

    def test_get_form_class(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CreateSpeakerForm)

    def test_dispatch_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('speaker/speaker_form.html')

    def test_dispatch_speaker(self):
        user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')
        Speaker.objects.create(
            user=user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertRedirects(response, '/speaker/profile/')

    def test_form_valid(self):
        User.objects.create_user(
            email='speaker@example.org', password='s3cr3t')
        data = {
            'name': 'Special Tester',
            'shirt_size': '2', 'video_permission': 'checked',
            'short_biography': 'A guy from somewhere having something great',
        }
        self.client.login(email='speaker@example.org', password='s3cr3t')
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, '/speaker/upload_portrait/')


class TestUserSpeakerProfileView(TestCase):
    def setUp(self):
        self.url = '/speaker/profile/'

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')
        cls.speaker = Speaker.objects.create(
            user=user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_used_template(self):
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('speaker/speaker_user_profile.html')

    def test_context_has_speaker(self):
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['speaker'], self.speaker)


class TestUserSpeakerPortraitUploadView(TestCase):
    def setUp(self):
        self.url = '/speaker/upload_portrait/'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_used_template(self):
        Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('speaker/speaker_form.html')

    def test_context_has_speaker(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('speaker', response.context)
        self.assertEqual(response.context['speaker'], speaker)

    def test_form_class(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('speaker', response.context)
        self.assertEqual(response.context['speaker'], speaker)

    def test_post_updates_speaker_image(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.assertFalse(bool(speaker.portrait))
        image_file = open(
            os.path.join(os.path.dirname(__file__),
                         'mu_at_mil_house.jpg'), 'rb')
        data = {'portrait': image_file}
        self.client.login(email='test@example.org', password='s3cr3t')
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, '/speaker/profile/')
        speaker.refresh_from_db()
        self.assertTrue(bool(speaker.portrait))

    def test_ajax_post_returns_json(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.assertFalse(bool(speaker.portrait))
        image_file = open(
            os.path.join(os.path.dirname(__file__),
                         'mu_at_mil_house.jpg'), 'rb')
        data = {'portrait': image_file}
        self.client.login(email='test@example.org', password='s3cr3t')
        response = self.client.post(self.url, data=data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertIn('image_url', json)
        speaker.refresh_from_db()
        self.assertTrue(bool(speaker.portrait))

    def test_post_error(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.assertFalse(bool(speaker.portrait))
        data = {}
        self.client.login(email='test@example.org', password='s3cr3t')
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIsInstance(
            response.context['form'], UserSpeakerPortraitForm)
        self.assertTrue(len(response.context['form'].errors) > 0)

    def test_ajax_post_error_json(self):
        speaker = Speaker.objects.create(
            user=self.user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )
        self.assertFalse(bool(speaker.portrait))
        data = {}
        self.client.login(email='test@example.org', password='s3cr3t')
        response = self.client.post(self.url, data=data,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        json = response.json()
        self.assertIn('errors', json)
        speaker.refresh_from_db()
        self.assertFalse(bool(speaker.portrait))


class TestUserSpeakerPortraitDeleteView(TestCase):
    def setUp(self):
        self.url = '/speaker/delete_portrait/'

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            email='test@example.org', password='s3cr3t')
        cls.speaker = Speaker.objects.create(
            user=user, shirt_size=2, video_permission=True,
            short_biography='A short biography text'
        )

    def test_needs_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/accounts/login/?next={}'.format(self.url))

    def test_needs_portrait(self):
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def _store_portrait_image(self):
        with open(os.path.join(
                os.path.dirname(__file__),
                'mu_at_mil_house.jpg'), 'rb') as image:
            self.speaker.portrait.save(
                os.path.basename(image.name), image)

    def test_used_template(self):
        self._store_portrait_image()
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("speaker/speaker_portrait_confirm_delete.html")

    def test_form_in_context_data(self):
        self._store_portrait_image()
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_post_deletes_portrait(self):
        self._store_portrait_image()
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.post(self.url)
        self.assertRedirects(response, '/speaker/profile/')
        self.speaker.refresh_from_db()
        self.assertFalse(bool(self.speaker.portrait))

    def test_ajax_post_deletes_portrait(self):
        self._store_portrait_image()
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.post(
            self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 204)
        self.speaker.refresh_from_db()
        self.assertFalse(bool(self.speaker.portrait))
