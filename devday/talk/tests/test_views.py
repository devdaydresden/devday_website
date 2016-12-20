from __future__ import unicode_literals

import os

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
from django.test import TestCase
from django_file_form.forms import ExistingFile

from attendee.models import Attendee
from talk.forms import CreateSpeakerForm, BecomeSpeakerForm
from talk.models import Speaker, Talk
from talk.views import CreateTalkView, ExistingFileView, SpeakerProfileView, CreateSpeakerView

User = get_user_model()


class TestSubmitSessionView(TestCase):
    def test_submit_session_anonymous(self):
        response = self.client.get('/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/submit_session.html')

    def test_submit_session_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/submit_session.html')

    def test_submit_session_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/submit-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/submit_session.html')

    def test_submit_session_speaker(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/submit-session/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/create-session/')


class TestSpeakerRegisteredView(TestCase):
    def test_template(self):
        response = self.client.get('/session/speaker-registered/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/speaker_registered.html')


class TestTalkSubmittedView(TestCase):
    def test_template(self):
        response = self.client.get('/session/submitted/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/submitted.html')


class TestCreateTalkView(TestCase):
    def test_needs_login(self):
        response = self.client.get('/session/create-session/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/session/create-session/')

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/create-session/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/create-session/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_template(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/create-session/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'talk/create_talk.html')

    def test_get_form_kwargs(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text')
        view = CreateTalkView()
        view.request = HttpRequest()
        view.request.user = user
        kwargs = view.get_form_kwargs()
        self.assertIn('speaker', kwargs)
        self.assertEqual(kwargs['speaker'], speaker)

    def test_redirect_after_success(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.post(
            '/session/create-session/',
            data={'title': 'A fantastic session', 'abstract': 'News for nerds, stuff that matters'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/submitted/')


class TestEditTalkView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email='speaker@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text')
        self.talk = Talk.objects.create(speaker=speaker, title='A nice topic', abstract='reasoning about a topic')

    def test_needs_login(self):
        response = self.client.get('/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/session/edit-session/{}/'.format(self.talk.id))

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_template(self):
        self.client.login(username='speaker@example.org', password='s3cr3t')
        response = self.client.get('/session/edit-session/{}/'.format(self.talk.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/talk_form.html')

    def test_redirect_after_success(self):
        self.client.login(username='speaker@example.org', password='s3cr3t')
        response = self.client.post('/session/edit-session/{}/'.format(self.talk.id), data={
            'title': 'A new title', 'abstract': 'Good things come to those who wait'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/speaker/profile/')


class TestExistingFileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email='speaker@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text',
            portrait=SimpleUploadedFile(
                name='testspeaker.jpg',
                content=open(os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'), 'rb').read(),
                content_type='image/jpeg')
        )

    def test_get_form_kwargs(self):
        view = ExistingFileView(kwargs={'id': self.speaker.id}, request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn('initial', kwargs)
        self.assertIn('uploaded_image', kwargs['initial'])
        self.assertIsInstance(kwargs['initial']['uploaded_image'], ExistingFile)

    def test_get_form_kwargs_no_portrait(self):
        self.speaker.portrait = None
        self.speaker.save()
        view = ExistingFileView(kwargs={'id': self.speaker.id}, request=HttpRequest())
        kwargs = view.get_form_kwargs()
        self.assertIn('initial', kwargs)
        self.assertNotIn('uploaded_image', kwargs['initial'])


class TestSpeakerProfileView(TestCase):
    def setUp(self):
        user = User.objects.create_user(email='speaker@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        self.speaker = Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text',
            portrait=SimpleUploadedFile(
                name='testspeaker.jpg',
                content=open(os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'), 'rb').read(),
                content_type='image/jpeg')
        )

    def test_needs_login(self):
        response = self.client.get('/speaker/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=/speaker/profile/')

    def test_needs_speaker_not_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/speaker/profile/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_needs_speaker_not_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/speaker/profile/')
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed('400.html')

    def test_template(self):
        self.client.login(username='speaker@example.org', password='s3cr3t')
        response = self.client.get('/speaker/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/speaker_profile.html')

    def test_get_context_data_no_talks(self):
        request = HttpRequest()
        request.user = self.speaker.user.user
        view = SpeakerProfileView(request=request)
        context = view.get_context_data()
        self.assertIn('attendee', context)
        self.assertIn('speaker', context)
        self.assertEqual(context['speaker'], self.speaker)
        self.assertIn('talks', context)
        self.assertEqual(len(context['talks']), 0)

    def test_get_context_data_with_talk(self):
        Talk.objects.create(speaker=self.speaker, title='Test talk', abstract='A tragedy of testing and errors')
        request = HttpRequest()
        request.user = self.speaker.user.user
        view = SpeakerProfileView(request=request)
        context = view.get_context_data()
        self.assertIn('attendee', context)
        self.assertIn('speaker', context)
        self.assertEqual(context['speaker'], self.speaker)
        self.assertIn('talks', context)
        self.assertEqual(len(context['talks']), 1)
        self.assertEqual(context['talks'][0].title, 'Test talk')


class TestCreateSpeakerView(TestCase):
    def test_dispatch_anonymous(self):
        response = self.client.get('/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/create_speaker.html')

    def test_get_form_class_anonymous(self):
        response = self.client.get('/session/new-speaker/')
        self.assertIsInstance(response.context['form'], CreateSpeakerForm)

    def test_dispatch_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/create_speaker.html')

    def test_get_form_class_user(self):
        User.objects.create_user(email='test@example.org', password='s3cr3t')
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/new-speaker/')
        self.assertIsInstance(response.context['form'], BecomeSpeakerForm)

    def test_dispatch_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/new-speaker/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('talk/create_speaker.html')

    def test_get_form_class_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/new-speaker/')
        self.assertIsInstance(response.context['form'], BecomeSpeakerForm)

    def test_dispatch_speaker(self):
        user = User.objects.create_user(email='test@example.org', password='s3cr3t')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(
            user=attendee, shirt_size=2, videopermission=True, shortbio='A short biography text'
        )
        self.client.login(username='test@example.org', password='s3cr3t')
        response = self.client.get('/session/new-speaker/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/speaker-registered/')

    def test_get_email_context(self):
        request = HttpRequest()
        view = CreateSpeakerView(request=request)
        context = view.get_email_context('test_key')
        self.assertIn('request', context)
        self.assertEqual(context['request'], request)

    def test_form_valid_anonymous(self):
        image_file = open(os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'), 'rb')
        data = {
            'email': 'speaker@example.org', 'firstname': 'Special', 'lastname': 'Tester', 'password1': 's3cr3t',
            'password2': 's3cr3t', 'shirt_size': '2', 'accept_contact': 'checked', 'videopermission': 'checked',
            'shortbio': 'A guy from somewhere having something great to talk about',
            'uploaded_image': image_file
        }
        response = self.client.post('/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(email='speaker@example.org')
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password('s3cr3t'))

    def test_form_valid_user(self):
        User.objects.create_user(email='speaker@example.org', password='s3cr3t')
        image_file = open(os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'), 'rb')
        data = {
            'firstname': 'Special', 'lastname': 'Tester', 'shirt_size': '2',
            'accept_contact': 'checked', 'videopermission': 'checked',
            'shortbio': 'A guy from somewhere having something great to talk about',
            'uploaded_image': image_file
        }
        self.client.login(email='speaker@example.org', password='s3cr3t')
        response = self.client.post('/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 0)

    def test_form_valid_attendee(self):
        user = User.objects.create_user(email='speaker@example.org', password='s3cr3t')
        Attendee.objects.create(user=user)
        image_file = open(os.path.join(os.path.dirname(__file__), 'mu_at_mil_house.jpg'), 'rb')
        data = {
            'firstname': 'Special', 'lastname': 'Tester', 'shirt_size': '2',
            'accept_contact': 'checked', 'videopermission': 'checked',
            'shortbio': 'A guy from somewhere having something great to talk about',
            'uploaded_image': image_file
        }
        self.client.login(email='speaker@example.org', password='s3cr3t')
        response = self.client.post('/session/new-speaker/', data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/session/speaker-registered/')
        self.assertEqual(len(mail.outbox), 0)
